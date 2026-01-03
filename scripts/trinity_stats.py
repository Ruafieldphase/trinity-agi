#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trinity Statistics Generator (Core-Elro-Core)
삼위일체 통합 통계 생성

정(正) - Core: 감응의 대화
반(反) - Elro: 감응의 구조 (정보이론 변환)
합(合) - Core: 설계 통합
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from collections import Counter
import re
import argparse
from workspace_root import get_workspace_root

def parse_datetime(dt_str):
    """ISO 8601 datetime 파싱"""
    if not dt_str or dt_str == "null":
        return None
    try:
        # Remove timezone suffix for parsing
        dt_str = dt_str.replace('+00:00', 'Z')
        if dt_str.endswith('Z'):
            dt_str = dt_str[:-1]
        return datetime.fromisoformat(dt_str)
    except:
        return None

def load_jsonl(file_path):
    """JSONL 파일 로드"""
    records = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except FileNotFoundError:
        print(f"Warning: {file_path} not found", file=sys.stderr)
    return records

def load_origin_core(extra_dir: Path):
    """Optional: Load additional Core conversation sources from original folder.
    Supports JSON array files like shared_conversations.json or conversations.json.
    Returns list of minimal records with conversation_id/title/create_time.
    """
    records = []
    if not extra_dir or not extra_dir.exists():
        return records
    candidates = [
        extra_dir / "shared_conversations.json",
        extra_dir / "conversations.json",
    ]
    for p in candidates:
        try:
            if p.exists():
                with open(p, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for i, item in enumerate(data):
                            title = (
                                item.get('title')
                                or item.get('conversation_title')
                                or item.get('name')
                                or f"core_origin_{p.stem}_{i}"
                            )
                            cid = (
                                item.get('conversation_id')
                                or item.get('id')
                                or f"core_origin_{p.stem}_{i}"
                            )
                            ct = item.get('create_time') or item.get('created_at') or None
                            records.append(
                                {
                                    'conversation_id': cid,
                                    'conversation_title': title,
                                    'create_time': ct,
                                }
                            )
        except Exception:
            # tolerate malformed/unknown formats
            continue
    return records

def extract_keywords(text, top_n=20):
    """한글 키워드 추출 (간단 버전)"""
    if not text:
        return []
    # 한글 2글자 이상 단어 추출
    words = re.findall(r'[가-힣]{2,}', text)
    # 불용어 필터 (간단 버전)
    stopwords = {'있는', '있습니다', '합니다', '입니다', '것입니다', '됩니다', '같은', '대한', '위한', '통해', '이것', '그것', '저것', '어떤', '어떻게', '무엇', '누구', '언제', '어디', '왜'}
    words = [w for w in words if w not in stopwords and len(w) >= 2]
    return Counter(words).most_common(top_n)

def analyze_phase(records, phase_name):
    """단일 phase 분석"""
    if not records:
        return {
            "phase": phase_name,
            "total_messages": 0,
            "unique_conversations": 0,
            "avg_turns": 0,
            "max_turns": 0,
            "time_span_days": 0,
            "keywords": []
        }
    
    # 대화별 그룹핑
    conv_groups = {}
    for r in records:
        conv_id = r.get('conversation_id', 'unknown')
        if conv_id not in conv_groups:
            conv_groups[conv_id] = []
        conv_groups[conv_id].append(r)
    
    # 통계 계산
    total_messages = len(records)
    unique_conversations = len(conv_groups)
    turn_counts = [len(msgs) for msgs in conv_groups.values()]
    avg_turns = sum(turn_counts) / len(turn_counts) if turn_counts else 0
    max_turns = max(turn_counts) if turn_counts else 0
    
    # 시간 범위
    timestamps = []
    for r in records:
        ct = r.get('create_time')
        dt = parse_datetime(ct)
        if dt:
            timestamps.append(dt)
    
    time_span_days = 0
    if len(timestamps) >= 2:
        timestamps.sort()
        time_span_days = (timestamps[-1] - timestamps[0]).days
    
    # 키워드 추출 (제목 기반)
    all_titles = " ".join([r.get('conversation_title', '') for r in records if r.get('conversation_title')])
    keywords = extract_keywords(all_titles, top_n=15)
    
    return {
        "phase": phase_name,
        "total_messages": total_messages,
        "unique_conversations": unique_conversations,
        "avg_turns": round(avg_turns, 1),
        "max_turns": max_turns,
        "time_span_days": time_span_days,
        "keywords": [{"keyword": k, "count": c} for k, c in keywords]
    }

def main():
    ap = argparse.ArgumentParser(description="Generate Trinity (Core/Elro/Core) statistics")
    ap.add_argument(
        "--extra-Core-dir",
        dest="extra_core_dir",
        default=str(get_workspace_root() / "ai_binoche_conversation_origin" / "Core"),
        help="Optional folder to ingest additional Core sources (JSON arrays)",
    )
    args = ap.parse_args()

    workspace = get_workspace_root()
    output_dir = workspace / "outputs" / "trinity"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    print("Loading Trinity datasets...", file=sys.stderr)
    Core_records = load_jsonl(workspace / "outputs" / "Core" / "core_conversations_flat.jsonl")
    elro_records = load_jsonl(workspace / "outputs" / "elro" / "elro_conversations_flat.jsonl")
    core_records = load_jsonl(workspace / "outputs" / "Core" / "core_conversations_flat.jsonl")

    # Optionally augment Core with original sources (non-destructive merge)
    extra_dir = Path(args.extra_core_dir) if args.extra_core_dir else None
    extra_core = load_origin_core(extra_dir) if extra_dir else []
    if extra_core:
        core_records.extend(extra_core)
    
    print(f"  Core (正): {len(Core_records)} messages", file=sys.stderr)
    print(f"  Elro (反): {len(elro_records)} messages", file=sys.stderr)
    print(f"  Core (合): {len(core_records)} messages", file=sys.stderr)
    
    # Analyze each phase
    Core_stats = analyze_phase(Core_records, "Core (正 - Thesis)")
    elro_stats = analyze_phase(elro_records, "Elro (反 - Antithesis)")
    core_stats = analyze_phase(core_records, "Core (合 - Synthesis)")
    
    # Combined stats
    trinity_stats = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "analyst": "Binoche_Observer 🌿",
            "philosophy": "Core-Elro-Core Dialectical Trinity"
        },
        "summary": {
            "total_messages": Core_stats["total_messages"] + elro_stats["total_messages"] + core_stats["total_messages"],
            "total_conversations": Core_stats["unique_conversations"] + elro_stats["unique_conversations"] + core_stats["unique_conversations"],
            "time_span_years": round(max(Core_stats["time_span_days"], elro_stats["time_span_days"], core_stats["time_span_days"]) / 365.25, 1)
        },
        "phases": {
            "Core": Core_stats,
            "elro": elro_stats,
            "Core": core_stats
        }
    }
    
    # Save JSON
    output_json = output_dir / "trinity_statistics.json"
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(trinity_stats, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Trinity statistics saved: {output_json}", file=sys.stderr)
    print(json.dumps(trinity_stats, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
