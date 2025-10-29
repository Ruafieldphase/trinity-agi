import sys
from pathlib import Path

TOOLS_ROOT = Path(r"d:/nas_backup/ai_binoche_conversation_origin/lumen")
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
    r"d:/nas_backup/outputs/luon_report/luon_rhythm_events.csv",
    "--outdir",
    r"d:/nas_backup/outputs/luon_report",
]

try:
    main()
except SystemExit:
    pass
