from pathlib import Path
import re

from pathlib import Path
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

source = workspace / 'outputs' / 'ChatGPT_대화의언어적감응_full.md'
output = workspace / 'outputs' / 'ChatGPT_대화의언어적감응_summary.md'
text = source.read_text(encoding='utf-8')

sections = re.split(r'\n## Prompt:', text)
summary_parts = [sections[0].strip()]
for block in sections[1:8]:
    lines = block.strip().splitlines()
    if not lines:
        continue
    prompt_line = lines[0]
    rest = '\n'.join(lines[1:])
    response_match = re.split(r'## Response:', rest, maxsplit=1)
    if len(response_match) == 2:
        prompt_text = prompt_line.strip()
        response_text = response_match[1].strip()
        summary_parts.append('## Prompt:\n' + prompt_text)
        trimmed_resp = '\n'.join(response_text.splitlines()[:20])
        summary_parts.append('### Response (trimmed):\n' + trimmed_resp)

summary = '\n\n'.join(summary_parts)
output.write_text(summary, encoding='utf-8')
