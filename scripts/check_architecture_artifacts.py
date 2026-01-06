import json
import os
from pathlib import Path
from datetime import datetime
from workspace_root import get_workspace_root


def load_summary(summary_path: Path):
    with summary_path.open('r', encoding='utf-8') as f:
        return json.load(f)


def check_files(root: Path, files):
    results = []
    for f in files:
        p = root / f
        exists = p.exists()
        results.append({
            'file': f,
            'path': str(p),
            'exists': exists
        })
    return results


def write_reports(out_dir: Path, report_md: str, report_json: dict):
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / 'architecture_artifacts_check.md').write_text(report_md, encoding='utf-8')
    (out_dir / 'architecture_artifacts_check.json').write_text(
        json.dumps(report_json, ensure_ascii=False, indent=2), encoding='utf-8')


def main():
    workspace = get_workspace_root()
    summary_path = workspace / 'outputs' / 'architecture_probe_summary.json'
    out_dir = workspace / 'outputs'

    if not summary_path.exists():
        msg = f"WARN: summary not found: {summary_path}"
        print(msg)
        write_reports(out_dir, f"# Architecture Artifacts Check\n\n{msg}\n", {
            'status': 'warn',
            'reason': 'summary_missing',
            'summary_path': str(summary_path)
        })
        return 0

    summary = load_summary(summary_path)
    root_dir = Path(summary.get('path', ''))
    code_artifacts = summary.get('codeArtifacts', [])

    rows = []
    total = 0
    found = 0
    per_file = []
    for item in code_artifacts:
        file = item.get('file')
        if not file:
            continue
        total += 1
        exists = (root_dir / file).exists()
        if exists:
            found += 1
        per_file.append({
            'file': file,
            'root': str(root_dir),
            'full_path': str(root_dir / file),
            'exists': exists,
            'highlights': item.get('highlights', [])
        })
        rows.append(f"| `{file}` | `{root_dir}` | {'✅' if exists else '❌'} |")

    pct = (found / total * 100.0) if total else 0.0
    ts = datetime.now().isoformat(timespec='seconds')
    md = [
        f"# Architecture Artifacts Check",
        f"- Time: {ts}",
        f"- Summary path: `{summary_path}`",
        f"- Root: `{root_dir}`",
        f"- Found: {found}/{total} ({pct:.1f}%)",
        "",
        "| File | Root | Exists |",
        "|---|---|---|",
    ]
    md.extend(rows or ["| (none) | - | - |"])
    report_md = "\n".join(md) + "\n"

    report_json = {
        'time': ts,
        'summary_path': str(summary_path),
        'root': str(root_dir),
        'found': found,
        'total': total,
        'percent': pct,
        'files': per_file,
        'status': 'ok' if total == 0 or found > 0 else 'warn'
    }

    write_reports(out_dir, report_md, report_json)
    print(f"Artifacts found {found}/{total} ({pct:.1f}%). Report written to outputs/architecture_artifacts_check.*")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
