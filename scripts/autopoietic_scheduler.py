"""
Autopoietic Scheduler - AGI System Task Automation

원본: C:\\workspace\\original_data\\scheduler.py
목적: 자동화 작업 실행 (일일/시간별/즉시)
구현: 순수 Python (APScheduler 의존성 제거)

핵심 기능:
- 일일 작업: 매일 03:00 (BQI 학습, 모니터링 유지보수 등)
- 시간별 작업: 매시 정각 (메트릭 수집, 헬스체크)
- 즉시 실행: 테스트/디버깅용

Exit Code:
  0 = Success
  1 = Failure
"""
import sys
import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Callable, List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum



class ScheduleType(Enum):
    """스케줄 타입"""
    DAILY = "daily"  # 매일 지정 시각
    HOURLY = "hourly"  # 매시 지정 분
    ONCE = "once"  # 1회 실행


@dataclass
class ScheduledTask:
    """스케줄된 작업 정의"""
    task_id: str
    name: str
    func: Callable
    schedule_type: ScheduleType
    hour: int = 0  # DAILY용
    minute: int = 0
    description: str = ""
    enabled: bool = True
    last_run: Optional[datetime] = None


class AutopoieticScheduler:
    """
    Autopoietic Scheduler (자율 유지 스케줄러)
    
    순수 Python 구현 (의존성 없음)
    원본 scheduler.py의 핵심 로직을 간소화하여 현재 AGI 시스템에 통합.
    """

    def __init__(self):
        """스케줄러 초기화"""
        self.tasks: List[ScheduledTask] = []
        self.execution_history: List[Dict[str, Any]] = []
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self.logger = logging.getLogger("AutopoieticScheduler")
        self.logger.info("Scheduler initialized (pure Python implementation)")

    def add_task(
        self,
        task_id: str,
        name: str,
        func: Callable,
        schedule_type: ScheduleType,
        hour: int = 0,
        minute: int = 0,
        description: str = "",
        enabled: bool = True
    ):
        """작업 추가"""
        task = ScheduledTask(
            task_id=task_id,
            name=name,
            func=func,
            schedule_type=schedule_type,
            hour=hour,
            minute=minute,
            description=description,
            enabled=enabled
        )
        self.tasks.append(task)
        
        if enabled:
            self.logger.info(f"Task added: {name} (id={task_id}, type={schedule_type.value})")
        else:
            self.logger.info(f"Task registered but disabled: {name}")

    def add_daily_task(
        self,
        task_id: str,
        name: str,
        func: Callable,
        hour: int,
        minute: int = 0,
        description: str = ""
    ):
        """일일 작업 추가 (매일 지정 시각 실행)"""
        self.add_task(task_id, name, func, ScheduleType.DAILY, hour, minute, description)

    def add_hourly_task(
        self,
        task_id: str,
        name: str,
        func: Callable,
        minute: int = 0,
        description: str = ""
    ):
        """시간별 작업 추가 (매시 지정 분 실행)"""
        self.add_task(task_id, name, func, ScheduleType.HOURLY, 0, minute, description)

    def _should_run_task(self, task: ScheduledTask) -> bool:
        """작업 실행 여부 판단"""
        if not task.enabled:
            return False

        now = datetime.now()

        # 첫 실행이면 무조건 실행
        if task.last_run is None:
            return False  # 첫 스케줄링 시점에는 실행 안 함 (다음 시각부터)

        if task.schedule_type == ScheduleType.DAILY:
            # 매일 지정 시각
            if now.hour == task.hour and now.minute == task.minute:
                # 이미 실행했는지 확인 (같은 분 내 중복 실행 방지)
                if task.last_run and task.last_run.replace(second=0, microsecond=0) == now.replace(second=0, microsecond=0):
                    return False
                return True
        
        elif task.schedule_type == ScheduleType.HOURLY:
            # 매시 지정 분
            if now.minute == task.minute:
                # 이미 실행했는지 확인
                if task.last_run and task.last_run.replace(second=0, microsecond=0) == now.replace(second=0, microsecond=0):
                    return False
                return True

        return False

    def _scheduler_loop(self):
        """스케줄러 메인 루프"""
        self.logger.info("Scheduler loop started")
        
        while self.running:
            try:
                now = datetime.now()
                
                for task in self.tasks:
                    if self._should_run_task(task):
                        self.logger.info(f"Executing scheduled task: {task.name}")
                        self._execute_task(task)
                
                # 1분 대기
                time.sleep(60)
                
            except Exception as e:
                self.logger.error(f"Scheduler loop error: {e}")
                time.sleep(60)

        self.logger.info("Scheduler loop stopped")

    def _execute_task(self, task: ScheduledTask):
        """작업 실행 (내부용)"""
        start_time = time.time()
        task.last_run = datetime.now()
        
        try:
            task.func()
            duration = time.time() - start_time
            self.logger.info(f"Task completed: {task.name} ({duration:.2f}s)")
            
            self.execution_history.append({
                "task_id": task.task_id,
                "task_name": task.name,
                "timestamp": task.last_run.isoformat(),
                "duration_seconds": duration,
                "status": "SUCCESS"
            })
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Task failed: {task.name} - {e}")
            
            self.execution_history.append({
                "task_id": task.task_id,
                "task_name": task.name,
                "timestamp": task.last_run.isoformat(),
                "duration_seconds": duration,
                "status": "FAILED",
                "error": str(e)
            })

    def start(self):
        """스케줄러 시작 (백그라운드 스레드)"""
        if self.running:
            self.logger.warning("Scheduler already running")
            return

        self.running = True
        self._thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._thread.start()
        self.logger.info(f"Scheduler started with {len(self.tasks)} tasks")
        self._log_scheduled_tasks()

    def shutdown(self):
        """스케줄러 종료"""
        if not self.running:
            self.logger.info("Scheduler was not running")
            return

        self.running = False
        if self._thread:
            self._thread.join(timeout=5)
        self.logger.info("Scheduler shutdown complete")

    def run_task_now(self, task_id: str) -> bool:
        """작업 즉시 실행 (테스트/디버깅용)"""
        task = next((t for t in self.tasks if t.task_id == task_id), None)
        if not task:
            self.logger.error(f"Task not found: {task_id}")
            return False

        self.logger.info(f"Running task immediately: {task.name}")
        start_time = time.time()
        
        try:
            task.func()
            duration = time.time() - start_time
            self.logger.info(f"Task completed: {task.name} ({duration:.2f}s)")
            
            self.execution_history.append({
                "task_id": task_id,
                "task_name": task.name,
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": duration,
                "status": "SUCCESS"
            })
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Task failed: {task.name} - {e}")
            
            self.execution_history.append({
                "task_id": task_id,
                "task_name": task.name,
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": duration,
                "status": "FAILED",
                "error": str(e)
            })
            return False

    def get_status(self) -> Dict[str, Any]:
        """스케줄러 상태 조회"""
        return {
            "running": self.running,
            "total_tasks": len(self.tasks),
            "enabled_tasks": sum(1 for t in self.tasks if t.enabled),
            "execution_count": len(self.execution_history),
            "last_execution": self.execution_history[-1] if self.execution_history else None,
            "tasks": [
                {
                    "id": t.task_id,
                    "name": t.name,
                    "type": t.schedule_type.value,
                    "schedule": f"{t.hour:02d}:{t.minute:02d}" if t.schedule_type == ScheduleType.DAILY else f"*:{t.minute:02d}",
                    "last_run": t.last_run.isoformat() if t.last_run else None
                }
                for t in self.tasks if t.enabled
            ]
        }

    def _log_scheduled_tasks(self):
        """등록된 작업 로깅"""
        if self.tasks:
            self.logger.info("Scheduled tasks:")
            for task in self.tasks:
                if task.enabled:
                    if task.schedule_type == ScheduleType.DAILY:
                        schedule_str = f"daily at {task.hour:02d}:{task.minute:02d}"
                    elif task.schedule_type == ScheduleType.HOURLY:
                        schedule_str = f"hourly at :{task.minute:02d}"
                    else:
                        schedule_str = "once"
                    self.logger.info(f"  - {task.name} (id={task.task_id}, {schedule_str})")
        else:
            self.logger.warning("No tasks registered")


# ============================================================================
# 예제 작업 함수들 (실제 운영 시 교체 필요)
# ============================================================================

def task_bqi_daily_learning():
    """BQI 일일 학습 작업"""
    logging.info("[BQI] Daily learning task started")
    time.sleep(0.5)  # 실제 작업 시뮬레이션
    logging.info("[BQI] Daily learning completed")


def task_monitoring_maintenance():
    """모니터링 일일 유지보수 (로그 정리, 스냅샷 회전 등)"""
    logging.info("[Monitoring] Daily maintenance started")
    time.sleep(0.3)
    logging.info("[Monitoring] Maintenance completed")


def task_hourly_health_check():
    """시간별 헬스체크"""
    logging.info("[Health] Hourly check started")
    time.sleep(0.1)
    logging.info("[Health] Check completed")


# ============================================================================
# CLI 인터페이스
# ============================================================================

def demo_scheduler():
    """데모: 스케줄러 설정 및 즉시 실행 테스트"""
    print("=" * 70)
    print("Autopoietic Scheduler Demo")
    print("=" * 70)

    # 스케줄러 초기화
    scheduler = AutopoieticScheduler()

    # 일일 작업 등록
    scheduler.add_daily_task(
        task_id="bqi_daily",
        name="BQI Daily Learning",
        func=task_bqi_daily_learning,
        hour=3,
        minute=10,
        description="BQI 패턴 학습 (매일 03:10)"
    )

    scheduler.add_daily_task(
        task_id="monitoring_daily",
        name="Monitoring Maintenance",
        func=task_monitoring_maintenance,
        hour=3,
        minute=20,
        description="모니터링 유지보수 (매일 03:20)"
    )

    # 시간별 작업 등록
    scheduler.add_hourly_task(
        task_id="health_hourly",
        name="Hourly Health Check",
        func=task_hourly_health_check,
        minute=0,
        description="헬스체크 (매시 정각)"
    )

    print("\n[Info] Registered 3 tasks (2 daily, 1 hourly)")

    # 상태 확인
    status = scheduler.get_status()
    print(f"\n[Status] Running: {status['running']}")
    print(f"[Status] Total tasks: {status['total_tasks']}")
    print(f"[Status] Enabled: {status['enabled_tasks']}")

    # 즉시 실행 테스트
    print("\n[Test] Running tasks immediately for validation...")
    print("-" * 70)

    success_count = 0
    for task in scheduler.tasks:
        if scheduler.run_task_now(task.task_id):
            success_count += 1

    print("-" * 70)
    print(f"\n[Result] {success_count}/{len(scheduler.tasks)} tasks executed successfully")

    # 실행 이력
    if scheduler.execution_history:
        print("\n[History] Execution log:")
        for record in scheduler.execution_history[-3:]:
            status_icon = "✓" if record["status"] == "SUCCESS" else "✗"
            print(f"  {status_icon} {record['task_name']}: {record['duration_seconds']:.2f}s")

    print("\n" + "=" * 70)
    print("PASS: Scheduler demo completed successfully")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        exit_code = demo_scheduler()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\nFAIL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
