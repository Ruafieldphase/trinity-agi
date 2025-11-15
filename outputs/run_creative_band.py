import subprocess
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
from creative_band import main

main([
    "--events", str(workspace / "outputs" / "luon_report" / "luon_rhythm_events.csv"),
    "--out", str(workspace / "outputs" / "luon_report" / "creative_band.json")
try:
    main()
except SystemExit:
    pass