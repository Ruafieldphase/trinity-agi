import re
from pathlib import Path

from pathlib import Path
import re
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Find workspace root dynamically
if (Path(__file__).parent.parent / 'fdo_agi_repo').exists():
    sys.path.insert(0, str(Path(__file__).parent.parent / 'fdo_agi_repo'))
    from workspace_utils import find_workspace_root
    workspace = find_workspace_root(Path(__file__).parent)
else:
    workspace = Path(__file__).parent.parent

SCAN_DIRS = [
    workspace / "outputs",
    workspace / "ai_binoche_conversation_origin" / "perple_comet_cople_eru",
    workspace / "ai_binoche_conversation_origin" / "sena",
    workspace / "ai_binoche_conversation_origin" / "rio",
    workspace / "ai_binoche_conversation_origin" / "ari",
    workspace / "LLM_Unified",
]

PATTERNS = {
    "Google API Key (AIza...)": re.compile(r"AIza[0-9A-Za-z_-]{35}"),
    "OpenAI Key (sk-)": re.compile(r"sk-[A-Za-z0-9]{10,}"),
    "URL (http/https)": re.compile(r"https?://[^\s)\]\"']+"),
    "Email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
}

EXCLUDE_EXT = {".png", ".svg", ".zip", ".pdf", ".exe", ".dll", ".ttf", ".jpg", ".mp4", ".pyc"}
MAX_BYTES = 1_500_000
REPORT = workspace / "outputs" / "sensitive_scan_report.md"

results = {name: [] for name in PATTERNS}

for base in TARGET_DIRS:
    if not base.exists():
        continue
    for path in base.rglob('*'):
        if not path.is_file():
            continue
        if path.suffix.lower() in EXCLUDE_EXT:
            continue
        try:
            if path.stat().st_size > MAX_BYTES:
                continue
            text = path.read_text(encoding='utf-8')
        except Exception:
            try:
                text = path.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                continue
        for label, regex in PATTERNS.items():
            matches = regex.findall(text)
            if matches:
                snippets = []
                for m in matches:
                    snippet = m
                    if len(snippet) > 120:
                        snippet = snippet[:117] + '...'
                    snippets.append(snippet)
                results[label].append((path.as_posix(), sorted(set(snippets))))

with REPORT.open('w', encoding='utf-8') as f:
    f.write('# Sensitive Information Scan Report\n\n')
    f.write('Directories scanned:\n')
    for d in TARGET_DIRS:
        f.write(f'- {d.as_posix()}\n')
    f.write('\n')
    f.write(f'Size limit per file: {MAX_BYTES} bytes\n\n')
    for label, entries in results.items():
        f.write(f'## {label}\n')
        if not entries:
            f.write('No matches found.\n\n')
            continue
        for path_str, snippets in entries:
            f.write(f'- **{path_str}**\n')
            for snip in snippets:
                f.write(f'  - `{snip}`\n')
            f.write('\n')
