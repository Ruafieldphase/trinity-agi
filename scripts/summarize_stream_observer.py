#!/usr/bin/env python3
import argparse, json, os, sys, datetime as dt
from collections import Counter, defaultdict

DEF_OUT_MD = os.path.join('outputs', 'stream_observer_summary_latest.md')
DEF_OUT_JSON = os.path.join('outputs', 'stream_observer_summary_latest.json')
TELE_DIR = os.path.join('outputs', 'telemetry')


def iso_now():
    return dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00', 'Z')


def parse_args():
    ap = argparse.ArgumentParser(description='Summarize stream observer telemetry')
    ap.add_argument('--hours', type=int, default=24, help='Lookback window in hours (default: 24)')
    ap.add_argument('--telemetry-dir', default=TELE_DIR, help='Telemetry dir (default: outputs/telemetry)')
    ap.add_argument('--out-md', default=DEF_OUT_MD, help='Output markdown path')
    ap.add_argument('--out-json', default=DEF_OUT_JSON, help='Output JSON path')
    return ap.parse_args()


def iter_jsonl(paths):
    for p in paths:
        if not os.path.isfile(p):
            continue
        with open(p, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except Exception:
                    continue


def select_paths(tele_dir, start_utc, end_utc):
    # files are named stream_observer_YYYY-MM-DD.jsonl
    out = []
    d = start_utc.date()
    while d <= end_utc.date():
        name = f"stream_observer_{d.isoformat()}.jsonl"
        out.append(os.path.join(tele_dir, name))
        d += dt.timedelta(days=1)
    return out


def within(ts_str, start_utc, end_utc):
    try:
        ts = dt.datetime.fromisoformat(ts_str.replace('Z','').replace('+00:00',''))
    except Exception:
        return False
    return start_utc <= ts <= end_utc


def summarize(records):
    by_proc = Counter()
    by_title = Counter()
    by_vscode = Counter()
    total = 0
    first_ts = None
    last_ts = None
    
    # 탐색 패턴 분석 추가
    window_switches = 0
    prev_title = None
    durations = []
    prev_ts = None

    for r in records:
        total += 1
        by_proc[r.get('process_name')] += 1
        wt = (r.get('window_title') or '')
        if wt:
            by_title[wt] += 1
            if prev_title and wt != prev_title:
                window_switches += 1
            prev_title = wt
        
        vf = r.get('vscode_file_guess')
        if vf:
            by_vscode[vf] += 1
        
        ts = r.get('ts_utc')
        if ts:
            try:
                t = dt.datetime.fromisoformat(ts.replace('Z','').replace('+00:00',''))
                if prev_ts:
                    duration = (t - prev_ts).total_seconds()
                    if 0 < duration < 300:  # 5분 이내만
                        durations.append(duration)
                prev_ts = t
                
                if first_ts is None or t < first_ts:
                    first_ts = t
                if last_ts is None or t > last_ts:
                    last_ts = t
            except Exception:
                pass
    
    # 학습 패턴 분류
    avg_duration = sum(durations) / len(durations) if durations else 0
    unique_contexts = len(by_proc)  # 프로세스 수 = 고유 컨텍스트
    learning_pattern = 'unknown'
    
    # ADHD 스타일: 주의력 과잉 + 카오스 속 질서
    if window_switches > 15 and avg_duration > 3.0 and unique_contexts > 3:
        learning_pattern = 'adhd_hyperfocus_exploration'  # ADHD 하이퍼포커스 탐색
    elif window_switches > 15 and avg_duration > 2.0:
        learning_pattern = 'exploratory_hippocampal'  # 탐색적 해마 학습
    elif window_switches > 15 and avg_duration < 2.0:
        learning_pattern = 'distracted'  # 실제 산만 (피로/스트레스)
    elif avg_duration > 15.0:
        learning_pattern = 'deep_focus'  # 깊은 집중
    elif avg_duration > 5.0:
        learning_pattern = 'shallow_flow'  # 얕은 흐름

    return {
        'total_records': total,
        'first_ts_utc': first_ts.isoformat()+'Z' if first_ts else None,
        'last_ts_utc': last_ts.isoformat()+'Z' if last_ts else None,
        'window_switches': window_switches,
        'avg_duration_per_window': round(avg_duration, 2),
        'learning_pattern': learning_pattern,
        'top_processes': by_proc.most_common(10),
        'top_window_titles': by_title.most_common(10),
        'top_vscode_files': by_vscode.most_common(10),
    }


def write_md(path, window_hours, summary):
    lines = []
    lines.append(f"# Stream Observer Summary ({window_hours}h)\n")
    lines.append(f"Generated: {iso_now()}\n")
    lines.append("")
    lines.append(f"- Records: {summary['total_records']}")
    lines.append(f"- Window: {summary['first_ts_utc']} .. {summary['last_ts_utc']}")
    lines.append(f"- Window Switches: {summary['window_switches']}")
    lines.append(f"- Avg Duration/Window: {summary['avg_duration_per_window']}s")
    lines.append(f"- **Learning Pattern: {summary['learning_pattern']}** 🧠")
    lines.append("")
    
    # 패턴 설명 추가
    pattern_desc = {
        'adhd_hyperfocus_exploration': '🌟 ADHD 하이퍼포커스 - 주의력 과잉으로 카오스 속 패턴 발견',
        'exploratory_hippocampal': '🌊 탐색적 해마 학습 - 리듬을 따라 다양한 경험 습득',
        'distracted': '⚠️ 산만함 - 짧은 전환으로 집중 저하 (피로/스트레스 가능)',
        'deep_focus': '🎯 깊은 집중 - 장시간 몰입',
        'shallow_flow': '💫 얕은 흐름 - 적절한 집중과 전환',
        'unknown': '❓ 알 수 없음'
    }
    if summary['learning_pattern'] in pattern_desc:
        lines.append(f"> {pattern_desc[summary['learning_pattern']]}\n")
        lines.append("")

    def sec(name, items):
        lines.append(f"## {name}\n")
        if not items:
            lines.append("(none)\n")
            return
        for k, v in items:
            safe = (k or '').replace('\n',' ')[:140]
            lines.append(f"- {v:>5}  |  {safe}")
        lines.append("")

    sec('Top Processes', summary['top_processes'])
    sec('Top Window Titles', summary['top_window_titles'])
    sec('Top VS Code Files', summary['top_vscode_files'])

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def main():
    args = parse_args()
    end_utc = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    start_utc = end_utc - dt.timedelta(hours=args.hours)
    paths = select_paths(args.telemetry_dir, start_utc, end_utc)

    recs = [r for r in iter_jsonl(paths) if within(r.get('ts_utc',''), start_utc, end_utc)]
    summary = summarize(recs)

    os.makedirs(os.path.dirname(args.out_json), exist_ok=True)
    with open(args.out_json, 'w', encoding='utf-8') as f:
        json.dump({
            'generated_utc': iso_now(),
            'window_hours': args.hours,
            'summary': summary,
        }, f, ensure_ascii=False, indent=2)

    write_md(args.out_md, args.hours, summary)
    print(json.dumps({'ok': True, 'records': summary['total_records'], 'out_md': args.out_md, 'out_json': args.out_json}))


if __name__ == '__main__':
    sys.exit(main())
