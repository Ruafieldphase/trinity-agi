#!/usr/bin/env python3
"""
Rhythm Health Checker
리듬 기반 시스템의 건강도를 체크합니다.

각 루프(Self-care, 목표 생성/실행, 피드백)의 박자와 동기화 상태를 모니터링합니다.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import argparse

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class RhythmHealthChecker:
    """리듬 건강도 체크 클래스"""
    
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.outputs = workspace / "outputs"
        self.memory = workspace / "fdo_agi_repo" / "memory"
        
        # 기대되는 리듬 주기 (분 단위)
        self.expected_rhythms = {
            "self_care_update": 30,  # Self-care 요약 갱신
            "goal_generation": 60,   # 목표 생성
            "goal_execution": 30,    # 목표 실행
            "feedback_analysis": 60, # 피드백 분석
            "trinity_cycle": 1440,   # Trinity 사이클 (24시간)
        }
        
        # 허용 지연 시간 (분 단위)
        self.tolerance_minutes = 15
    
    def check_file_freshness(self, filepath: Path, expected_interval_minutes: int) -> Dict[str, Any]:
        """파일의 최신성을 체크합니다."""
        if not filepath.exists():
            return {
                "status": "missing",
                "message": f"파일이 존재하지 않습니다: {filepath.name}",
                "severity": "high"
            }
        
        mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
        age_minutes = (datetime.now() - mtime).total_seconds() / 60
        
        expected_with_tolerance = expected_interval_minutes + self.tolerance_minutes
        
        if age_minutes <= expected_interval_minutes:
            return {
                "status": "healthy",
                "age_minutes": round(age_minutes, 1),
                "message": f"정상 (최근 {round(age_minutes, 1)}분)",
                "severity": "none"
            }
        elif age_minutes <= expected_with_tolerance:
            return {
                "status": "warning",
                "age_minutes": round(age_minutes, 1),
                "message": f"경고: 약간 오래됨 (최근 {round(age_minutes, 1)}분)",
                "severity": "low"
            }
        else:
            return {
                "status": "stale",
                "age_minutes": round(age_minutes, 1),
                "message": f"정체: 너무 오래됨 (최근 {round(age_minutes, 1)}분)",
                "severity": "high"
            }
    
    def check_self_care_rhythm(self) -> Dict[str, Any]:
        """Self-care 루프 리듬 체크"""
        summary_file = self.outputs / "self_care_metrics_summary.json"
        report_file = self.outputs / "self_care_report.md"
        
        summary_check = self.check_file_freshness(
            summary_file,
            self.expected_rhythms["self_care_update"]
        )
        report_check = self.check_file_freshness(
            report_file,
            self.expected_rhythms["self_care_update"]
        )
        
        # Self-care 요약 내용 분석
        alerts = []
        if summary_file.exists():
            try:
                with open(summary_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # 정체 감지
                    if data.get("stagnation_detected"):
                        alerts.append({
                            "type": "stagnation",
                            "message": "Self-care 루프 정체 감지됨",
                            "severity": "high"
                        })
                    
                    # 순환 이상 감지
                    if data.get("circulation_anomaly"):
                        alerts.append({
                            "type": "circulation",
                            "message": "순환 이상 감지됨",
                            "severity": "medium"
                        })
                    
                    # 경고 수 체크
                    warnings = data.get("warnings", [])
                    if len(warnings) > 3:
                        alerts.append({
                            "type": "warnings",
                            "message": f"{len(warnings)}개의 경고 발견",
                            "severity": "medium"
                        })
            except Exception as e:
                alerts.append({
                    "type": "error",
                    "message": f"Self-care 요약 파싱 실패: {e}",
                    "severity": "high"
                })
        
        return {
            "loop_name": "Self-Care",
            "summary_file_status": summary_check,
            "report_file_status": report_check,
            "alerts": alerts,
            "overall_health": self._calculate_health_score([summary_check, report_check], alerts)
        }
    
    def check_goal_generation_rhythm(self) -> Dict[str, Any]:
        """목표 생성 리듬 체크"""
        goals_file = self.outputs / "autonomous_goals_latest.json"
        
        goals_check = self.check_file_freshness(
            goals_file,
            self.expected_rhythms["goal_generation"]
        )
        
        alerts = []
        if goals_file.exists():
            try:
                with open(goals_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    goals = data.get("goals", [])
                    
                    # 목표 수 체크
                    if len(goals) == 0:
                        alerts.append({
                            "type": "no_goals",
                            "message": "생성된 목표가 없습니다",
                            "severity": "medium"
                        })
                    elif len(goals) > 20:
                        alerts.append({
                            "type": "too_many_goals",
                            "message": f"목표가 너무 많습니다 ({len(goals)}개)",
                            "severity": "low"
                        })
                    
                    # 긴급 목표 체크
                    urgent_count = sum(1 for g in goals if g.get("priority") == "urgent")
                    if urgent_count > 5:
                        alerts.append({
                            "type": "urgent_overload",
                            "message": f"긴급 목표가 {urgent_count}개로 과다",
                            "severity": "high"
                        })
            except Exception as e:
                alerts.append({
                    "type": "error",
                    "message": f"목표 파일 파싱 실패: {e}",
                    "severity": "high"
                })
        
        return {
            "loop_name": "Goal Generation",
            "file_status": goals_check,
            "alerts": alerts,
            "overall_health": self._calculate_health_score([goals_check], alerts)
        }
    
    def check_goal_execution_rhythm(self) -> Dict[str, Any]:
        """목표 실행 리듬 체크"""
        tracker_file = self.memory / "goal_tracker.json"
        
        tracker_check = self.check_file_freshness(
            tracker_file,
            self.expected_rhythms["goal_execution"]
        )
        
        alerts = []
        if tracker_file.exists():
            try:
                with open(tracker_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    goals = data.get("goals", [])
                    
                    # 실행 중인 목표 체크
                    in_progress = [g for g in goals if g.get("status") == "in_progress"]
                    if len(in_progress) > 3:
                        alerts.append({
                            "type": "too_many_in_progress",
                            "message": f"동시 실행 중인 목표가 {len(in_progress)}개로 과다",
                            "severity": "medium"
                        })
                    
                    # 실패 목표 체크
                    failed = [g for g in goals if g.get("status") == "failed"]
                    if len(goals) > 0 and len(failed) > len(goals) * 0.3:  # 30% 이상 실패
                        alerts.append({
                            "type": "high_failure_rate",
                            "message": f"실패율이 높습니다 ({len(failed)}/{len(goals)})",
                            "severity": "high"
                        })
                    
                    # 정체 목표 체크 (24시간 이상 in_progress)
                    now = datetime.now()
                    for goal in goals:
                        if goal.get("status") == "in_progress":
                            started = datetime.fromisoformat(goal.get("started_at", now.isoformat()))
                            if (now - started).total_seconds() > 86400:  # 24시간
                                alerts.append({
                                    "type": "stalled_goal",
                                    "message": f"목표 정체: {goal.get('title', goal.get('id'))}",
                                    "severity": "high"
                                })
            except Exception as e:
                alerts.append({
                    "type": "error",
                    "message": f"목표 추적 파일 파싱 실패: {e}",
                    "severity": "high"
                })
        
        return {
            "loop_name": "Goal Execution",
            "file_status": tracker_check,
            "alerts": alerts,
            "overall_health": self._calculate_health_score([tracker_check], alerts)
        }
    
    def check_feedback_rhythm(self) -> Dict[str, Any]:
        """피드백 루프 리듬 체크"""
        feedback_file = self.outputs / "autonomous_goal_feedback_latest.json"
        
        feedback_check = self.check_file_freshness(
            feedback_file,
            self.expected_rhythms["feedback_analysis"]
        )
        
        alerts = []
        if feedback_file.exists():
            try:
                with open(feedback_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # 전체 성공률 체크
                    success_rate = data.get("overall_success_rate", 0)
                    if success_rate < 0.5:
                        alerts.append({
                            "type": "low_success_rate",
                            "message": f"전체 성공률이 낮습니다 ({success_rate:.1%})",
                            "severity": "high"
                        })
                    
                    # 개선 추세 체크
                    trend = data.get("improvement_trend", "stable")
                    if trend == "declining":
                        alerts.append({
                            "type": "declining_trend",
                            "message": "성능이 하락 추세입니다",
                            "severity": "medium"
                        })
            except Exception as e:
                alerts.append({
                    "type": "error",
                    "message": f"피드백 파일 파싱 실패: {e}",
                    "severity": "high"
                })
        
        return {
            "loop_name": "Feedback",
            "file_status": feedback_check,
            "alerts": alerts,
            "overall_health": self._calculate_health_score([feedback_check], alerts)
        }
    
    def check_trinity_rhythm(self) -> Dict[str, Any]:
        """Trinity 사이클 리듬 체크"""
        trinity_file = self.outputs / "autopoietic_trinity_cycle_latest.json"
        
        trinity_check = self.check_file_freshness(
            trinity_file,
            self.expected_rhythms["trinity_cycle"]
        )
        
        alerts = []
        if trinity_file.exists():
            try:
                with open(trinity_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Trinity 권장사항 체크
                    recommendations = data.get("recommendations", [])
                    if len(recommendations) > 5:
                        alerts.append({
                            "type": "many_recommendations",
                            "message": f"{len(recommendations)}개의 Trinity 권장사항",
                            "severity": "low"
                        })
            except Exception as e:
                alerts.append({
                    "type": "error",
                    "message": f"Trinity 파일 파싱 실패: {e}",
                    "severity": "low"  # Trinity는 선택적
                })
        
        return {
            "loop_name": "Trinity",
            "file_status": trinity_check,
            "alerts": alerts,
            "overall_health": self._calculate_health_score([trinity_check], alerts)
        }
    
    def _calculate_health_score(self, file_checks: List[Dict], alerts: List[Dict]) -> Dict[str, Any]:
        """전체 건강도 점수 계산"""
        # 파일 상태 점수
        file_scores = []
        for check in file_checks:
            if check["status"] == "healthy":
                file_scores.append(100)
            elif check["status"] == "warning":
                file_scores.append(70)
            elif check["status"] == "stale":
                file_scores.append(30)
            else:  # missing
                file_scores.append(0)
        
        file_score = sum(file_scores) / len(file_scores) if file_scores else 0
        
        # 알림 점수 감소
        alert_penalty = 0
        for alert in alerts:
            if alert["severity"] == "high":
                alert_penalty += 30
            elif alert["severity"] == "medium":
                alert_penalty += 15
            elif alert["severity"] == "low":
                alert_penalty += 5
        
        final_score = max(0, file_score - alert_penalty)
        
        # 상태 결정
        if final_score >= 80:
            status = "healthy"
            emoji = "✅"
        elif final_score >= 60:
            status = "warning"
            emoji = "⚠️"
        elif final_score >= 40:
            status = "degraded"
            emoji = "🔶"
        else:
            status = "critical"
            emoji = "🚨"
        
        return {
            "score": round(final_score, 1),
            "status": status,
            "emoji": emoji
        }
    
    def check_rhythm_synchronization(self, results: Dict[str, Dict]) -> Dict[str, Any]:
        """리듬 동기화 상태 체크"""
        # 각 루프의 최종 갱신 시간 수집
        update_times = {}
        for loop_name, result in results.items():
            file_status = result.get("file_status") or result.get("summary_file_status")
            if file_status and file_status.get("status") != "missing":
                update_times[loop_name] = file_status.get("age_minutes", 999)
        
        if len(update_times) < 2:
            return {
                "synchronized": False,
                "message": "동기화 판단에 충분한 데이터가 없습니다",
                "max_time_diff": None
            }
        
        # 최대 시간 차이 계산
        max_time_diff = max(update_times.values()) - min(update_times.values())
        
        # 동기화 판단 (30분 이내 차이면 동기화됨)
        synchronized = max_time_diff <= 30
        
        return {
            "synchronized": synchronized,
            "max_time_diff_minutes": round(max_time_diff, 1),
            "message": f"최대 시간 차이: {round(max_time_diff, 1)}분" if not synchronized else "리듬이 동기화되어 있습니다",
            "update_times": {k: round(v, 1) for k, v in update_times.items()}
        }
    
    def run_health_check(self) -> Dict[str, Any]:
        """전체 건강도 체크 실행"""
        print("🔍 리듬 건강도 체크 시작...\n")
        
        # 각 루프 체크
        results = {
            "self_care": self.check_self_care_rhythm(),
            "goal_generation": self.check_goal_generation_rhythm(),
            "goal_execution": self.check_goal_execution_rhythm(),
            "feedback": self.check_feedback_rhythm(),
            "trinity": self.check_trinity_rhythm(),
        }
        
        # 동기화 체크
        sync_status = self.check_rhythm_synchronization(results)
        
        # 전체 점수 계산
        overall_scores = [r["overall_health"]["score"] for r in results.values()]
        overall_score = sum(overall_scores) / len(overall_scores)
        
        # 심각도 높은 알림 수집
        critical_alerts = []
        for loop_name, result in results.items():
            for alert in result.get("alerts", []):
                if alert["severity"] in ["high", "medium"]:
                    critical_alerts.append({
                        "loop": loop_name,
                        **alert
                    })
        
        # 전체 상태 결정
        if overall_score >= 80 and sync_status["synchronized"]:
            overall_status = "healthy"
            overall_emoji = "✅"
        elif overall_score >= 60:
            overall_status = "warning"
            overall_emoji = "⚠️"
        elif overall_score >= 40:
            overall_status = "degraded"
            overall_emoji = "🔶"
        else:
            overall_status = "critical"
            overall_emoji = "🚨"
        
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": overall_status,
            "overall_emoji": overall_emoji,
            "overall_score": round(overall_score, 1),
            "loop_results": results,
            "synchronization": sync_status,
            "critical_alerts": critical_alerts,
            "recommendations": self._generate_recommendations(results, sync_status, critical_alerts)
        }
    
    def _generate_recommendations(self, results: Dict, sync_status: Dict, critical_alerts: List) -> List[str]:
        """권장사항 생성"""
        recommendations = []
        
        # 동기화 문제
        if not sync_status["synchronized"]:
            recommendations.append(
                f"⏰ 리듬 동기화 필요: 최대 {sync_status['max_time_diff_minutes']}분 차이 발생"
            )
        
        # Self-care 문제
        sc_result = results.get("self_care", {})
        if sc_result.get("overall_health", {}).get("score", 100) < 60:
            recommendations.append(
                "🛟 Self-care 루프 점검 필요: scripts/update_self_care_metrics.ps1 실행"
            )
        
        # 목표 생성 문제
        gg_result = results.get("goal_generation", {})
        if gg_result.get("file_status", {}).get("status") == "stale":
            recommendations.append(
                "🎯 목표 생성기 재실행 필요: python scripts/autonomous_goal_generator.py"
            )
        
        # 목표 실행 문제
        ge_result = results.get("goal_execution", {})
        ge_alerts = [a for a in ge_result.get("alerts", []) if a["severity"] == "high"]
        if ge_alerts:
            recommendations.append(
                "⚙️ 목표 실행 상태 점검: fdo_agi_repo/memory/goal_tracker.json 확인"
            )
        
        # 피드백 문제
        fb_result = results.get("feedback", {})
        fb_alerts = [a for a in fb_result.get("alerts", []) if a["type"] == "low_success_rate"]
        if fb_alerts:
            recommendations.append(
                "📊 성공률 하락: 목표 전략 재검토 필요"
            )
        
        # 일반 권장사항
        if not recommendations:
            recommendations.append("✅ 모든 리듬이 정상입니다")
        
        return recommendations

def main():
    parser = argparse.ArgumentParser(description="리듬 건강도 체크")
    parser.add_argument("--workspace", type=str, default=str(Path(__file__).parent.parent),
                        help="작업 공간 경로")
    parser.add_argument("--output", type=str, help="결과 저장 경로 (JSON)")
    parser.add_argument("--verbose", action="store_true", help="상세 출력")
    
    args = parser.parse_args()
    
    workspace = Path(args.workspace)
    checker = RhythmHealthChecker(workspace)
    
    # 건강도 체크 실행
    result = checker.run_health_check()
    
    # 결과 출력
    print(f"\n{result['overall_emoji']} 전체 상태: {result['overall_status'].upper()}")
    print(f"📊 전체 점수: {result['overall_score']}/100\n")
    
    # 각 루프 상태
    print("=== 루프별 상태 ===")
    for loop_name, loop_result in result["loop_results"].items():
        health = loop_result["overall_health"]
        print(f"{health['emoji']} {loop_result['loop_name']}: {health['score']}/100 ({health['status']})")
    
    # 동기화 상태
    sync = result["synchronization"]
    sync_emoji = "✅" if sync["synchronized"] else "⚠️"
    print(f"\n{sync_emoji} 동기화: {sync['message']}")
    
    # 심각한 알림
    if result["critical_alerts"]:
        print(f"\n🚨 심각한 알림 ({len(result['critical_alerts'])}개):")
        for alert in result["critical_alerts"]:
            print(f"  [{alert['loop']}] {alert['message']}")
    
    # 권장사항
    print(f"\n💡 권장사항:")
    for rec in result["recommendations"]:
        print(f"  {rec}")
    
    # JSON 저장
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n✅ 결과 저장: {output_path}")
    
    # 상세 출력
    if args.verbose:
        print("\n=== 상세 정보 ===")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 종료 코드 (critical이면 1, 아니면 0)
    sys.exit(1 if result["overall_status"] == "critical" else 0)

if __name__ == "__main__":
    main()
