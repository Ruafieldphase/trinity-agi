import json, math, statistics
from pathlib import Path
from datetime import datetime
import pandas as pd

from pathlib import Path
import json
import sys

# Find workspace root
sys.path.insert(0, str(Path(__file__).parent.parent))
if (Path(__file__).parent.parent / 'fdo_agi_repo').exists():
    sys.path.insert(0, str(Path(__file__).parent.parent / 'fdo_agi_repo'))
    from workspace_utils import find_workspace_root
    workspace = find_workspace_root(Path(__file__).parent)
else:
    workspace = Path(__file__).parent.parent

share = json.loads((workspace / 'copilot_share.json').read_text(encoding='utf-8'))
msgs = sorted(share['messages'], key=lambda m: m['createdAt'])
rows = []
prev_ts = None
for m in msgs:
    texts = [c['text'] for c in m.get('content', []) if c.get('type') == 'text']
    if not texts:
        continue
    text = '\n\n'.join(texts)
    ts = datetime.fromisoformat(m['createdAt'].replace('Z', '+00:00'))
    delta = 0.0 if prev_ts is None else (ts - prev_ts).total_seconds()
    prev_ts = ts
    tokens = max(1, int(len(text) / 3.5))
    persona = m['author']
    role = 'assistant' if persona == 'ai' else 'user'
    rows.append({
        'timestamp': ts.astimezone().isoformat(),
        'persona': persona,
        'role': role,
        'tokens': tokens,
        'delta_sec': delta,
        'text': text,
    })

if rows:
    token_values = [r['tokens'] for r in rows]
    mean = statistics.fmean(token_values)
    stdev = statistics.pstdev(token_values)
    alpha = 0.3
    prev_r = None
    def logistic(x):
        return 1 / (1 + math.exp(-x))
    for r in rows:
        z = 0.0 if stdev == 0 else (r['tokens'] - mean) / stdev
        R = logistic(z)
        R_smooth = R if prev_r is None else (1 - alpha) * prev_r + alpha * R
        r['R'] = round(R, 6)
        r['R_smooth'] = round(R_smooth, 6)
        prev_r = R_smooth

out_path = workspace / 'outputs' / 'copilot_events.csv'
df = pd.DataFrame(rows)
if not df.empty:
    df = df[['timestamp','persona','role','tokens','delta_sec','R','R_smooth','text']]
df.to_csv(out_path, index=False, encoding='utf-8')
print(out_path)