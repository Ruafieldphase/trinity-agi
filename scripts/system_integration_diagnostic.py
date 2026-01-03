#!/usr/bin/env python3
"""
System Integration Diagnostic
시스템 모듈 간 통합 상태를 진단하는 스크립트

각 모듈의 구현 상태와 연결 상태를 체크합니다.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from workspace_root import get_workspace_root

# 프로젝트 루트 설정
workspace_root = get_workspace_root()
sys.path.insert(0, str(workspace_root))
sys.path.insert(0, str(workspace_root / "fdo_agi_repo"))
sys.path.insert(0, str(workspace_root / "scripts"))


class SystemIntegrationDiagnostic:
    """시스템 통합 진단"""
    
    def __init__(self):
        self.workspace = workspace_root
        self.memory_dir = self.workspace / "fdo_agi_repo" / "memory"
        self.outputs = self.workspace / "outputs"
        
        self.report = {
            "timestamp": datetime.now().isoformat(),
            "modules": {},
            "integrations": {},
            "recommendations": []
        }
    
    def check_hippocampus_implementation(self) -> Dict[str, Any]:
        """해마(장기 기억) 구현 상태 체크"""
        print("\n🧠 해마(Hippocampus) 장기 기억 시스템 체크...")
        
        status = {
            "module_exists": False,
            "long_term_memory_class": False,
            "semantic_memory_implemented": False,
            "episodic_memory_implemented": False,
            "procedural_memory_implemented": False,
            "consolidation_active": False,
            "session_memory_db_exists": False
        }
        
        try:
            from copilot.hippocampus import Hippocampus, LongTermMemory
            status["module_exists"] = True
            status["long_term_memory_class"] = True
            
            # 해마 인스턴스 생성
            hippocampus = Hippocampus(self.workspace)
            
            # Semantic memory 구현 체크
            semantic_result = hippocampus.long_term.recall_semantic("test", top_k=1)
            status["semantic_memory_implemented"] = len(semantic_result) > 0 or \
                                                    hasattr(hippocampus.long_term, '_semantic_db')
            
            # Session Memory DB 존재 여부 - Hippocampus가 사용하는 실제 경로 확인
            if hasattr(hippocampus.long_term, 'paths') and 'semantic' in hippocampus.long_term.paths:
                session_db = hippocampus.long_term.paths['semantic']
            else:
                session_db = self.memory_dir / "session_memory.db"
            status["session_memory_db_exists"] = Path(session_db).exists()
            
            # Episodic memory (단기->장기 통합) 체크
            status["episodic_memory_implemented"] = (
                hasattr(hippocampus, 'consolidate') and
                callable(hippocampus.consolidate)
            )
            
            # Procedural memory 체크
            proc_path = self.memory_dir / "procedural_memory.jsonl"
            status["procedural_memory_implemented"] = proc_path.exists()
            
            print(f"  ✓ 모듈 존재: {status['module_exists']}")
            print(f"  {'✓' if status['semantic_memory_implemented'] else '✗'} Semantic Memory 구현: {status['semantic_memory_implemented']}")
            print(f"  {'✓' if status['session_memory_db_exists'] else '✗'} Session DB: {status['session_memory_db_exists']}")
            print(f"  {'✓' if status['episodic_memory_implemented'] else '✗'} Episodic Memory: {status['episodic_memory_implemented']}")
            print(f"  {'✓' if status['procedural_memory_implemented'] else '✗'} Procedural Memory: {status['procedural_memory_implemented']}")
            
        except Exception as e:
            print(f"  ❌ 오류: {e}")
            status["error"] = str(e)
        
        self.report["modules"]["hippocampus"] = status
        return status
    
    def check_quantum_flow_integration(self) -> Dict[str, Any]:
        """Quantum Flow Monitor 통합 상태 체크"""
        print("\n⚡ Quantum Flow Monitor 통합 체크...")
        
        status = {
            "module_exists": False,
            "connected_to_selfcare": False,
            "connected_to_goal_system": False,
            "recent_measurements": 0,
            "flow_state_tracked": False
        }
        
        try:
            from copilot.quantum_flow_monitor import QuantumFlowMonitor
            status["module_exists"] = True
            
            monitor = QuantumFlowMonitor(self.workspace)
            
            # 최근 측정 기록 확인
            flow_log = self.outputs / "quantum_flow_log.jsonl"
            if flow_log.exists():
                with open(flow_log, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    status["recent_measurements"] = len(lines)
                    status["flow_state_tracked"] = len(lines) > 0
            
            # Self-care 통합 확인 (간접적)
            selfcare_summary = self.outputs / "selfcare_summary_latest.json"
            if selfcare_summary.exists():
                with open(selfcare_summary, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # quantum_flow 필드가 있는지 확인
                    status["connected_to_selfcare"] = "quantum_flow" in data or \
                                                      "phase_coherence" in data
            
            # Goal system 통합 확인
            goal_tracker = self.memory_dir / "goal_tracker.json"
            if goal_tracker.exists():
                with open(goal_tracker, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 최근 목표에 flow_state 필드가 있는지
                    status["connected_to_goal_system"] = any(
                        "flow_state" in goal for goal in data.get("goals", [])
                    )
            
            print(f"  ✓ 모듈 존재: {status['module_exists']}")
            print(f"  {'✓' if status['flow_state_tracked'] else '✗'} Flow 상태 추적: {status['recent_measurements']}개 측정")
            print(f"  {'✓' if status['connected_to_selfcare'] else '✗'} Self-care 통합: {status['connected_to_selfcare']}")
            print(f"  {'✓' if status['connected_to_goal_system'] else '✗'} Goal 시스템 통합: {status['connected_to_goal_system']}")
            
        except Exception as e:
            print(f"  ❌ 오류: {e}")
            status["error"] = str(e)
        
        self.report["modules"]["quantum_flow"] = status
        return status
    
    def check_reward_system_integration(self) -> Dict[str, Any]:
        """Reward System (기저핵) 통합 상태 체크"""
        print("\n🎯 Reward System (기저핵) 통합 체크...")
        
        status = {
            "module_exists": False,
            "connected_to_goal_generator": False,
            "connected_to_goal_executor": False,
            "reward_signals_recorded": 0,
            "policy_cache_exists": False,
            "active_learning": False
        }
        
        try:
            from reward_tracker import RewardTracker
            status["module_exists"] = True
            
            tracker = RewardTracker(self.workspace)
            
            # Reward 신호 기록 확인
            if tracker.reward_log.exists():
                with open(tracker.reward_log, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    status["reward_signals_recorded"] = len(lines)
            
            # Policy cache 확인
            status["policy_cache_exists"] = tracker.policy_cache.exists()
            
            # Goal generator 통합 확인
            goal_gen_script = self.workspace / "scripts" / "autonomous_goal_generator.py"
            if goal_gen_script.exists():
                with open(goal_gen_script, 'r', encoding='utf-8') as f:
                    content = f.read()
                    status["connected_to_goal_generator"] = "RewardTracker" in content
            
            # Goal executor 통합 확인
            goal_exec_script = self.workspace / "scripts" / "autonomous_goal_executor.py"
            if goal_exec_script.exists():
                with open(goal_exec_script, 'r', encoding='utf-8') as f:
                    content = f.read()
                    status["connected_to_goal_executor"] = "RewardTracker" in content
            
            # 활성 학습 여부 (최근 24시간 내 보상 신호)
            if status["reward_signals_recorded"] > 0:
                cutoff = datetime.now() - timedelta(hours=24)
                recent_signals = 0
                with open(tracker.reward_log, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            signal = json.loads(line)
                            ts = datetime.fromisoformat(signal["timestamp"])
                            if ts > cutoff:
                                recent_signals += 1
                status["active_learning"] = recent_signals > 0
            
            print(f"  ✓ 모듈 존재: {status['module_exists']}")
            print(f"  {'✓' if status['connected_to_goal_generator'] else '✗'} Goal Generator 연결: {status['connected_to_goal_generator']}")
            print(f"  {'✓' if status['connected_to_goal_executor'] else '✗'} Goal Executor 연결: {status['connected_to_goal_executor']}")
            print(f"  {'✓' if status['reward_signals_recorded'] > 0 else '✗'} Reward 신호: {status['reward_signals_recorded']}개 기록")
            print(f"  {'✓' if status['active_learning'] else '✗'} 활성 학습(24h): {status['active_learning']}")
            
        except Exception as e:
            print(f"  ❌ 오류: {e}")
            status["error"] = str(e)
        
        self.report["modules"]["reward_system"] = status
        return status
    
    def check_meta_supervisor_status(self) -> Dict[str, Any]:
        """Meta Supervisor 상태 체크"""
        print("\n👁️ Meta Supervisor 상태 체크...")
        
        status = {
            "module_exists": False,
            "scheduled": False,
            "recent_execution": None,
            "rhythm_health_integrated": False,
            "auto_intervention_enabled": False
        }
        
        try:
            meta_script = self.workspace / "scripts" / "meta_supervisor.py"
            status["module_exists"] = meta_script.exists()
            
            # 최근 실행 로그 확인
            meta_log = self.outputs / "meta_supervisor_latest.json"
            if meta_log.exists():
                with open(meta_log, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    status["recent_execution"] = data.get("timestamp")
                    status["auto_intervention_enabled"] = data.get("intervention_enabled", False)
            
            # Rhythm health 통합 확인
            rhythm_health = self.outputs / "rhythm_health_latest.json"
            status["rhythm_health_integrated"] = rhythm_health.exists()
            
            print(f"  {'✓' if status['module_exists'] else '✗'} 모듈 존재: {status['module_exists']}")
            print(f"  {'✓' if status['recent_execution'] else '✗'} 최근 실행: {status['recent_execution'] or 'None'}")
            print(f"  {'✓' if status['rhythm_health_integrated'] else '✗'} Rhythm Health 통합: {status['rhythm_health_integrated']}")
            print(f"  {'✓' if status['auto_intervention_enabled'] else '✗'} 자동 개입: {status['auto_intervention_enabled']}")
            
        except Exception as e:
            print(f"  ❌ 오류: {e}")
            status["error"] = str(e)
        
        self.report["modules"]["meta_supervisor"] = status
        return status
    
    def check_integration_loops(self) -> Dict[str, Any]:
        """통합 루프 연결 상태 체크"""
        print("\n🔄 통합 루프 연결 체크...")
        
        loops = {
            "selfcare_to_quantum": False,
            "quantum_to_goals": False,
            "goals_to_reward": False,
            "reward_to_goals": False,
            "hippocampus_to_goals": False,
            "meta_supervisor_active": False
        }
        
        # Self-care → Quantum Flow
        selfcare_script = self.workspace / "scripts" / "generate_selfcare_summary.py"
        if selfcare_script.exists():
            with open(selfcare_script, 'r', encoding='utf-8') as f:
                content = f.read()
                loops["selfcare_to_quantum"] = "quantum_flow" in content.lower()
        
        # Quantum → Goals
        goal_gen = self.workspace / "scripts" / "autonomous_goal_generator.py"
        if goal_gen.exists():
            with open(goal_gen, 'r', encoding='utf-8') as f:
                content = f.read()
                loops["quantum_to_goals"] = "quantum_flow" in content.lower()
        
        # Goals → Reward
        goal_exec = self.workspace / "scripts" / "autonomous_goal_executor.py"
        if goal_exec.exists():
            with open(goal_exec, 'r', encoding='utf-8') as f:
                content = f.read()
                loops["goals_to_reward"] = "reward_tracker" in content.lower()
        
        # Reward → Goals (피드백)
        if goal_gen.exists():
            with open(goal_gen, 'r', encoding='utf-8') as f:
                content = f.read()
                loops["reward_to_goals"] = "reward_tracker" in content.lower()
        
        # Hippocampus → Goals
        if goal_gen.exists():
            with open(goal_gen, 'r', encoding='utf-8') as f:
                content = f.read()
                loops["hippocampus_to_goals"] = "hippocampus" in content.lower()
        
        # Meta Supervisor 활성화
        meta_log = self.outputs / "meta_supervisor_latest.json"
        loops["meta_supervisor_active"] = meta_log.exists()
        
        for loop_name, connected in loops.items():
            status_icon = "✓" if connected else "✗"
            print(f"  {status_icon} {loop_name}: {connected}")
        
        self.report["integrations"] = loops
        return loops
    
    def generate_recommendations(self):
        """개선 권장사항 생성"""
        print("\n💡 개선 권장사항...")
        
        recommendations = []
        
        # Hippocampus 장기 기억
        hippo = self.report["modules"].get("hippocampus", {})
        if not hippo.get("semantic_memory_implemented"):
            recommendations.append({
                "priority": "HIGH",
                "module": "Hippocampus",
                "issue": "Semantic Memory 미구현",
                "action": "store_semantic(), recall_semantic() 메서드를 SQLite FTS5로 구현"
            })
        
        if not hippo.get("session_memory_db_exists"):
            recommendations.append({
                "priority": "HIGH",
                "module": "Hippocampus",
                "issue": "Session Memory DB 부재",
                "action": "session_memory.db 생성 및 초기화"
            })
        
        # Quantum Flow 통합
        quantum = self.report["modules"].get("quantum_flow", {})
        if not quantum.get("connected_to_selfcare"):
            recommendations.append({
                "priority": "MEDIUM",
                "module": "Quantum Flow",
                "issue": "Self-care 시스템과 연결 부족",
                "action": "Self-care 요약에 quantum flow 메트릭 추가"
            })
        
        if not quantum.get("connected_to_goal_system"):
            recommendations.append({
                "priority": "MEDIUM",
                "module": "Quantum Flow",
                "issue": "Goal 시스템과 연결 부족",
                "action": "Goal 생성/실행 시 flow state 반영"
            })
        
        # Reward System
        reward = self.report["modules"].get("reward_system", {})
        if not reward.get("active_learning"):
            recommendations.append({
                "priority": "LOW",
                "module": "Reward System",
                "issue": "최근 보상 신호 없음",
                "action": "Goal 실행 결과를 보상 시스템에 기록"
            })
        
        # Meta Supervisor
        meta = self.report["modules"].get("meta_supervisor", {})
        if not meta.get("recent_execution"):
            recommendations.append({
                "priority": "MEDIUM",
                "module": "Meta Supervisor",
                "issue": "Meta Supervisor 미실행",
                "action": "주기적 실행 스케줄 등록 또는 수동 실행"
            })
        
        # 통합 루프
        loops = self.report.get("integrations", {})
        if not loops.get("selfcare_to_quantum"):
            recommendations.append({
                "priority": "HIGH",
                "module": "Integration",
                "issue": "Self-care → Quantum Flow 루프 미연결",
                "action": "generate_selfcare_summary.py에 quantum flow 측정 추가"
            })
        
        self.report["recommendations"] = recommendations
        
        for rec in recommendations:
            priority_icon = "🔴" if rec["priority"] == "HIGH" else "🟡" if rec["priority"] == "MEDIUM" else "🟢"
            print(f"\n  {priority_icon} [{rec['priority']}] {rec['module']}")
            print(f"     문제: {rec['issue']}")
            print(f"     조치: {rec['action']}")
    
    def save_report(self):
        """진단 리포트 저장"""
        output_file = self.outputs / "system_integration_diagnostic_latest.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📊 진단 리포트 저장: {output_file}")
        
        # Markdown 리포트도 생성
        self._generate_markdown_report()
    
    def _generate_markdown_report(self):
        """Markdown 형식 리포트 생성"""
        md_file = self.outputs / "system_integration_diagnostic_latest.md"
        
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write("# 시스템 통합 진단 리포트\n\n")
            f.write(f"**생성 시각**: {self.report['timestamp']}\n\n")
            
            f.write("## 📊 모듈 상태\n\n")
            
            for module_name, module_status in self.report["modules"].items():
                f.write(f"### {module_name.upper()}\n\n")
                for key, value in module_status.items():
                    if key != "error":
                        icon = "✅" if value else "❌"
                        f.write(f"- {icon} **{key}**: {value}\n")
                if "error" in module_status:
                    f.write(f"\n⚠️ **오류**: {module_status['error']}\n")
                f.write("\n")
            
            f.write("## 🔄 통합 루프 상태\n\n")
            for loop_name, connected in self.report.get("integrations", {}).items():
                icon = "✅" if connected else "❌"
                f.write(f"- {icon} **{loop_name}**: {connected}\n")
            
            f.write("\n## 💡 개선 권장사항\n\n")
            for i, rec in enumerate(self.report.get("recommendations", []), 1):
                priority_icon = "🔴" if rec["priority"] == "HIGH" else "🟡" if rec["priority"] == "MEDIUM" else "🟢"
                f.write(f"\n### {i}. {priority_icon} [{rec['priority']}] {rec['module']}\n\n")
                f.write(f"**문제**: {rec['issue']}\n\n")
                f.write(f"**조치**: {rec['action']}\n\n")
        
        print(f"📄 Markdown 리포트: {md_file}")
    
    def run_full_diagnostic(self):
        """전체 진단 실행"""
        print("=" * 70)
        print("🔍 시스템 통합 진단 시작")
        print("=" * 70)
        
        self.check_hippocampus_implementation()
        self.check_quantum_flow_integration()
        self.check_reward_system_integration()
        self.check_meta_supervisor_status()
        self.check_integration_loops()
        self.generate_recommendations()
        self.save_report()
        
        print("\n" + "=" * 70)
        print("✅ 진단 완료")
        print("=" * 70)


def main():
    diagnostic = SystemIntegrationDiagnostic()
    diagnostic.run_full_diagnostic()


if __name__ == "__main__":
    main()
