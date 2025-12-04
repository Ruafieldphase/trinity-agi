#!/usr/bin/env python3
"""Analyze Rua Dataset and generate statistics dashboard."""
import json
import sys
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime
from typing import Dict, List, Any

def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    """Load JSONL file."""
    records = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records

def analyze_dataset(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze dataset and return statistics."""
    total_records = len(records)
    
    # By role
    role_counts = Counter(r.get('author_role') for r in records)
    
    # By conversation
    conv_counts = Counter(r.get('conversation_id') for r in records)
    unique_conversations = len(conv_counts)
    avg_messages_per_conv = total_records / unique_conversations if unique_conversations > 0 else 0
    
    # Conversation titles
    conv_titles = {}
    for r in records:
        conv_id = r.get('conversation_id')
        title = r.get('conversation_title')
        if conv_id and title:
            conv_titles[conv_id] = title
    
    # Time range
    timestamps = []
    for r in records:
        ct = r.get('create_time')
        if ct and isinstance(ct, str):
            try:
                dt = datetime.fromisoformat(ct.replace('Z', '+00:00'))
                timestamps.append(dt)
            except:
                pass
    
    time_range = None
    if timestamps:
        timestamps.sort()
        time_range = {
            'earliest': timestamps[0].isoformat(),
            'latest': timestamps[-1].isoformat(),
            'span_days': (timestamps[-1] - timestamps[0]).days
        }
    
    # Top conversations by message count
    top_convs = conv_counts.most_common(10)
    top_convs_with_titles = [
        {
            'id': conv_id,
            'title': conv_titles.get(conv_id, '(no title)'),
            'count': count
        }
        for conv_id, count in top_convs
    ]
    
    # Content length statistics
    content_lengths = [len(r.get('content', '')) for r in records if r.get('content')]
    avg_content_len = sum(content_lengths) / len(content_lengths) if content_lengths else 0
    
    return {
        'total_records': total_records,
        'unique_conversations': unique_conversations,
        'avg_messages_per_conv': round(avg_messages_per_conv, 2),
        'role_distribution': dict(role_counts),
        'time_range': time_range,
        'top_conversations': top_convs_with_titles,
        'avg_content_length': round(avg_content_len, 2)
    }

def generate_markdown_report(stats: Dict[str, Any], output_path: Path):
    """Generate Markdown report."""
    md = f"""# Rua Dataset Analysis Report

Generated: {datetime.now().isoformat()}

## Summary Statistics

- **Total Records**: {stats['total_records']:,}
- **Unique Conversations**: {stats['unique_conversations']:,}
- **Average Messages per Conversation**: {stats['avg_messages_per_conv']:.2f}
- **Average Content Length**: {stats['avg_content_length']:.0f} characters

## Role Distribution

"""
    for role, count in sorted(stats['role_distribution'].items(), key=lambda x: -x[1]):
        pct = (count / stats['total_records'] * 100) if stats['total_records'] > 0 else 0
        md += f"- **{role}**: {count:,} ({pct:.1f}%)\n"
    
    if stats['time_range']:
        tr = stats['time_range']
        md += f"""
## Time Range

- **Earliest Message**: {tr['earliest']}
- **Latest Message**: {tr['latest']}
- **Span**: {tr['span_days']} days
"""
    
    md += f"""
## Top 10 Conversations by Message Count

"""
    for i, conv in enumerate(stats['top_conversations'], 1):
        md += f"{i}. **{conv['title']}** ({conv['count']:,} messages)\n"
        md += f"   - ID: `{conv['id']}`\n\n"
    
    md += f"""
---
*End of Report*
"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(md)
    print(f"✅ Markdown report written to {output_path}")

def main():
    # Paths
    input_jsonl = Path(r"C:\workspace\agi\outputs\rua_dataset_parsed.jsonl")
    output_json = Path(r"C:\workspace\agi\outputs\rua_analysis.json")
    output_md = Path(r"C:\workspace\agi\outputs\rua_analysis.md")
    
    if not input_jsonl.exists():
        print(f"ERROR: {input_jsonl} not found", file=sys.stderr)
        return 1
    
    print(f"📂 Loading: {input_jsonl}")
    records = load_jsonl(input_jsonl)
    print(f"📊 Loaded {len(records):,} records")
    
    print(f"🔍 Analyzing...")
    stats = analyze_dataset(records)
    
    # Write JSON
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(f"✅ JSON stats written to {output_json}")
    
    # Write Markdown
    generate_markdown_report(stats, output_md)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
