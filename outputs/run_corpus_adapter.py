import sys
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

TOOLS_ROOT = workspace / "ai_binoche_conversation_origin" / "lumen"
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
