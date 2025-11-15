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

TOOLS_ROOT = workspace / "ai_binoche_conversation_origin" / "lumen"
INFO_DIR = next(
    (p for p in TOOLS_ROOT.glob("chatgpt-*") if (p / "luon_feedback_dashboard.py").exists()),
    TOOLS_ROOT / "chatgpt-정보이론철학적분석",
)

sys.path.append(str(INFO_DIR))

try:
    from matplotlib_hangul import ensure_korean_font

    ensure_korean_font()
except Exception:
    pass

from luon_feedback_dashboard import main  # noqa: E402

sys.argv = [
    "luon_feedback_dashboard",
    "--events",
    str(workspace / "outputs" / "luon_report" / "luon_rhythm_events.csv"),
    "--outdir",
    str(workspace / "outputs" / "luon_report"),
]

try:
    main()
except SystemExit:
    pass
