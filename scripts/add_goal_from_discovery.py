#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime

p = Path(__file__).parent.parent / 'fdo_agi_repo' / 'memory' / 'goal_tracker.json'
if not p.exists():
    raise FileNotFoundError(f"Goal tracker not found: {p}")
with p.open('r', encoding='utf-8') as f:
    data = json.load(f)

new_goal = {
    'title': '🧠 자기 인식 확장',
    'status': 'proposed',
    'added_at': datetime.utcnow().replace(microsecond=0).isoformat() + 'Z',
    'source': 'self_discovery',
    'priority': 10.0,
    'type': 'reflection',
    'executable': {
        'type': 'script',
        'script': '${workspaceFolder}/scripts/generate_groove_profile.py',
        'args': ['--hours', '24'],
        'timeout': 600,
    },
    'metadata': {'origin': 'self_discovery_experiment'},
}

data.setdefault('goals', []).append(new_goal)
now = datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'
# update metadata keys for tracker
if isinstance(data, dict):
    data['updatedAt'] = now
    data['last_updated'] = now

with p.open('w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print('Appended goal to tracker', p)
