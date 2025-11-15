import sys
from pathlib import Path

# Find workspace root
sys.path.insert(0, str(Path(__file__).parent.parent))
if (Path(__file__).parent.parent / 'fdo_agi_repo').exists():
    sys.path.insert(0, str(Path(__file__).parent.parent / 'fdo_agi_repo'))
    from workspace_utils import find_workspace_root
    workspace = find_workspace_root(Path(__file__).parent)
else:
    workspace = Path(__file__).parent.parent

lumen_path = workspace / "ai_binoche_conversation_origin" / "lumen" / "chatgpt-정보이론철학적분석"
sys.path.append(str(lumen_path))
from luon_rhythm_queue_v2 import main

sys.argv = [
    "luon_rhythm_queue_v2",
    "--events", str(workspace / "outputs" / "luon_report" / "luon_rhythm_events.csv"),
    "--config", str(workspace / "outputs" / "luon_report" / "luon_config_tuned_kpi.yaml"),
    "--outdir", str(workspace / "outputs" / "luon_report")
]
try:
    main()
except SystemExit:
    pass