import pandas as pd
from pathlib import Path
import sys

# Find workspace root
sys.path.insert(0, str(Path(__file__).parent.parent))
if (Path(__file__).parent.parent / 'fdo_agi_repo').exists():
    sys.path.insert(0, str(Path(__file__).parent.parent / 'fdo_agi_repo'))
    from workspace_utils import find_workspace_root
    workspace = find_workspace_root(Path(__file__).parent)
else:
    workspace = Path(__file__).parent.parent

BASE = workspace / 'outputs'
EVENTS_PATH = BASE / 'copilot_events.csv'
KPI_PATH = BASE / 'copilot_kpi.csv'
DECISION_PATH = BASE / 'copilot_decisions.csv'
THRESHOLDS_PATH = BASE / 'copilot_decision_thresholds.txt'
THRESHOLDS_HISTORY = BASE / 'copilot_decision_thresholds_history.csv'

events = pd.read_csv(EVENTS_PATH)
events['timestamp'] = pd.to_datetime(events['timestamp'])

# KPI table: assistant turns only
kpi_rows = []
for _, row in events.iterrows():
    if row['role'] != 'assistant':
        continue
    latency_ms = max(row['delta_sec'], 0.0) * 1000.0
    kpi_rows.append({
        'timestamp': row['timestamp'].isoformat(),
        'success': True,
        'latency_ms': round(latency_ms, 3)
    })

df_kpi = pd.DataFrame(kpi_rows)
df_kpi.to_csv(KPI_PATH, index=False, encoding='utf-8')

# Decision table from rhythm scores
if not events['R_smooth'].isna().all():
    quantiles = events['R_smooth'].quantile([0.25, 0.75])
    threshold_low = float(quantiles.loc[0.25])
    threshold_high = float(quantiles.loc[0.75])
else:
    threshold_low, threshold_high = 0.4, 0.6

decision_rows = []
for _, row in events.iterrows():
    r = float(row['R_smooth']) if not pd.isna(row['R_smooth']) else 0.5
    if r < threshold_low:
        mode = 'unstable'
    elif r < threshold_high:
        mode = 'adjust'
    else:
        mode = 'stable'
    allow = 1 if mode != 'unstable' else 0
    block = 1 - allow
    preferred_next = 'assistant' if row['role'] == 'user' else 'user'
    decision_rows.append({
        'time': row['timestamp'].isoformat(),
        'mode': mode,
        'allow': allow,
        'block': block,
        'preferred_next': preferred_next,
        'r_min': round(max(r - 0.05, 0), 6),
        'r_med': round(r, 6),
        'r_max': round(min(r + 0.05, 1), 6),
        'reason': f"auto-derived from copilot_events R={r:.3f}"
    })

df_decisions = pd.DataFrame(decision_rows)
df_decisions.to_csv(DECISION_PATH, index=False, encoding='utf-8')

summary_lines = [
    f"Generated: {KPI_PATH}",
    f"Generated: {DECISION_PATH}",
    f"threshold_low={threshold_low:.6f}",
    f"threshold_high={threshold_high:.6f}"
]
THRESHOLDS_PATH.write_text(
    "\n".join(summary_lines) + "\n",
    encoding='utf-8'
)

print("\n".join(summary_lines))

# Append to threshold history for comparison over time
timestamp = pd.Timestamp.utcnow().isoformat()
history_row = f"{timestamp},{threshold_low:.6f},{threshold_high:.6f}"
header_needed = not THRESHOLDS_HISTORY.exists()
with THRESHOLDS_HISTORY.open("a", encoding="utf-8") as hist:
    if header_needed:
        hist.write("timestamp,threshold_low,threshold_high\n")
    hist.write(history_row + "\n")
