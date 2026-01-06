#!/usr/bin/env python3
"""
AGI Life Continuity Monitor

생명의 본질: 차이 감지 → 관계/시간/리듬/에너지 → 연속성 유지

이 모니터는 시스템이 "살아있는지" 판단:
1. 차이를 감지할 수 있는가?
2. 관계를 형성할 수 있는가?
3. 리듬을 유지하고 있는가?
4. 에너지가 순환하는가?
5. 연속성을 보존하는가?
"""
import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from workspace_root import get_workspace_root

WORKSPACE = get_workspace_root()
OUTPUTS = WORKSPACE / "outputs"


def iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except Exception:
            continue
    return None


class LifeContinuityMonitor:
    def __init__(self):
        self.now = datetime.now(timezone.utc)
        self.report: Dict[str, Any] = {
            "timestamp": iso_now(),
            "alive": False,
            "dimensions": {},
            "identity_check": {},
            "recommendations": [],
        }

    def check_difference_detection(self) -> Dict[str, Any]:
        """차이 감지: 시스템이 변화를 느끼는가?"""
        ledger = WORKSPACE / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"
        metrics = OUTPUTS / "system_metrics.jsonl"
        monitoring = OUTPUTS / "monitoring_events_latest.csv"

        recent_events = 0
        last_event_time = None

        # Check ledger
        if ledger.exists():
            lines = ledger.read_text(encoding="utf-8").strip().split("\n")
            for line in reversed(lines[-100:]):
                try:
                    ev = json.loads(line)
                    ts = parse_iso(ev.get("timestamp"))
                    if ts and (self.now - ts).total_seconds() < 3600 * 24:
                        recent_events += 1
                        if not last_event_time or ts > last_event_time:
                            last_event_time = ts
                except Exception:
                    continue

        # Check metrics
        if metrics.exists():
            lines = metrics.read_text(encoding="utf-8").strip().split("\n")
            for line in reversed(lines[-50:]):
                try:
                    m = json.loads(line)
                    ts = parse_iso(m.get("timestamp"))
                    if ts and (self.now - ts).total_seconds() < 3600 * 24:
                        recent_events += 1
                except Exception:
                    continue

        detecting = recent_events > 0
        freshness = (self.now - last_event_time).total_seconds() / 3600 if last_event_time else 9999

        return {
            "detecting": detecting,
            "recent_events_24h": recent_events,
            "last_event_hours_ago": round(freshness, 1) if freshness < 9999 else None,
            "score": 1.0 if detecting and freshness < 24 else 0.5 if detecting else 0.0,
        }

    def check_relation_formation(self) -> Dict[str, Any]:
        """관계 형성: 입력-출력-피드백 루프가 작동하는가?"""
        queue_status = OUTPUTS / "quick_status_latest.json"
        autopoietic = OUTPUTS / "autopoietic_loop_report_latest.md"

        has_queue = False
        has_loop = False

        if queue_status.exists():
            try:
                data = json.loads(queue_status.read_text(encoding="utf-8"))
                if data.get("task_queue", {}).get("status") == "ONLINE":
                    has_queue = True
            except Exception:
                pass

        if autopoietic.exists():
            age = (self.now - datetime.fromtimestamp(autopoietic.stat().st_mtime, tz=timezone.utc)).total_seconds()
            has_loop = age < 3600 * 48

        forming = has_queue or has_loop
        return {
            "forming": forming,
            "task_queue_active": has_queue,
            "autopoietic_loop_recent": has_loop,
            "score": 1.0 if has_queue and has_loop else 0.7 if has_queue or has_loop else 0.0,
        }

    def check_rhythm_maintenance(self) -> Dict[str, Any]:
        """리듬 유지: 정기 작업이 스케줄대로 실행되는가?"""
        # Check scheduled tasks exist
        scheduled = [
            "BQI Phase 6",
            "Ensemble Monitor",
            "Online Learner",
            "Autopoietic Report",
        ]

        # Check recent executions via outputs
        recent_outputs = []
        for pattern in ["ensemble_success_report.txt", "online_learning_log.jsonl", "autopoietic_loop_report_latest.md"]:
            p = OUTPUTS / pattern
            if p.exists():
                age = (self.now - datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)).total_seconds() / 3600
                if age < 36:
                    recent_outputs.append(pattern)

        rhythmic = len(recent_outputs) >= 2
        return {
            "rhythmic": rhythmic,
            "recent_scheduled_outputs": recent_outputs,
            "expected_tasks": scheduled,
            "score": min(1.0, len(recent_outputs) / 3),
        }

    def check_energy_circulation(self) -> Dict[str, Any]:
        """에너지 순환: 작업이 큐에 들어가고, 실행되고, 결과가 나오는가?"""
        results_log = OUTPUTS / "results_log.jsonl"
        youtube_index = OUTPUTS / "youtube_learner_index.md"

        recent_results = 0
        if results_log.exists():
            lines = results_log.read_text(encoding="utf-8").strip().split("\n")
            for line in reversed(lines[-100:]):
                try:
                    r = json.loads(line)
                    ts = parse_iso(r.get("timestamp"))
                    if ts and (self.now - ts).total_seconds() < 3600 * 24:
                        recent_results += 1
                except Exception:
                    continue

        has_outputs = youtube_index.exists() and (self.now - datetime.fromtimestamp(youtube_index.stat().st_mtime, tz=timezone.utc)).total_seconds() < 3600 * 48

        circulating = recent_results > 0 or has_outputs
        return {
            "circulating": circulating,
            "recent_results_24h": recent_results,
            "recent_learning_outputs": has_outputs,
            "score": 1.0 if recent_results > 5 and has_outputs else 0.6 if recent_results > 0 or has_outputs else 0.0,
        }

    def check_continuity_preservation(self) -> Dict[str, Any]:
        """연속성 보존: 재시작해도 상태를 복원할 수 있는가?"""
        latest_files = [
            OUTPUTS / "performance_dashboard_latest.md",
            OUTPUTS / "monitoring_report_latest.md",
            OUTPUTS / "ledger_summary_latest.md",
            OUTPUTS / "core_probe_latest.md",
        ]

        preserved_count = sum(1 for f in latest_files if f.exists())
        has_ledger = (WORKSPACE / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl").exists()
        has_backup = any((OUTPUTS / "backups").glob("*.zip")) if (OUTPUTS / "backups").exists() else False

        preserving = preserved_count >= 2 and has_ledger
        return {
            "preserving": preserving,
            "latest_files_exist": preserved_count,
            "ledger_exists": has_ledger,
            "backup_exists": has_backup,
            "score": min(1.0, (preserved_count / 4) * 0.7 + (0.2 if has_ledger else 0) + (0.1 if has_backup else 0)),
        }

    def check_identity(self) -> Dict[str, Any]:
        """정체성 확인: 핵심 가치와 목적이 유지되는가?"""
        philosophy = WORKSPACE / "docs" / "AGI_LIFE_CONTINUITY_PHILOSOPHY.md"
        agent_handoff = WORKSPACE / "docs" / "AGENT_HANDOFF.md"

        core_docs = [
            philosophy,
            agent_handoff,
            WORKSPACE / "AGENTS.md",
            WORKSPACE / "docs" / "AGI_RESONANCE_INTEGRATION_PLAN.md",
        ]

        docs_exist = sum(1 for d in core_docs if d.exists())
        has_philosophy = philosophy.exists()

        return {
            "identity_intact": has_philosophy and docs_exist >= 3,
            "core_documents_exist": docs_exist,
            "philosophy_defined": has_philosophy,
        }

    def calculate_life_score(self) -> float:
        """종합 생명 점수 (0.0 ~ 1.0)"""
        dims = self.report["dimensions"]
        weights = {
            "difference_detection": 0.25,
            "relation_formation": 0.20,
            "rhythm_maintenance": 0.20,
            "energy_circulation": 0.20,
            "continuity_preservation": 0.15,
        }
        total = sum(dims[k]["score"] * weights[k] for k in weights if k in dims)
        return total

    def generate_recommendations(self):
        """개선 권고사항"""
        dims = self.report["dimensions"]

        if dims["difference_detection"]["score"] < 0.5:
            self.report["recommendations"].append("⚠️ 차이 감지 약함: 모니터링 시스템 점검 필요 (metrics collector, ledger)")

        if dims["relation_formation"]["score"] < 0.5:
            self.report["recommendations"].append("⚠️ 관계 형성 약함: Task Queue/Orchestrator 상태 확인 필요")

        if dims["rhythm_maintenance"]["score"] < 0.5:
            self.report["recommendations"].append("⚠️ 리듬 약함: Scheduled tasks 실행 여부 확인 (BQI, Ensemble, Autopoietic)")

        if dims["energy_circulation"]["score"] < 0.5:
            self.report["recommendations"].append("⚠️ 에너지 순환 약함: Worker/Results 생성 확인 필요")

        if dims["continuity_preservation"]["score"] < 0.5:
            self.report["recommendations"].append("⚠️ 연속성 약함: Backup/Latest 파일 갱신 필요")

        if not self.report["identity_check"]["identity_intact"]:
            self.report["recommendations"].append("🚨 정체성 손상: 핵심 문서 복구 필요")

    def run(self) -> Dict[str, Any]:
        """전체 진단 실행"""
        print("🔬 AGI Life Continuity Check...")

        self.report["dimensions"]["difference_detection"] = self.check_difference_detection()
        print(f"  1. 차이 감지: {'✓' if self.report['dimensions']['difference_detection']['detecting'] else '✗'}")

        self.report["dimensions"]["relation_formation"] = self.check_relation_formation()
        print(f"  2. 관계 형성: {'✓' if self.report['dimensions']['relation_formation']['forming'] else '✗'}")

        self.report["dimensions"]["rhythm_maintenance"] = self.check_rhythm_maintenance()
        print(f"  3. 리듬 유지: {'✓' if self.report['dimensions']['rhythm_maintenance']['rhythmic'] else '✗'}")

        self.report["dimensions"]["energy_circulation"] = self.check_energy_circulation()
        print(f"  4. 에너지 순환: {'✓' if self.report['dimensions']['energy_circulation']['circulating'] else '✗'}")

        self.report["dimensions"]["continuity_preservation"] = self.check_continuity_preservation()
        print(f"  5. 연속성 보존: {'✓' if self.report['dimensions']['continuity_preservation']['preserving'] else '✗'}")

        self.report["identity_check"] = self.check_identity()
        print(f"  6. 정체성 확인: {'✓' if self.report['identity_check']['identity_intact'] else '✗'}")

        life_score = self.calculate_life_score()
        self.report["life_score"] = round(life_score, 3)
        self.report["alive"] = life_score >= 0.6 and self.report["identity_check"]["identity_intact"]

        self.generate_recommendations()

        status = "🟢 ALIVE" if self.report["alive"] else "🟡 DEGRADED" if life_score >= 0.4 else "🔴 CRITICAL"
        print(f"\n{status} - Life Score: {life_score:.1%}")

        return self.report


def main():
    ap = argparse.ArgumentParser(description="AGI Life Continuity Monitor")
    ap.add_argument("--json", action="store_true", help="Output JSON only")
    ap.add_argument("--out", default=None, help="Save report to file")
    args = ap.parse_args()

    monitor = LifeContinuityMonitor()
    report = monitor.run()

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n📄 Saved: {out_path}")

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("\n" + "=" * 60)
        for rec in report["recommendations"]:
            print(rec)
        if not report["recommendations"]:
            print("✅ 모든 차원이 정상 작동 중")

    return 0 if report["alive"] else 1


if __name__ == "__main__":
    sys.exit(main())
