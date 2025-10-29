import sys
from pathlib import Path

TOOLS_ROOT = Path(r"d:/nas_backup/ai_binoche_conversation_origin/lumen")
INFO_DIR = next(
    (p for p in TOOLS_ROOT.glob("chatgpt-*") if (p / "tools/luon/elo_corpus_adapter.py").exists()),
    TOOLS_ROOT / "chatgpt-정보이론철학적분석",
)

sys.path.append(str(INFO_DIR / "tools/luon"))

from elo_corpus_adapter import main as adapter_main  # noqa: E402

mapping = INFO_DIR / "tools/luon/elo_corpus_mapping.sample.yaml"

if not mapping.exists():
    raise FileNotFoundError(f"Mapping file not found: {mapping}")

sys.argv = [
    "elo_corpus_adapter",
    "--map",
    str(mapping),
]

try:
    adapter_main()
except SystemExit:
    pass
