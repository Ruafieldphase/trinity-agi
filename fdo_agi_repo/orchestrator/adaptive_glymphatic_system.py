"""
Adaptive Glymphatic System
통합 적응형 시스템
"""
from typing import Dict
import time
from datetime import datetime
from .workload_monitor import WorkloadMonitor
from .fatigue_detector import FatigueDetector
from .adaptive_glymphatic_scheduler import AdaptiveGlymphaticScheduler
from .rhythm_aware_glymphatic import RhythmAwareGlymphaticSystem
from .metrics_logger import JsonlEventLogger


class AdaptiveGlymphaticSystem:
    """적응형 Glymphatic 시스템"""
    
    def __init__(self):
        self.workload = WorkloadMonitor()
        self.fatigue = FatigueDetector()
        self.scheduler = AdaptiveGlymphaticScheduler()
        self.rhythm = RhythmAwareGlymphaticSystem()
        self.logger = JsonlEventLogger(
            path="fdo_agi_repo/memory/glymphatic_ledger.jsonl",
            component="glymphatic",
        )
        
    def monitor_and_decide(self) -> Dict:
        """모니터링 및 청소 결정"""
        
        # 1. 현재 상태 측정
        workload_data = self.workload.measure()
        fatigue_data = self.fatigue.get_status()
        
        # 2. 리듬 기반 조정
        rhythm_adjustment = self.rhythm.adjust_cleanup_urgency(
            base_fatigue=fatigue_data["fatigue_level"],
            workload=workload_data["workload_percent"]
        )
        
        # 3. 최적 시간 계산 (조정된 피로도 사용)
        decision = self.scheduler.find_optimal_time(
            workload=workload_data["workload_percent"],
            fatigue=rhythm_adjustment["adjusted_fatigue"]
        )
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "workload": workload_data,
            "fatigue": fatigue_data,
            "rhythm_adjustment": rhythm_adjustment,
            "decision": decision,
            "should_cleanup": decision["action"] == "cleanup_now"
        }

        # 4. 운영 텔레메트리 기록
        try:
            self.logger.log(
                "decision",
                {
                    "workload_percent": workload_data.get("workload_percent"),
                    "cpu_percent": workload_data.get("cpu_percent"),
                    "memory_percent": workload_data.get("memory_percent"),
                    "fatigue_level": fatigue_data.get("fatigue_level"),
                    "fatigue_status": fatigue_data.get("status"),
                    "adjusted_fatigue": rhythm_adjustment.get("adjusted_fatigue"),
                    "rhythm_phase": rhythm_adjustment.get("rhythm_phase"),
                    "rhythm_health": rhythm_adjustment.get("rhythm_health"),
                    "decision_action": decision.get("action"),
                    "decision_reason": decision.get("reason"),
                    "decision_delay_minutes": decision.get("delay_minutes"),
                    "decision_confidence": decision.get("confidence"),
                    "should_cleanup": result["should_cleanup"],
                },
            )
        except Exception:
            pass

        # 5. 결과 반환
        return result
    
    def run_cleanup(self) -> Dict:
        """청소 실행"""
        print("🌊 Glymphatic 청소 시작...")
        start = time.time()

        # 현재 컨텍스트 스냅샷 기록
        try:
            current_workload = self.workload.measure()
            current_fatigue = self.fatigue.get_status()
        except Exception:
            current_workload = {"workload_percent": None}
            current_fatigue = {"fatigue_level": None}

        # 이벤트: cleanup_start
        try:
            self.logger.log(
                "cleanup_start",
                {
                    "workload_percent": current_workload.get("workload_percent"),
<<<<<<< HEAD
                    "fatigue_level": current_fatigue.get("fatigue_level"),
                },
            )
            
            # 🧹 Active Clean: Call PowerShell Script
            import subprocess
            cleanup_script = r"c:\workspace\agi\scripts\metabolic_cleanup.ps1"
            print(f"🧹 Invoking Active Metabolic Cleaner: {cleanup_script}")
            subprocess.run(
                ["powershell", "-ExecutionPolicy", "Bypass", "-File", cleanup_script], 
                check=False,
                creationflags=0x08000000  # CREATE_NO_WINDOW
            )
            
        except Exception as e:
            print(f"❌ Cleanup Execution Failed: {e}")
=======
>>>>>>> origin/main
                    "cpu_percent": current_workload.get("cpu_percent"),
                    "memory_percent": current_workload.get("memory_percent"),
                    "fatigue_level": current_fatigue.get("fatigue_level"),
                },
            )
        except Exception:
            pass
        
        # 실제 청소 작업 (예시)
        # - 메모리 최적화
        # - 임시 파일 정리
        # - 캐시 정리
        time.sleep(2)  # 시뮬레이션
        
        duration = time.time() - start
        
        # 청소 완료 기록
        self.fatigue.mark_cleanup()

        print(f"✅ 청소 완료 ({duration:.1f}초)")

        result = {
            "success": True,
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        }

        # 이벤트: cleanup_end
        try:
            self.logger.log(
                "cleanup_end",
                {
                    "success": result["success"],
                    "duration": result["duration"],
                },
            )
        except Exception:
            pass

        return result
    
    def adaptive_loop(self, check_interval: int = 60):
        """적응형 루프 (1분마다 체크)"""
        print("🔄 적응형 Glymphatic 시스템 시작")
        
        while True:
            try:
                # 상태 체크 및 결정
                status = self.monitor_and_decide()
                
                print(f"\n⏰ {datetime.now().strftime('%H:%M:%S')}")
                print(f"   작업량: {status['workload']['workload_percent']:.1f}%")
                print(f"   피로도: {status['fatigue']['fatigue_level']:.1f}%")
                print(f"   조정 피로도: {status['rhythm_adjustment']['adjusted_fatigue']:.1f}%")
                print(f"   리듬: {status['rhythm_adjustment'].get('rhythm_phase', 'unknown')}")
                print(f"   결정: {status['decision']['action']}")
                
                # 청소 필요시 실행
                if status["should_cleanup"]:
                    self.run_cleanup()
                
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                print("\n🛑 시스템 중지")
                break
            except Exception as e:
                print(f"❌ 오류: {e}")
                time.sleep(check_interval)


if __name__ == "__main__":
    system = AdaptiveGlymphaticSystem()
    system.adaptive_loop()
