#!/usr/bin/env python3
"""
Lubit Dataset Analysis
Generates statistics and insights from parsed lubit data.
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter

def analyze_lubit(jsonl_path):
    """Analyze parsed lubit dataset."""
    
    # Load data
    records = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            records.append(json.loads(line.strip()))
    
    # Basic stats
    total_records = len(records)
    unique_sessions = len(set(r['session_id'] for r in records if r['session_id']))
    
    # Role distribution
    roles = Counter(r['role'] for r in records)
    
    # Session analysis
    session_messages = defaultdict(list)
    for r in records:
        if r['session_id']:
            session_messages[r['session_id']].append(r)
    
    # Top sessions by message count
    top_sessions = sorted(
        [(sid, len(msgs)) for sid, msgs in session_messages.items()],
        key=lambda x: -x[1]
    )[:10]
    
    # Source file distribution
    source_files = Counter(r['source_file'] for r in records)
    
    # Time range
    timestamps = [r['timestamp'] for r in records if r.get('timestamp')]
    if timestamps:
        timestamps.sort()
        time_start = timestamps[0]
        time_end = timestamps[-1]
        
        try:
            dt_start = datetime.fromisoformat(time_start.replace('Z', '+00:00'))
            dt_end = datetime.fromisoformat(time_end.replace('Z', '+00:00'))
            time_span_days = (dt_end - dt_start).days
        except:
            time_span_days = None
    else:
        time_start = None
        time_end = None
        time_span_days = None
    
    # Content analysis
    avg_content_len = sum(len(r['content']) for r in records) / len(records) if records else 0
    
    # Compile results
    analysis = {
        'timestamp': datetime.now().isoformat(),
        'total_records': total_records,
        'unique_sessions': unique_sessions,
        'avg_messages_per_session': total_records / unique_sessions if unique_sessions else 0,
        'role_distribution': dict(roles),
        'top_sessions': [{'session_id': sid[:8] + '...', 'message_count': count} 
                        for sid, count in top_sessions],
        'time_range': {
            'start': time_start,
            'end': time_end,
            'span_days': time_span_days
        },
        'source_files': len(source_files),
        'avg_content_length': round(avg_content_len, 2)
    }
    
    return analysis

def format_report(analysis):
    """Format analysis as Markdown."""
    
    md = "# Lubit Dataset Analysis\n\n"
    md += f"**Generated**: {analysis['timestamp']}\n\n"
    
    md += "## Overview\n\n"
    md += f"- **Total Records**: {analysis['total_records']:,}\n"
    md += f"- **Unique Sessions**: {analysis['unique_sessions']:,}\n"
    md += f"- **Avg Messages/Session**: {analysis['avg_messages_per_session']:.2f}\n"
    md += f"- **Source Files**: {analysis['source_files']:,}\n"
    md += f"- **Avg Content Length**: {analysis['avg_content_length']:.0f} chars\n\n"
    
    md += "## Role Distribution\n\n"
    total = sum(analysis['role_distribution'].values())
    for role, count in sorted(analysis['role_distribution'].items(), key=lambda x: -x[1]):
        pct = 100 * count / total
        md += f"- **{role}**: {count:,} ({pct:.1f}%)\n"
    md += "\n"
    
    md += "## Time Range\n\n"
    if analysis['time_range']['start']:
        md += f"- **Start**: {analysis['time_range']['start']}\n"
        md += f"- **End**: {analysis['time_range']['end']}\n"
        if analysis['time_range']['span_days']:
            md += f"- **Span**: {analysis['time_range']['span_days']} days\n"
    else:
        md += "*(No timestamp data)*\n"
    md += "\n"
    
    md += "## Top 10 Sessions\n\n"
    for i, session in enumerate(analysis['top_sessions'], 1):
        md += f"{i}. **{session['session_id']}** - {session['message_count']} messages\n"
    md += "\n"
    
    return md

def main():
    if len(sys.argv) < 2:
        print("Usage: python lubit_analyze.py <input_jsonl> [output_json] [output_md]")
        sys.exit(1)
    
    input_jsonl = Path(sys.argv[1])
    output_json = Path(sys.argv[2]) if len(sys.argv) > 2 else Path('outputs/lubit_analysis.json')
    output_md = Path(sys.argv[3]) if len(sys.argv) > 3 else Path('outputs/lubit_analysis.md')
    
    if not input_jsonl.exists():
        print(f"Error: Input file not found: {input_jsonl}")
        sys.exit(1)
    
    # Run analysis
    analysis = analyze_lubit(input_jsonl)
    
    # Write JSON
    output_json.parent.mkdir(parents=True, exist_ok=True)
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    
    print(f"Wrote analysis to {output_json}")
    
    # Write Markdown
    report = format_report(analysis)
    with open(output_md, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"Wrote report to {output_md}")
    
    # Print summary
    print(f"\nSummary:")
    print(f"  Total records: {analysis['total_records']:,}")
    print(f"  Unique sessions: {analysis['unique_sessions']:,}")
    print(f"  Avg messages/session: {analysis['avg_messages_per_session']:.2f}")

if __name__ == '__main__':
    main()
