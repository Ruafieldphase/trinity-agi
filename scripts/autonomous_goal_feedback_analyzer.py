#!/usr/bin/env python3
"""
자율 목표 피드백 분석기
goal_tracker.json의 실행 이력을 분석하여 다음 목표 생성에 활용할 인사이트 추출
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from collections import defaultdict

WORKSPACE = Path(__file__).parent.parent
GOAL_TRACKER = WORKSPACE / "fdo_agi_repo" / "memory" / "goal_tracker.json"
RESONANCE_LEDGER = WORKSPACE / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"
FEEDBACK_OUTPUT = WORKSPACE / "fdo_agi_repo" / "memory" / "goal_feedback_insights.json"


def load_goal_tracker() -> Dict[str, Any]:
    """goal_tracker.json 로드"""
    if not GOAL_TRACKER.exists():
        return {"goals": []}
    
    with open(GOAL_TRACKER, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_recent_resonance(hours: int = 24) -> List[Dict[str, Any]]:
    """최근 resonance 이벤트 로드"""
    if not RESONANCE_LEDGER.exists():
        return []
    
    cutoff = datetime.now() - timedelta(hours=hours)
    events = []
    
    with open(RESONANCE_LEDGER, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                event_time = datetime.fromisoformat(event.get("timestamp", "").replace("Z", "+00:00"))
                if event_time >= cutoff:
                    events.append(event)
            except:
                continue
    
    return events


def analyze_goal_type_performance(tracker: Dict[str, Any]) -> Dict[str, Any]:
    """목표 타입별 성공률 분석"""
    type_stats = defaultdict(lambda: {"total": 0, "success": 0, "failed": 0})
    
    for goal in tracker.get("goals", []):
        goal_type = goal.get("type", "unknown")
        executions = goal.get("executions", [])
        
        for ex in executions:
            type_stats[goal_type]["total"] += 1
            status = ex.get("status", "unknown")
            if status == "success":
                type_stats[goal_type]["success"] += 1
            elif status == "failed":
                type_stats[goal_type]["failed"] += 1
    
    # 성공률 계산
    for goal_type, stats in type_stats.items():
        if stats["total"] > 0:
            stats["success_rate"] = round(stats["success"] / stats["total"] * 100, 1)
        else:
            stats["success_rate"] = 0.0
    
    # 성공률 순으로 정렬
    sorted_types = sorted(type_stats.items(), key=lambda x: x[1]["success_rate"], reverse=True)
    
    return {
        "type_stats": dict(type_stats),
        "best_performing": sorted_types[0] if sorted_types else ("none", {}),
        "worst_performing": sorted_types[-1] if sorted_types else ("none", {})
    }


def analyze_priority_effectiveness(tracker: Dict[str, Any]) -> Dict[str, Any]:
    """우선순위별 실행률 분석 (높은 우선순위가 실제로 먼저 실행되는지)"""
    priority_execution = defaultdict(list)
    
    for goal in tracker.get("goals", []):
        priority = goal.get("priority", 5)
        executions = goal.get("executions", [])
        
        if executions:
            # 첫 실행까지 걸린 시간 (생성 시간 vs 첫 실행 시간)
            created = goal.get("created_at", "")
            first_exec = executions[0].get("timestamp", "")
            
            if created and first_exec:
                try:
                    created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                    exec_dt = datetime.fromisoformat(first_exec.replace("Z", "+00:00"))
                    delay = (exec_dt - created_dt).total_seconds()
                    priority_execution[priority].append(delay)
                except:
                    pass
    
    # 우선순위별 평균 지연 시간
    priority_delays = {}
    for priority, delays in priority_execution.items():
        if delays:
            priority_delays[priority] = {
                "avg_delay_seconds": round(sum(delays) / len(delays), 2),
                "count": len(delays)
            }
    
    # 우선순위 역상관 확인 (높은 우선순위 = 낮은 지연)
    is_effective = True
    if len(priority_delays) >= 2:
        sorted_by_priority = sorted(priority_delays.items(), key=lambda x: x[0], reverse=True)
        for i in range(len(sorted_by_priority) - 1):
            high_pri = sorted_by_priority[i]
            low_pri = sorted_by_priority[i + 1]
            # 높은 우선순위가 더 긴 지연이면 비효과적
            if high_pri[1]["avg_delay_seconds"] > low_pri[1]["avg_delay_seconds"]:
                is_effective = False
                break
    
    return {
        "priority_delays": priority_delays,
        "is_priority_effective": is_effective,
        "recommendation": "우선순위 시스템 작동 중" if is_effective else "우선순위 조정 필요"
    }


def analyze_resonance_goal_correlation(tracker: Dict[str, Any], 
                                       resonance_events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Resonance 상태와 목표 성공률 상관관계 분석"""
    
    # Resonance 상태별 목표 실행 결과
    resonance_goal_map = defaultdict(lambda: {"success": 0, "failed": 0})
    
    for goal in tracker.get("goals", []):
        executions = goal.get("executions", [])
        for ex in executions:
            exec_time = ex.get("timestamp", "")
            if not exec_time:
                continue
            
            try:
                exec_dt = datetime.fromisoformat(exec_time.replace("Z", "+00:00"))
            except:
                continue
            
            # 가장 가까운 resonance 이벤트 찾기
            closest_resonance = None
            min_diff = float('inf')
            
            for event in resonance_events:
                event_time_str = event.get("timestamp", "")
                if not event_time_str:
                    continue
                try:
                    event_dt = datetime.fromisoformat(event_time_str.replace("Z", "+00:00"))
                    diff = abs((exec_dt - event_dt).total_seconds())
                    if diff < min_diff and diff < 3600:  # 1시간 이내
                        min_diff = diff
                        closest_resonance = event
                except:
                    continue
            
            if closest_resonance:
                level = closest_resonance.get("level", "unknown")
                status = ex.get("status", "unknown")
                
                if status == "success":
                    resonance_goal_map[level]["success"] += 1
                elif status == "failed":
                    resonance_goal_map[level]["failed"] += 1
    
    # 성공률 계산
    resonance_success_rates = {}
    for level, counts in resonance_goal_map.items():
        total = counts["success"] + counts["failed"]
        if total > 0:
            resonance_success_rates[level] = {
                "success_rate": round(counts["success"] / total * 100, 1),
                "total_executions": total
            }
    
    # 최고/최악 resonance 상태
    sorted_resonance = sorted(resonance_success_rates.items(), 
                             key=lambda x: x[1]["success_rate"], reverse=True)
    
    return {
        "resonance_success_rates": resonance_success_rates,
        "best_resonance_for_goals": sorted_resonance[0] if sorted_resonance else ("unknown", {}),
        "worst_resonance_for_goals": sorted_resonance[-1] if sorted_resonance else ("unknown", {}),
        "recommendation": f"목표 실행 최적 상태: {sorted_resonance[0][0] if sorted_resonance else 'N/A'}"
    }


def generate_adaptive_recommendations(type_perf: Dict[str, Any],
                                      priority_eff: Dict[str, Any],
                                      resonance_corr: Dict[str, Any]) -> List[str]:
    """적응형 추천사항 생성"""
    recommendations = []
    
    # 1. 목표 타입 추천
    best_type = type_perf.get("best_performing", ("none", {}))[0]
    worst_type = type_perf.get("worst_performing", ("none", {}))[0]
    
    if best_type != "none":
        best_rate = type_perf["type_stats"].get(best_type, {}).get("success_rate", 0)
        recommendations.append(
            f"📈 '{best_type}' 타입 목표가 {best_rate}% 성공률로 가장 효과적 → 우선 생성 추천"
        )
    
    if worst_type != "none" and worst_type != best_type:
        worst_rate = type_perf["type_stats"].get(worst_type, {}).get("success_rate", 0)
        if worst_rate < 50:
            recommendations.append(
                f"⚠️ '{worst_type}' 타입 목표가 {worst_rate}% 성공률로 저조 → 개선 필요 또는 생성 빈도 감소"
            )
    
    # 2. 우선순위 시스템 추천
    if not priority_eff.get("is_priority_effective", True):
        recommendations.append(
            "⚙️ 우선순위 시스템 비효과적 → 실행 로직 재검토 필요"
        )
    
    # 3. Resonance 상태 추천
    best_resonance = resonance_corr.get("best_resonance_for_goals", ("unknown", {}))[0]
    if best_resonance != "unknown":
        best_res_rate = resonance_corr["resonance_success_rates"].get(best_resonance, {}).get("success_rate", 0)
        recommendations.append(
            f"🎯 '{best_resonance}' 상태에서 목표 성공률 {best_res_rate}% → 해당 상태 탐지 시 목표 실행 권장"
        )
    
    return recommendations


def save_feedback_insights(insights: Dict[str, Any]):
    """피드백 인사이트 저장"""
    FEEDBACK_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    
    with open(FEEDBACK_OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(insights, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 피드백 인사이트 저장: {FEEDBACK_OUTPUT}")


def main():
    print("🔍 자율 목표 피드백 분석 시작...")
    
    # 1. 데이터 로드
    print("   📂 goal_tracker.json 로드...")
    tracker = load_goal_tracker()
    
    print("   📂 resonance_ledger.jsonl 로드 (최근 24h)...")
    resonance_events = load_recent_resonance(hours=24)
    
    # 2. 분석
    print("   📊 목표 타입별 성능 분석...")
    type_performance = analyze_goal_type_performance(tracker)
    
    print("   📊 우선순위 효과성 분석...")
    priority_effectiveness = analyze_priority_effectiveness(tracker)
    
    print("   📊 Resonance-목표 상관관계 분석...")
    resonance_correlation = analyze_resonance_goal_correlation(tracker, resonance_events)
    
    # 3. 추천사항 생성
    print("   🎯 적응형 추천사항 생성...")
    recommendations = generate_adaptive_recommendations(
        type_performance, priority_effectiveness, resonance_correlation
    )
    
    # 4. 결과 통합
    insights = {
        "timestamp": datetime.now().isoformat(),
        "analysis_period_hours": 24,
        "type_performance": type_performance,
        "priority_effectiveness": priority_effectiveness,
        "resonance_correlation": resonance_correlation,
        "recommendations": recommendations,
        "metadata": {
            "total_goals": len(tracker.get("goals", [])),
            "total_resonance_events": len(resonance_events)
        }
    }
    
    # 5. 저장
    save_feedback_insights(insights)
    
    # 6. 요약 출력
    print("\n" + "="*50)
    print("📊 피드백 분석 결과 요약")
    print("="*50)
    
    print(f"\n🎯 목표 타입 성능:")
    best_type, best_stats = type_performance.get("best_performing", ("none", {}))
    if best_type != "none":
        print(f"   최고: {best_type} ({best_stats.get('success_rate', 0)}% 성공률)")
    
    print(f"\n⚙️ 우선순위 시스템:")
    print(f"   {'✅ 효과적' if priority_effectiveness.get('is_priority_effective') else '⚠️ 개선 필요'}")
    
    print(f"\n🎯 Resonance 상관관계:")
    best_res, best_res_stats = resonance_correlation.get("best_resonance_for_goals", ("unknown", {}))
    if best_res != "unknown":
        print(f"   최적: {best_res} ({best_res_stats.get('success_rate', 0)}% 성공률)")
    
    print(f"\n💡 추천사항 ({len(recommendations)}개):")
    for i, rec in enumerate(recommendations, 1):
        print(f"   {i}. {rec}")
    
    print("\n✅ 분석 완료!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
