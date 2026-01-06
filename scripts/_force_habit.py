import sys
from pathlib import Path

# Add workspace root to path
sys.path.append(str(Path.cwd()))

from scripts.striatum_pattern_engine import StriatumPatternEngine

engine = StriatumPatternEngine(Path.cwd())

context = {
    'what': 'play_music',
    'who': 'user',
    'where': 'workspace'
}

# Define the workflow as a sequence of nodes (steps)
action = {
    'workflow': 'powershell_playback',
    'type': 'workflow',
    'steps': [
        "powershell -ExecutionPolicy Bypass -File c:\\workspace\\agi\\scripts\\play_rest_session_v2.ps1"
    ]
}

engine.force_habit(context, action)
print("✅ Workflow habit forced successfully.")
