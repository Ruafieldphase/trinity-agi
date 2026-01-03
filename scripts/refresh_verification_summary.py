#!/usr/bin/env python3
"""
Reads outputs/meta_supervision_latest.json and renders a concise
verification summary markdown to outputs/verification_summary_latest.md.
Also prints a one-liner for quick inclusion.
"""
import json
from pathlib import Path
from datetime import datetime
from workspace_root import get_workspace_root

WORKSPACE = get_workspace_root()
OUT = WORKSPACE / 'outputs'
SRC = OUT / 'meta_supervision_latest.json'
DST = OUT / 'verification_summary_latest.md'

def main():
    if not SRC.exists():
        print('no_meta_supervision_json')
        return 1
    data = json.loads(SRC.read_text(encoding='utf-8'))
    ver = data.get('verification', {})
    level = ver.get('level', 'unknown')
    results = ver.get('results', [])
    passed = sum(1 for r in results if r.get('success'))
    total = len(results)
    failed = [r for r in results if not r.get('success')]

    lines = []
    lines.append('# 🔬 Self-Verification Summary')
    lines.append('')
    lines.append(f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    lines.append('')
    lines.append('## 📈 Status')
    lines.append('')
    lines.append(f'- Level: {level.upper()}')
    lines.append(f'- Passed: {passed}/{total}')
    lines.append('')
    if failed:
        lines.append('## ❌ Failures')
        lines.append('')
        for r in failed:
            name = r.get('name','unknown')
            exit_code = r.get('exit_code')
            lines.append(f'- {name} (exit {exit_code})')
        lines.append('')
    else:
        lines.append('## ✅ All checks passed')
        lines.append('')

    DST.write_text('\n'.join(lines), encoding='utf-8')
    print(f'one_liner|level={level}|passed={passed}|total={total}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())

