#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VS Code Tasks 분석 스크립트 (간단 버전)
tasks.json을 파싱하여 통계 및 개선 제안 제공
"""

import json
import re
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Any

def load_tasks_json(path: str = ".vscode/tasks.json") -> Dict[str, Any]:
    """tasks.json 로드"""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_tasks(data: Dict[str, Any]) -> Dict[str, Any]:
    """작업 분석"""
    tasks = data.get("tasks", [])
    
    # 기본 통계
    total = len(tasks)
    
    # 카테고리 추출 (라벨 첫 단어)
    categories = Counter()
    priorities = Counter()
    groups = Counter()
    backgrounds = 0
    
    for task in tasks:
        label = task.get("label", "")
        
        # 카테고리 (첫 단어 또는 이모지 뒤 단어)
        match = re.match(r'^(?:[^\w\s]*\s*)?(\w+)', label)
        if match:
            category = match.group(1)
            categories[category] += 1
        
        # 우선순위 추론
        if any(kw in label.lower() for kw in ['emergency', 'critical', 'recover']):
            priorities['P0_CRITICAL'] += 1
        elif any(kw in label.lower() for kw in ['daily', 'register', 'start']):
            priorities['P1_HIGH'] += 1
        elif any(kw in label.lower() for kw in ['generate', 'report', 'status']):
            priorities['P2_NORMAL'] += 1
        elif any(kw in label.lower() for kw in ['test', 'debug', 'verify']):
            priorities['P3_LOW'] += 1
        else:
            priorities['P4_OPTIONAL'] += 1
        
        # 그룹
        group = task.get("group", "none")
        groups[group] += 1
        
        # 백그라운드
        if task.get("isBackground"):
            backgrounds += 1
    
    return {
        "total_tasks": total,
        "categories": dict(categories.most_common(15)),
        "priorities": dict(priorities),
        "groups": dict(groups),
        "background_tasks": backgrounds
    }

def find_similar_tasks(data: Dict[str, Any], threshold: float = 0.7) -> List[Dict[str, Any]]:
    """유사한 작업 찾기 (중복 가능성)"""
    tasks = data.get("tasks", [])
    similar_groups = []
    
    # 간단한 유사도 체크 (라벨 기반)
    checked = set()
    
    for i, task1 in enumerate(tasks):
        if i in checked:
            continue
        
        label1 = task1.get("label", "").lower()
        words1 = set(re.findall(r'\w+', label1))
        
        similar = [task1]
        
        for j, task2 in enumerate(tasks[i+1:], i+1):
            if j in checked:
                continue
            
            label2 = task2.get("label", "").lower()
            words2 = set(re.findall(r'\w+', label2))
            
            # Jaccard 유사도
            intersection = words1 & words2
            union = words1 | words2
            
            if len(union) > 0:
                similarity = len(intersection) / len(union)
                
                if similarity >= threshold:
                    similar.append(task2)
                    checked.add(j)
        
        if len(similar) > 1:
            similar_groups.append(similar)
            checked.add(i)
    
    return similar_groups

def print_report(stats: Dict[str, Any], similar: List[Dict[str, Any]]):
    """보고서 출력"""
    print("=" * 80)
    print("VS CODE TASKS.JSON 분석 보고서")
    print("=" * 80)
    
    print(f"\n📊 전체 통계")
    print(f"  총 작업 개수: {stats['total_tasks']}개")
    print(f"  백그라운드 작업: {stats['background_tasks']}개")
    
    print(f"\n📁 카테고리별 분포 (Top 15)")
    for cat, count in stats['categories'].items():
        pct = (count / stats['total_tasks']) * 100
        print(f"  {cat:20s}: {count:3d}개 ({pct:5.1f}%)")
    
    print(f"\n🎯 우선순위 분포")
    priority_order = ['P0_CRITICAL', 'P1_HIGH', 'P2_NORMAL', 'P3_LOW', 'P4_OPTIONAL']
    for pri in priority_order:
        count = stats['priorities'].get(pri, 0)
        pct = (count / stats['total_tasks']) * 100 if stats['total_tasks'] > 0 else 0
        print(f"  {pri:15s}: {count:3d}개 ({pct:5.1f}%)")
    
    print(f"\n🔧 그룹 분포")
    for group, count in stats['groups'].items():
        pct = (count / stats['total_tasks']) * 100
        print(f"  {group:15s}: {count:3d}개 ({pct:5.1f}%)")
    
    print(f"\n⚠️  유사한 작업 그룹 (중복 가능성)")
    if similar:
        for i, group in enumerate(similar[:10], 1):  # 상위 10개만
            print(f"\n  그룹 {i} ({len(group)}개):")
            for task in group:
                print(f"    - {task.get('label', 'Unknown')}")
    else:
        print("  (발견되지 않음)")
    
    print("\n" + "=" * 80)
    print("💡 개선 제안")
    print("=" * 80)
    
    # 제안 생성
    if stats['total_tasks'] > 300:
        print("\n1. 작업 개수가 많습니다 (300개 이상)")
        print("   → 카테고리별 파일 분할 고려")
        print("   → DB 기반 레지스트리 도입 고려")
    
    if similar:
        print(f"\n2. 유사한 작업 {len(similar)}개 그룹 발견")
        print("   → 통합 또는 매개변수화 검토")
    
    if stats['priorities'].get('P4_OPTIONAL', 0) > stats['total_tasks'] * 0.3:
        print("\n3. 선택적 작업(P4)이 30% 이상")
        print("   → 사용 빈도 낮은 작업 아카이브 고려")
    
    print("\n" + "=" * 80)

def main():
    """메인 함수"""
    try:
        # tasks.json 로드
        workspace_root = Path(__file__).parent.parent
        tasks_path = workspace_root / ".vscode" / "tasks.json"
        
        print(f"📂 분석 중: {tasks_path}")
        data = load_tasks_json(str(tasks_path))
        
        # 분석
        stats = analyze_tasks(data)
        similar = find_similar_tasks(data)
        
        # 보고서 출력
        print_report(stats, similar)
        
        # JSON 저장
        output_path = workspace_root / "outputs" / "tasks_analysis.json"
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                "stats": stats,
                "similar_groups": [[t.get("label") for t in group] for group in similar]
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 상세 결과 저장: {output_path}")
        
    except FileNotFoundError:
        print("❌ tasks.json 파일을 찾을 수 없습니다.")
        print(f"   경로: {tasks_path}")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    main()
