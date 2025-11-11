#!/usr/bin/env python3
"""
Meta Supervisor
시스템 전체를 조율하는 메타-감독 모듈

리듬 건강도를 모니터링하고, 필요시 최소한의 개입을 수행합니다.
"""

import json
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import argparse

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class MetaSupervisor:
    """메타-감독 클래스"""
    
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.outputs = workspace / "outputs"
        self.scripts = workspace / "scripts"
        self.fdo_agi_repo = workspace / "fdo_agi_repo"
        
        # 파이썬 실행 파일 경로
        self.python_exe = self._find_python_exe()
        
        # 개입 임계값
        self.intervention_threshold = 40  # 점수가 이 이하면 자동 개입
        self.critical_threshold = 30  # 이 이하면 긴급 개입

    def _run_cmd(self, cmd: List[str]) -> Dict[str, Any]:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            return {
                "exit_code": result.returncode,
                "stdout": result.stdout[-800:],
                "stderr": result.stderr[-800:],
                "success": result.returncode == 0,
            }
        except Exception as e:
            return {"exit_code": -1, "stderr": str(e), "stdout": "", "success": False}

    def determine_verification_level(self, health_data: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """건강 신호 기반 검증 강도(light/medium/strict) 결정"""
        score = analysis.get("score", 0)
        level = analysis.get("intervention_level", "none")
        sync = health_data.get("synchronization", {})
        max_diff = sync.get("max_time_diff_minutes", 0) or 0

        if level == "critical" or score < 40 or max_diff >= 120:
            return "strict"
        if level == "warning" or score < 60 or max_diff >= 60:
            return "medium"
        return "light"

    def run_self_verification(self, level: str) -> List[Dict[str, Any]]:
        """검증 강도에 따른 셀프-검증 실행"""
        tasks: List[Dict[str, Any]] = []

        def add_task(name: str, cmd: List[str]):
            res = self._run_cmd(cmd)
            tasks.append({"name": name, **res})

        # 공통 경로
        val_settings = self.scripts / "validate_settings_json.py"
        val_observer = self.scripts / "validate_observer_dashboard_integration.py"
        val_perf_ps = self.scripts / "validate_performance_dashboard.ps1"
        diag_sys = self.scripts / "system_integration_diagnostic.py"

        if level in ("light", "medium", "strict"):
            if val_settings.exists():
                add_task("validate_settings_json", [self.python_exe, str(val_settings)])
            if val_observer.exists():
                add_task("validate_observer_dashboard", [self.python_exe, str(val_observer)])

        if level in ("medium", "strict"):
            if val_perf_ps.exists():
                add_task("validate_performance_dashboard", ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(val_perf_ps), "-VerboseOutput"])  # type: ignore

        if level == "strict":
            if diag_sys.exists():
                add_task("system_integration_diagnostic", [self.python_exe, str(diag_sys)])

        return tasks

    def attempt_auto_remediation(self, verification_results: List[Dict[str, Any]]) -> List[str]:
        """간단한 자동 시정 조치 시도 (중간/강 검증에서만 의미)"""
        notes: List[str] = []
        # Observer 대시보드 신선도 실패 시 통합 파이프라인 실행 시도
        need_refresh = False
        for v in verification_results or []:
            if v.get("name") == "validate_observer_dashboard" and not v.get("success"):
                out = (v.get("stdout") or "") + "\n" + (v.get("stderr") or "")
                if "신선도" in out or "fresh" in out.lower():
                    need_refresh = True
                    break
        if need_refresh:
            pipeline = self.scripts / "integrate_stream_observer_dashboard.py"
            if pipeline.exists():
                res = self._run_cmd([self.python_exe, str(pipeline)])
                if res.get("success"):
                    notes.append("observer_dashboard_refreshed")
                else:
                    notes.append("observer_dashboard_refresh_failed")
        return notes
    
    def _find_python_exe(self) -> str:
        """파이썬 실행 파일 찾기"""
        venv_python = self.fdo_agi_repo / ".venv" / "Scripts" / "python.exe"
        if venv_python.exists():
            return str(venv_python)
        return "python"
    
    def run_rhythm_health_check(self) -> Dict[str, Any]:
        """리듬 건강도 체크 실행"""
        print("🔍 리듬 건강도 체크 실행 중...")
        
        checker_script = self.scripts / "rhythm_health_checker.py"
        output_file = self.outputs / "rhythm_health_latest.json"
        
        try:
            result = subprocess.run(
                [self.python_exe, str(checker_script), "--output", str(output_file)],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            # 결과 로드
            if output_file.exists():
                with open(output_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print(f"⚠️  건강도 체크 결과 파일 없음: {output_file}")
                return {}
        
        except Exception as e:
            print(f"❌ 건강도 체크 실패: {e}")
            return {}
    
    def analyze_health_status(self, health_data: Dict[str, Any]) -> Dict[str, Any]:
        """건강 상태 분석 및 액션 결정"""
        if not health_data:
            return {
                "needs_intervention": True,
                "intervention_level": "critical",
                "reason": "건강도 체크 데이터 없음",
                "actions": ["run_health_check"]
            }
        
        score = health_data.get("overall_score", 0)
        status = health_data.get("overall_status", "unknown")
        critical_alerts = health_data.get("critical_alerts", [])
        sync = health_data.get("synchronization", {})
        
        actions = []
        needs_intervention = False
        intervention_level = "none"
        reasons = []
        
        # 점수 기반 판단
        if score < self.critical_threshold:
            needs_intervention = True
            intervention_level = "critical"
            reasons.append(f"심각한 상태: 점수 {score}/100")
            actions.extend(["emergency_recovery", "notify_admin"])
        elif score < self.intervention_threshold:
            needs_intervention = True
            intervention_level = "warning"
            reasons.append(f"경고 상태: 점수 {score}/100")
        
        # 심각한 알림 기반 판단
        high_severity_alerts = [a for a in critical_alerts if a.get("severity") == "high"]
        if high_severity_alerts:
            needs_intervention = True
            if intervention_level == "none":
                intervention_level = "warning"
            reasons.append(f"{len(high_severity_alerts)}개의 심각한 알림")
        
        # 동기화 문제
        if not sync.get("synchronized", True):
            reasons.append(f"리듬 동기화 필요 (차이: {sync.get('max_time_diff_minutes', 0)}분)")
            if intervention_level != "critical":
                intervention_level = "warning"
        
        # 루프별 구체적인 액션 결정
        loop_results = health_data.get("loop_results", {})
        
        # Self-care 루프
        sc_result = loop_results.get("self_care", {})
        if sc_result.get("overall_health", {}).get("score", 100) < 60:
            actions.append("update_self_care")
            reasons.append("Self-care 루프 점검 필요")
        
        # 목표 생성
        gg_result = loop_results.get("goal_generation", {})
        if gg_result.get("file_status", {}).get("status") == "stale":
            actions.append("generate_goals")
            reasons.append("목표 생성기 재실행 필요")
        
        # 목표 실행
        ge_result = loop_results.get("goal_execution", {})
        ge_high_alerts = [a for a in ge_result.get("alerts", []) if a.get("severity") == "high"]
        if ge_high_alerts:
            actions.append("check_goal_tracker")
            reasons.append("목표 실행 상태 점검 필요")
        
        # 피드백
        fb_result = loop_results.get("feedback", {})
        if fb_result.get("file_status", {}).get("status") in ["stale", "missing"]:
            actions.append("analyze_feedback")
            reasons.append("피드백 분석 필요")
        
        # Trinity
        trinity_result = loop_results.get("trinity", {})
        if trinity_result.get("file_status", {}).get("status") == "missing":
            # Trinity는 선택적이므로 경고만
            reasons.append("Trinity 사이클 누락 (선택적)")
        
        # 액션이 하나라도 있거나 경고/치명 수준이면 개입 필요로 간주
        if actions or intervention_level != "none":
            needs_intervention = True

        return {
            "needs_intervention": needs_intervention,
            "intervention_level": intervention_level,
            "reasons": reasons,
            "actions": list(set(actions)),  # 중복 제거
            "score": score,
            "status": status
        }
    
    def execute_action(self, action: str) -> Dict[str, Any]:
        """액션 실행"""
        print(f"⚙️  액션 실행: {action}")
        
        action_map = {
            "update_self_care": self._update_self_care,
            "generate_goals": self._generate_goals,
            "analyze_feedback": self._analyze_feedback,
            "check_goal_tracker": self._check_goal_tracker,
            "run_health_check": self.run_rhythm_health_check,
            "emergency_recovery": self._emergency_recovery,
            "notify_admin": self._notify_admin,
        }
        
        action_func = action_map.get(action)
        if not action_func:
            return {
                "success": False,
                "message": f"알 수 없는 액션: {action}"
            }
        
        try:
            result = action_func()
            return {
                "success": True,
                "action": action,
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "action": action,
                "error": str(e)
            }

    def execute_actions(self, actions: List[str]) -> List[Dict[str, Any]]:
        """액션 리스트 일괄 실행"""
        results: List[Dict[str, Any]] = []
        if not actions:
            return results
        for action in actions:
            results.append(self.execute_action(action))
        return results
    
    def _update_self_care(self) -> str:
        """Self-care 요약 갱신"""
        script = self.scripts / "update_self_care_metrics.ps1"
        if not script.exists():
            return "Self-care 갱신 스크립트 없음"
        
        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(script)],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        return "Self-care 요약 갱신 완료" if result.returncode == 0 else f"갱신 실패: {result.stderr}"
    
    def _generate_goals(self) -> str:
        """목표 생성"""
        script = self.scripts / "autonomous_goal_generator.py"
        if not script.exists():
            return "목표 생성 스크립트 없음"
        
        result = subprocess.run(
            [self.python_exe, str(script), "--hours", "6"],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        return "목표 생성 완료" if result.returncode == 0 else f"생성 실패: {result.stderr}"
    
    def _analyze_feedback(self) -> str:
        """피드백 분석"""
        # 먼저 feedback 분석 실행
        analyze_script = self.scripts / "analyze_feedback.py"
        if not analyze_script.exists():
            return "피드백 분석 스크립트 없음"
        
        result = subprocess.run(
            [self.python_exe, str(analyze_script), "--hours", "24"],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode != 0:
            return f"분석 실패: {result.stderr}"
        
        # 분석 완료 후 액션 적용
        action_script = self.scripts / "apply_feedback_actions.py"
        if action_script.exists():
            action_result = subprocess.run(
                [self.python_exe, str(action_script)],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            return "피드백 분석 및 액션 적용 완료"
        
        return "피드백 분석 완료"
    
    def _check_goal_tracker(self) -> str:
        """목표 추적 상태 확인"""
        tracker_file = self.fdo_agi_repo / "memory" / "goal_tracker.json"
        if not tracker_file.exists():
            return "목표 추적 파일 없음"
        
        with open(tracker_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            goals = data.get("goals", [])
            in_progress = [g for g in goals if g.get("status") == "in_progress"]
            return f"확인 완료: {len(goals)}개 목표 중 {len(in_progress)}개 진행 중"
    
    def _emergency_recovery(self) -> str:
        """긴급 복구"""
        print("  🚨 긴급 복구 시작...")
        recovery_steps = []
        
        # 1. Task Queue Server 재시작
        server_script = self.scripts / "ensure_task_queue_server.ps1"
        if server_script.exists():
            result = subprocess.run(
                ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(server_script)],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            recovery_steps.append("Task Queue Server 재시작" if result.returncode == 0 else "Server 재시작 실패")
        
        # 2. Worker 재시작
        worker_script = self.scripts / "ensure_rpa_worker.ps1"
        if worker_script.exists():
            result = subprocess.run(
                ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(worker_script)],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            recovery_steps.append("RPA Worker 재시작" if result.returncode == 0 else "Worker 재시작 실패")
        
        # 3. Self-care 갱신
        recovery_steps.append(self._update_self_care())
        
        # 4. 목표 생성
        recovery_steps.append(self._generate_goals())
        
        print("  ✅ 긴급 복구 완료")
        return f"긴급 복구 완료: {'; '.join(recovery_steps)}"
    
    def _notify_admin(self) -> str:
        """관리자 알림"""
        # 실제로는 이메일이나 Slack 등으로 알림 전송
        # 여기서는 로그만 기록
        log_file = self.outputs / "meta_supervisor_alerts.log"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now().isoformat()}: CRITICAL - 즉시 확인 필요\n")
        return f"알림 기록: {log_file}"
    
    def generate_supervision_report(self, 
                                     health_data: Dict[str, Any],
                                     analysis: Dict[str, Any],
                                     action_results: List[Dict[str, Any]],
                                     verification_level: Optional[str] = None,
                                     verification_results: Optional[List[Dict[str, Any]]] = None,
                                     remediation_notes: Optional[List[str]] = None) -> str:
        """감독 보고서 생성"""
        report_lines = [
            "# 메타-감독 보고서",
            "",
            f"생성 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 📊 전체 상태",
            "",
            f"- **상태**: {health_data.get('overall_emoji', '❓')} {health_data.get('overall_status', 'unknown').upper()}",
            f"- **점수**: {health_data.get('overall_score', 0)}/100",
            f"- **개입 수준**: {analysis.get('intervention_level', 'none').upper()}",
            "",
            "## 🔍 루프별 상태",
            ""
        ]
        
        # 루프별 상태
        loop_results = health_data.get("loop_results", {})
        for loop_name, loop_result in loop_results.items():
            health = loop_result.get("overall_health", {})
            report_lines.extend([
                f"### {loop_result.get('loop_name', loop_name)}",
                "",
                f"- 점수: {health.get('score', 0)}/100",
                f"- 상태: {health.get('emoji', '❓')} {health.get('status', 'unknown')}",
                ""
            ])
            
            # 알림
            alerts = loop_result.get("alerts", [])
            if alerts:
                report_lines.append("**알림**:")
                for alert in alerts:
                    severity_emoji = {"high": "🚨", "medium": "⚠️", "low": "ℹ️"}.get(alert.get("severity", ""), "❓")
                    report_lines.append(f"- {severity_emoji} {alert.get('message', '')}")
                report_lines.append("")
        
        # 동기화 상태
        sync = health_data.get("synchronization", {})
        report_lines.extend([
            "## ⏰ 리듬 동기화",
            "",
            f"- 동기화 상태: {'✅ 정상' if sync.get('synchronized') else '⚠️  비동기'}",
            f"- {sync.get('message', '')}",
            ""
        ])
        
        # 개입 필요 여부
        if analysis.get("needs_intervention"):
            report_lines.extend([
                "## ⚙️  자동 개입",
                "",
                "**사유**:",
            ])
            for reason in analysis.get("reasons", []):
                report_lines.append(f"- {reason}")
            report_lines.append("")
            
            report_lines.append("**수행된 액션**:")
            for action_result in action_results:
                action = action_result.get("action", "unknown")
                success = action_result.get("success", False)
                result_msg = action_result.get("result", action_result.get("error", ""))
                status_emoji = "✅" if success else "❌"
                report_lines.append(f"- {status_emoji} `{action}`: {result_msg}")
            report_lines.append("")
        else:
            report_lines.extend([
                "## ✅ 시스템 정상",
                "",
                "모든 루프가 안정적으로 동작하고 있습니다. 자동 개입이 필요하지 않습니다.",
                ""
            ])
        
        # 셀프-검증 결과
        if verification_level:
            report_lines.extend([
                "## 🧪 셀프-검증",
                "",
                f"- **검증 강도**: {verification_level.upper()}",
                ""
            ])
            if verification_results:
                for v in verification_results:
                    status_emoji = "✅" if v.get("success") else "❌"
                    name = v.get("name", "unknown")
                    exit_code = v.get("exit_code")
                    report_lines.append(f"- {status_emoji} {name} (exit {exit_code})")
                report_lines.append("")
            if remediation_notes:
                report_lines.append("**자동 시정 조치**:")
                for n in remediation_notes:
                    report_lines.append(f"- {n}")
                report_lines.append("")

        # 권장사항
        recommendations = health_data.get("recommendations", [])
        if recommendations:
            report_lines.extend([
                "## 💡 권장사항",
                ""
            ])
            for rec in recommendations:
                report_lines.append(f"- {rec}")
            report_lines.append("")
        
        # 다음 체크 시간
        report_lines.extend([
            "## ⏭️  다음 체크",
            "",
            f"예상 시각: {(datetime.now() + timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            "",
            "*이 보고서는 메타-감독 시스템에 의해 자동 생성되었습니다.*"
        ])
        
        return "\n".join(report_lines)
    
    def run_supervision_cycle(self) -> Dict[str, Any]:
        """감독 사이클 실행"""
        print("🌊 메타-감독 사이클 시작...")
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # 1. 건강도 체크
        health_data = self.run_rhythm_health_check()
        if not health_data:
            print("❌ 건강도 데이터를 가져올 수 없습니다.")
            return {
                "success": False,
                "error": "건강도 체크 실패"
            }
        
        # 2. 상태 분석
        analysis = self.analyze_health_status(health_data)
        
        print(f"\n📊 분석 결과:")
        print(f"  점수: {analysis['score']}/100")
        print(f"  상태: {analysis['status']}")
        print(f"  개입 필요: {analysis['needs_intervention']}")
        print(f"  개입 수준: {analysis['intervention_level']}")
        
        if analysis['reasons']:
            print(f"\n🔍 사유:")
            for reason in analysis['reasons']:
                print(f"  - {reason}")
        
        # 3. 필요시 액션 실행
        action_results: List[Dict[str, Any]] = []
        if analysis['needs_intervention'] and analysis['actions']:
            print(f"\n⚙️  액션 실행 중...")
            action_results = self.execute_actions(analysis['actions'])
            for r in action_results:
                status = "✅" if r.get('success') else "❌"
                print(f"  {status} {r.get('action', 'unknown')}")
        
        # 4. 셀프-검증 (리듬 기반)
        ver_level = self.determine_verification_level(health_data, analysis)
        print(f"\n🧪 셀프-검증 강도: {ver_level}")
        verification_results = self.run_self_verification(ver_level)

        # 5. 자동 시정 조치 (필요 시)
        remediation_notes = self.attempt_auto_remediation(verification_results)

        # 6. 보고서 생성
        report_md = self.generate_supervision_report(health_data, analysis, action_results, ver_level, verification_results, remediation_notes)
        report_file = self.outputs / "meta_supervision_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_md)
        
        # JSON도 저장
        report_json = {
            "timestamp": datetime.now().isoformat(),
            "health_data": health_data,
            "analysis": analysis,
            "action_results": action_results,
            "verification": {
                "level": ver_level,
                "results": verification_results,
                "remediation": remediation_notes,
            }
        }
        report_json_file = self.outputs / "meta_supervision_latest.json"
        with open(report_json_file, 'w', encoding='utf-8') as f:
            json.dump(report_json, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ 보고서 생성: {report_file}")
        
        return {
            "success": True,
            "health_score": analysis['score'],
            "status": analysis['status'],
            "intervention_level": analysis['intervention_level'],
            "actions_taken": len(action_results),
            "report_file": str(report_file)
        }

def main():
    parser = argparse.ArgumentParser(description="메타-감독 시스템")
    parser.add_argument("--workspace", type=str, default=str(Path(__file__).parent.parent),
                        help="작업 공간 경로")
    parser.add_argument("--intervention-threshold", type=int, default=40,
                        help="자동 개입 임계값 (점수)")
    parser.add_argument("--critical-threshold", type=int, default=30,
                        help="긴급 개입 임계값 (점수)")
    parser.add_argument("--no-action", action="store_true",
                        help="액션 실행 없이 분석만 수행")
    parser.add_argument("--test", action="store_true",
                        help="테스트 모드: 간단한 동작 확인")
    
    args = parser.parse_args()
    
    workspace = Path(args.workspace)
    supervisor = MetaSupervisor(workspace)
    supervisor.intervention_threshold = args.intervention_threshold
    supervisor.critical_threshold = args.critical_threshold
    
    if args.test:
        print("🧪 테스트 모드 시작...\n")
        
        # 1. 파이썬 실행 파일 확인
        print(f"✓ Python 실행 파일: {supervisor.python_exe}")
        print(f"  존재: {Path(supervisor.python_exe).exists() if supervisor.python_exe != 'python' else 'system python'}")
        
        # 2. 주요 디렉토리 확인
        print(f"\n✓ 작업 공간: {supervisor.workspace}")
        print(f"  outputs: {supervisor.outputs.exists()}")
        print(f"  scripts: {supervisor.scripts.exists()}")
        print(f"  fdo_agi_repo: {supervisor.fdo_agi_repo.exists()}")
        
        # 3. 건강도 체크 실행
        print(f"\n✓ 건강도 체크 실행 중...")
        health_data = supervisor.run_rhythm_health_check()
        if health_data:
            print(f"  점수: {health_data.get('overall_score', 0)}/100")
            print(f"  상태: {health_data.get('overall_status', 'unknown')}")
        else:
            print(f"  ⚠️  건강도 데이터 없음")
        
        # 4. 분석 테스트
        print(f"\n✓ 분석 엔진 테스트...")
        if health_data:
            analysis = supervisor.analyze_health_status(health_data)
            print(f"  개입 필요: {analysis['needs_intervention']}")
            print(f"  개입 수준: {analysis['intervention_level']}")
            print(f"  액션 수: {len(analysis['actions'])}")
        
        print(f"\n✅ 테스트 완료!")
        sys.exit(0)
    
    if args.no_action:
        print("ℹ️  --no-action 모드: 액션 실행 없이 분석만 수행합니다.\n")
        # 분석만 수행
        health_data = supervisor.run_rhythm_health_check()
        if health_data:
            analysis = supervisor.analyze_health_status(health_data)
            print(f"\n분석 결과: {json.dumps(analysis, indent=2, ensure_ascii=False)}")
    else:
        # 전체 사이클 실행
        result = supervisor.run_supervision_cycle()
        
        # 종료 코드 결정
        if result.get("success"):
            intervention_level = result.get("intervention_level", "none")
            if intervention_level == "critical":
                sys.exit(2)  # 심각
            elif intervention_level == "warning":
                sys.exit(1)  # 경고
            else:
                sys.exit(0)  # 정상
        else:
            sys.exit(3)  # 실패

if __name__ == "__main__":
    main()
