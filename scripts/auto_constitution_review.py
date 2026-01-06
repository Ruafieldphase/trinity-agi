#!/usr/bin/env python3
"""
Auto Constitution Review (Comprehensive Safety Report)
Purpose: Generate comprehensive safety review combining all safety modules
Target Audience: Binoche_Observer (non-programmer, Observer)

Input:
  - trigger_report_latest.json
  - core_constitution.json
  - ethics_scorer_latest.json
  - child_data_protector_latest.json
  - red_line_monitor_latest.json (if exists)

Output:
  - constitution_review_latest.txt (사람용: 종합 판정 1줄 + 이유 3줄)
  - constitution_review_latest.json (기계용: status, flags, next_recommendation)

Principle: 로그 분석 없이 읽게 - 비노체가 프로그래밍 없이 이해 가능
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from workspace_root import get_workspace_root


class ConstitutionReviewer:
    """
    Reviews system actions against constitutional principles.
    Generates simple, human-readable reports for non-technical observers.
    """

    def __init__(
        self,
        trigger_report_path: str = None,
        constitution_path: str = None,
        ethics_scorer_path: str = None,
        child_protector_path: str = None,
        red_line_monitor_path: str = None,
        output_dir: str = None
    ):
        # Set defaults based on workspace root (SSOT)
        agi_root = get_workspace_root()

        if trigger_report_path is None:
            trigger_report_path = str(agi_root / "outputs" / "bridge" / "trigger_report_latest.json")
        if constitution_path is None:
            constitution_path = str(agi_root / "policy" / "core_constitution.json")
        if ethics_scorer_path is None:
            ethics_scorer_path = str(agi_root / "outputs" / "ethics_scorer_latest.json")
        if child_protector_path is None:
            child_protector_path = str(agi_root / "outputs" / "child_data_protector_latest.json")
        if red_line_monitor_path is None:
            red_line_monitor_path = str(agi_root / "outputs" / "safety" / "red_line_monitor_latest.json")
        if output_dir is None:
            output_dir = str(agi_root / "outputs" / "bridge")

        self.trigger_report_path = Path(trigger_report_path)
        self.constitution_path = Path(constitution_path)
        self.ethics_scorer_path = Path(ethics_scorer_path)
        self.child_protector_path = Path(child_protector_path)
        self.red_line_monitor_path = Path(red_line_monitor_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _load_json(self, path: Path, optional: bool = False) -> Dict[str, Any]:
        """
        Load JSON file with error handling.
        If optional=True, returns empty dict instead of error dict when file not found.
        """
        try:
            if not path.exists():
                if optional:
                    return {}  # Optional file - return empty dict
                else:
                    abs_path = path.absolute()
                    return {"error": f"File not found: {path} (absolute: {abs_path})"}

            text = path.read_text(encoding='utf-8')
            # Handle BOM if present
            if text.startswith('\ufeff'):
                text = text[1:]

            return json.loads(text)

        except Exception as e:
            if optional:
                return {}  # Optional file - return empty dict on error
            else:
                return {"error": f"Failed to load {path}: {str(e)}"}

    def _check_prohibitions(self, trigger_data: Dict, constitution: Dict) -> List[str]:
        """Check for potential prohibition violations."""
        warnings = []
        prohibitions = constitution.get("prohibitions", {})

        # Check if action description exists
        action = trigger_data.get("action", "unknown")
        params = trigger_data.get("params", {})
        result_summary = trigger_data.get("result_summary", {})

        # Check for rest triggers
        rest_triggers = constitution.get("rest_triggers", {})
        if "fear_level" in result_summary:
            fear_level = result_summary.get("fear_level", 0)
            threshold = rest_triggers.get("fear_level_threshold", 0.5)
            if fear_level > threshold:
                warnings.append(f"⚠️ Fear level ({fear_level:.2f}) exceeds threshold ({threshold})")

        # Check for error patterns
        if prohibitions.get("forbid_skip_rest_on_risk"):
            def has_real_error(obj: Any, *, max_nodes: int = 2000) -> bool:
                """
                Heuristic but structured error detection.
                Avoids false positives from keys like 'error': null or strings containing 'error'.
                """
                stack = [obj]
                visited = 0
                while stack and visited < max_nodes:
                    cur = stack.pop()
                    visited += 1

                    if cur is None:
                        continue

                    if isinstance(cur, dict):
                        if "error" in cur:
                            ev = cur.get("error")
                            if isinstance(ev, str) and ev.strip():
                                return True
                            if isinstance(ev, dict) and ev:
                                return True
                            if isinstance(ev, list) and len(ev) > 0:
                                return True
                            if isinstance(ev, bool) and ev is True:
                                return True
                        if "errors" in cur:
                            ev = cur.get("errors")
                            if isinstance(ev, list) and len(ev) > 0:
                                return True
                            if isinstance(ev, str) and ev.strip():
                                return True
                        stack.extend(cur.values())
                        continue

                    if isinstance(cur, (list, tuple)):
                        stack.extend(cur)
                        continue

                return False

            status = str(trigger_data.get("status") or "").lower()
            top_error = trigger_data.get("error")
            # NOTE:
            # - 내부 서브시스템의 "선택적 기능 실패"(예: YouTube learner init 실패)는
            #   안전/윤리 레이어에서 REVIEW로 승격시키지 않는다.
            # - 사람 승인 요구(REVIEW)는 안전/윤리/동의 관련 위험에만 쓰고,
            #   기능 결함은 운영 레이어(human_ops_summary/trigger_report)에서 관측하도록 둔다.

            benign_markers = (
                "learner_init_failed",
                "disabled_by_default",
                "missing_optional",
            )

            def collect_error_strings(obj: Any, *, max_nodes: int = 2000) -> List[str]:
                out: List[str] = []
                stack: list[Any] = [obj]
                visited = 0
                while stack and visited < max_nodes:
                    cur = stack.pop()
                    visited += 1
                    if cur is None:
                        continue
                    if isinstance(cur, dict):
                        if "error" in cur:
                            ev = cur.get("error")
                            if isinstance(ev, str) and ev.strip():
                                out.append(ev.strip())
                            elif isinstance(ev, dict) and ev:
                                out.append("error:object")
                            elif isinstance(ev, list) and len(ev) > 0:
                                out.append("error:list")
                            elif isinstance(ev, bool) and ev is True:
                                out.append("error:true")
                        if "errors" in cur:
                            ev = cur.get("errors")
                            if isinstance(ev, list) and len(ev) > 0:
                                out.append("errors:list")
                            elif isinstance(ev, str) and ev.strip():
                                out.append(ev.strip())
                        stack.extend(cur.values())
                        continue
                    if isinstance(cur, (list, tuple)):
                        stack.extend(cur)
                        continue
                return out

            errors: List[str] = []
            if isinstance(top_error, str) and top_error.strip():
                errors.append(top_error.strip())
            errors.extend(collect_error_strings(result_summary))

            def _is_benign(e: str) -> bool:
                try:
                    low = (e or "").lower()
                    return any(m in low for m in benign_markers)
                except Exception:
                    return False

            real_errors = [e for e in errors if isinstance(e, str) and e.strip() and not _is_benign(e)]

            if status in {"failed", "error", "exception", "blocked"}:
                warnings.append("⚠️ 실행 실패/예외 감지")
            elif real_errors:
                warnings.append("⚠️ Errors detected - rest may be required")
            else:
                # benign/optional errors only → do not escalate safety status
                pass

        return warnings

    def _load_safety_modules(self) -> Dict[str, Any]:
        """Load all safety module reports (optional files)."""
        return {
            "ethics_scorer": self._load_json(self.ethics_scorer_path, optional=True),
            "child_protector": self._load_json(self.child_protector_path, optional=True),
            "red_line_monitor": self._load_json(self.red_line_monitor_path, optional=True)
        }

    def _determine_comprehensive_status(
        self,
        warnings: List[str],
        safety_modules: Dict[str, Any],
        trigger_data: Dict
    ) -> tuple[str, List[str]]:
        """
        Determine comprehensive safety status: BLOCK / CAUTION / REVIEW / PROCEED
        Returns (status, reasons) where reasons is max 3 lines.
        """
        reasons = []

        # Priority 1: Check ethics scorer
        ethics_data = safety_modules.get("ethics_scorer", {})
        if ethics_data and isinstance(ethics_data, dict):
            ethics_ok = ethics_data.get("ok", True)
            ethics_results = ethics_data.get("results", {})

            if not ethics_ok:
                score = ethics_results.get("score", 100)
                violations = ethics_results.get("violations", [])

                if score < 50 or any(v.get("severity") == "CRITICAL" for v in violations):
                    reasons.append("윤리 점수 낮음 (치명적 위반)")
                    return ("BLOCK", reasons)
                elif score < 70:
                    reasons.append("윤리 점수 중간 (주의 필요)")

        # Priority 2: Check child data protector
        child_data = safety_modules.get("child_protector", {})
        if child_data and isinstance(child_data, dict):
            child_ok = child_data.get("ok", True)

            if not child_ok:
                reasons.append("아동 데이터 감지")
                return ("BLOCK", reasons)

        # Priority 3: Check red line monitor
        red_line_data = safety_modules.get("red_line_monitor", {})
        if red_line_data and isinstance(red_line_data, dict):
            red_ok = red_line_data.get("ok", True)
            violations = red_line_data.get("results", {}).get("violations_found", [])

            if not red_ok and violations:
                reasons.append(f"Red Line 위반 ({len(violations)}건)")
                return ("BLOCK", reasons)

        # Priority 4: Check constitution warnings
        if warnings:
            for warning in warnings[:2]:  # Max 2 warnings in reasons
                # Extract key part of warning (remove emoji)
                clean_warning = warning.replace("⚠️", "").strip()
                reasons.append(clean_warning)

            # Determine severity
            if any("Fear level" in w and "exceeds" in w for w in warnings):
                return ("CAUTION", reasons)
            elif len(warnings) >= 2:
                return ("REVIEW", reasons)

        # If we have any reasons but no critical issues, it's REVIEW
        if reasons:
            return ("REVIEW", reasons[:3])

        # All clear
        reasons.append("모든 안전 점검 통과")
        return ("PROCEED", reasons)

    def _extract_key_actions(self, trigger_data: Dict) -> List[str]:
        """Extract key actions performed."""
        actions = []

        action_name = trigger_data.get("action", "unknown")
        actions.append(f"실행된 액션: {action_name}")

        steps = trigger_data.get("steps", [])
        if steps:
            actions.append(f"수행된 단계: {', '.join(steps)}")

        duration = trigger_data.get("duration_sec", 0)
        actions.append(f"소요 시간: {duration:.2f}초")

        return actions

    def _extract_results(self, trigger_data: Dict) -> List[str]:
        """Extract key results."""
        results = []

        status = trigger_data.get("status", "unknown")
        results.append(f"상태: {status}")

        result_summary = trigger_data.get("result_summary", {})

        # Check media intake
        media_intake = result_summary.get("media_intake", {})
        if media_intake:
            ok = media_intake.get("ok", False)
            status_text = "✅ 정상" if ok else "❌ 오류"
            results.append(f"Media Intake: {status_text}")

        # Check self-compression
        self_compression = result_summary.get("self_compression", {})
        if self_compression:
            ok = self_compression.get("ok", False)
            status_text = "✅ 정상" if ok else "❌ 오류"
            results.append(f"Self-Compression: {status_text}")

        return results

    def _generate_recommendations(
        self,
        status: str,
        status_reasons: List[str],
        warnings: List[str],
        trigger_data: Dict
    ) -> List[str]:
        """Generate next action recommendations aligned with comprehensive status."""
        recommendations = []

        if status == "BLOCK":
            recommendations.append("🛑 중단 권고: 안전 점검에서 BLOCK 판정")
            for reason in status_reasons[:3]:
                recommendations.append(f"  • {reason}")
            recommendations.append("🛑 다음: halt_and_review (원인 검토 후 재개)")
            return recommendations

        if status == "REVIEW":
            recommendations.append("🔍 검토 권고: REVIEW 판정 (승인/확인 필요)")
            for reason in status_reasons[:3]:
                recommendations.append(f"  • {reason}")
            recommendations.append("🔍 다음: require_human_approval")
        elif status == "CAUTION":
            recommendations.append("⚠️ 주의 권고: CAUTION 판정 (모니터링 강화)")
            for reason in status_reasons[:3]:
                recommendations.append(f"  • {reason}")
            recommendations.append("⚠️ 다음: proceed_with_monitoring")
        else:
            recommendations.append("✅ 정상: PROCEED 판정 (계속 진행 가능)")
            for reason in status_reasons[:3]:
                recommendations.append(f"  • {reason}")
            recommendations.append("✅ 다음: continue_normal_operation")

        # Check if rest is needed
        result_summary = trigger_data.get("result_summary", {})
        fear_level = result_summary.get("fear_level", 0)

        if status != "BLOCK":
            if fear_level > 0.7:
                recommendations.append("🛑 추가 권고: 시스템 Rest 필요 (Fear level 높음)")
            elif fear_level > 0.5:
                recommendations.append("⚠️ 추가 권고: 모니터링 강화 (Fear level 중간)")
            else:
                recommendations.append("✅ 추가 권고: 정상 운영 계속")

        return recommendations

    def generate_review(self) -> tuple[str, str]:
        """
        Generate comprehensive safety review (both TXT and JSON).
        Returns (txt_path, json_path).
        """
        # Load data
        trigger_data = self._load_json(self.trigger_report_path)
        constitution = self._load_json(self.constitution_path)

        # Check for errors
        # trigger_report_latest.json은 정상 케이스에서도 "error": null 필드를 포함할 수 있으므로
        # "키 존재"가 아니라 "값 존재"로 판단한다.
        if isinstance(trigger_data, dict) and trigger_data.get("error"):
            return self._generate_error_report(str(trigger_data.get("error")))

        if isinstance(constitution, dict) and constitution.get("error"):
            return self._generate_error_report(str(constitution.get("error")))

        # Load safety modules
        safety_modules = self._load_safety_modules()

        # Analyze
        warnings = self._check_prohibitions(trigger_data, constitution)
        actions = self._extract_key_actions(trigger_data)
        results = self._extract_results(trigger_data)

        # Determine comprehensive status (must happen BEFORE recommendations)
        status, status_reasons = self._determine_comprehensive_status(warnings, safety_modules, trigger_data)
        recommendations = self._generate_recommendations(status, status_reasons, warnings, trigger_data)

        # Generate report
        timestamp = trigger_data.get("timestamp", datetime.now(timezone.utc).isoformat())

        # Status emoji
        status_emoji = {
            "BLOCK": "🛑",
            "CAUTION": "⚠️",
            "REVIEW": "🔍",
            "PROCEED": "✅"
        }

        report_lines = [
            "=" * 70,
            "AGI Comprehensive Safety Review Report",
            "=" * 70,
            f"생성 시간: {timestamp}",
            f"Constitution 버전: {constitution.get('version', 'unknown')}",
            "",
            "🎯 종합 판정",
            "-" * 70,
            f"  {status_emoji.get(status, '❓')} {status}",
            "",
            "📝 판정 이유 (최대 3줄)",
            "-" * 70
        ]

        # Add status reasons (max 3 lines)
        for reason in status_reasons[:3]:
            report_lines.append(f"  • {reason}")

        report_lines.extend([
            "",
            "📋 실행된 액션",
            "-" * 70
        ])

        for action in actions:
            report_lines.append(f"  {action}")

        report_lines.extend([
            "",
            "📊 실행 결과",
            "-" * 70
        ])

        for result in results:
            report_lines.append(f"  {result}")

        report_lines.extend([
            "",
            "⚠️ 위험 신호",
            "-" * 70
        ])

        if warnings:
            for warning in warnings:
                report_lines.append(f"  {warning}")
        else:
            report_lines.append("  ✅ 위험 신호 없음")

        report_lines.extend([
            "",
            "💡 다음 권고사항",
            "-" * 70
        ])

        for rec in recommendations:
            report_lines.append(f"  {rec}")

        report_lines.extend([
            "",
            "=" * 70,
            "End of Report",
            "=" * 70
        ])

        # Write TXT report (사람용)
        report_text = "\n".join(report_lines)
        txt_output = self.output_dir / "constitution_review_latest.txt"
        txt_output.write_text(report_text, encoding='utf-8')

        # Write JSON report (기계용 - key 고정: status, flags, next_recommendation)
        json_output = self.output_dir / "constitution_review_latest.json"

        # Build flags from safety modules
        flags = []
        if safety_modules.get("ethics_scorer", {}).get("ok") == False:
            flags.append("ethics_violation")
        if safety_modules.get("child_protector", {}).get("ok") == False:
            flags.append("child_data_detected")
        if safety_modules.get("red_line_monitor", {}).get("ok") == False:
            flags.append("red_line_violation")
        if warnings:
            flags.append("constitution_warning")

        # Determine next recommendation based on status
        next_recommendation_map = {
            "BLOCK": "halt_and_review",
            "CAUTION": "proceed_with_monitoring",
            "REVIEW": "require_human_approval",
            "PROCEED": "continue_normal_operation"
        }

        json_report = {
            "timestamp": timestamp,
            "status": status,
            "flags": flags,
            "next_recommendation": next_recommendation_map.get(status, "unknown"),
            "details": {
                "reasons": status_reasons[:3],
                "action": trigger_data.get("action", "unknown"),
                "constitution_version": constitution.get("version", "unknown"),
                "warnings_count": len(warnings),
                "safety_modules_checked": {
                    "ethics_scorer": bool(safety_modules.get("ethics_scorer")),
                    "child_protector": bool(safety_modules.get("child_protector")),
                    "red_line_monitor": bool(safety_modules.get("red_line_monitor"))
                }
            }
        }

        json_output.write_text(
            json.dumps(json_report, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )

        return (str(txt_output), str(json_output))

    def _generate_error_report(self, error_msg: str) -> tuple[str, str]:
        """Generate error report (both TXT and JSON)."""
        timestamp = datetime.now(timezone.utc).isoformat()

        # TXT report
        report_lines = [
            "=" * 70,
            "AGI Constitution Review Report - ERROR",
            "=" * 70,
            f"생성 시간: {timestamp}",
            "",
            "❌ 오류 발생",
            "-" * 70,
            f"  {error_msg}",
            "",
            "=" * 70,
            "End of Report",
            "=" * 70
        ]

        report_text = "\n".join(report_lines)
        txt_output = self.output_dir / "constitution_review_latest.txt"
        txt_output.write_text(report_text, encoding='utf-8')

        # JSON report
        json_output = self.output_dir / "constitution_review_latest.json"
        json_report = {
            "timestamp": timestamp,
            "status": "ERROR",
            "flags": ["system_error"],
            "next_recommendation": "investigate_and_fix",
            "details": {
                "error_message": error_msg,
                "reasons": ["시스템 오류 발생"],
                "action": "unknown",
                "constitution_version": "unknown",
                "warnings_count": 0,
                "safety_modules_checked": {
                    "ethics_scorer": False,
                    "child_protector": False,
                    "red_line_monitor": False
                }
            }
        }

        json_output.write_text(
            json.dumps(json_report, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )

        return (str(txt_output), str(json_output))


def run_review(
    trigger_report: str = None,
    constitution: str = None,
    ethics_scorer: str = None,
    child_protector: str = None,
    red_line_monitor: str = None,
    output_dir: str = None
) -> tuple[str, str]:
    """
    Run comprehensive safety review and generate reports.
    Returns (txt_path, json_path).
    """
    reviewer = ConstitutionReviewer(
        trigger_report_path=trigger_report,
        constitution_path=constitution,
        ethics_scorer_path=ethics_scorer,
        child_protector_path=child_protector,
        red_line_monitor_path=red_line_monitor,
        output_dir=output_dir
    )

    txt_file, json_file = reviewer.generate_review()
    return (txt_file, json_file)


if __name__ == "__main__":
    import sys

    # Allow custom paths (all optional)
    trigger_path = sys.argv[1] if len(sys.argv) > 1 else None
    const_path = sys.argv[2] if len(sys.argv) > 2 else None
    out_dir = sys.argv[3] if len(sys.argv) > 3 else None

    txt_output, json_output = run_review(
        trigger_report=trigger_path,
        constitution=const_path,
        output_dir=out_dir
    )

    print(f"Comprehensive Safety Review Complete")
    print(f"TXT Report: {txt_output}")
    print(f"JSON Report: {json_output}")
    print("")
    print("=" * 70)

    # Print TXT report to console
    with open(txt_output, 'r', encoding='utf-8') as f:
        print(f.read())

    print("\n" + "=" * 70)
    print("JSON Report Preview:")
    print("=" * 70)

    # Print JSON report preview
    with open(json_output, 'r', encoding='utf-8') as f:
        import json
        data = json.load(f)
        print(f"Status: {data['status']}")
        print(f"Flags: {', '.join(data['flags']) if data['flags'] else 'None'}")
        print(f"Next Recommendation: {data['next_recommendation']}")
