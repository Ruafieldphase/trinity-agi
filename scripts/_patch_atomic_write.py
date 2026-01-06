import re
from pathlib import Path
from workspace_root import get_workspace_root
WORKSPACE_ROOT = get_workspace_root()
p = WORKSPACE_ROOT / "scripts" / "auto_orchestration.py"
src = p.read_text(encoding='utf-8')

# ensure atomic_write import
imp_line = "\nfrom utils.atomic_write import atomic_write\n"
if 'from utils.atomic_write import atomic_write' not in src:
    m = re.search(r"^from utils\.validator import core_chat_schema.*$", src, re.M)
    if m:
        idx = m.end()
        src = src[:idx] + imp_line + src[idx:]
    else:
        # fallback: after other imports
        m2 = re.search(r"^(?:import .*$\n)+", src, re.M)
        if m2:
            idx = m2.end()
            src = src[:idx] + imp_line + src[idx:]
        else:
            src = imp_line + src

# replace open-write block for report_file with atomic_write
pattern = r"(^\s*)with open\(report_file, 'w', encoding='utf-8'\) as f:\n\s*f\.write\(((?:f)?\"\"\"[\s\S]*?\"\"\")\)"

def repl(m):
    indent = m.group(1)
    content = m.group(2)
    return f"{indent}report_content = {content}\n{indent}atomic_write(str(report_file), report_content)"

src_new = re.sub(pattern, repl, src, flags=re.M)

if src_new != src:
    p.write_text(src_new, encoding='utf-8')
    print('Patched atomic write block')
else:
    print('No change needed (atomic write already applied?)')
