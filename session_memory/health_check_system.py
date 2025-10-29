#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
헬스 체크 및 자가 복구 시스템 - 시스템 건강도 모니터링

이 모듈은 에이전트 시스템의 건강도를 모니터링하고 자동으로 복구합니다.
"""

import sys
import io
import time
import threading
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import psutil

# UTF-8 인코딩 강제 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# ============================================================================
# 헬스 체크 상태
# ============================================================================

class HealthStatus(Enum):
    """헬스 상태"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """헬스 체크 결과"""
    component: str
    status: str
    message: str
    last_check: str
    response_time_ms: float = 0.0
    details: Dict[str, Any] = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}


# ============================================================================
# 헬스 체크 컴포넌트
# ============================================================================

class HealthCheck:
    """헬스 체크 기본 클래스"""

    def __init__(self, name: str, check_interval: int = 30):
        """초기화"""
        self.name = name
        self.check_interval = check_interval
        self.last_check: Optional[datetime] = None
        self.is_healthy = True
        self.failure_count = 0
        self.max_failures = 3

    def check(self) -> HealthCheckResult:
        """헬스 체크 수행"""
        start_time = time.time()
        result = self._perform_check()
        result.response_time_ms = (time.time() - start_time) * 1000

        self.last_check = datetime.now()

        # 실패 카운트 업데이트
        if result.status == HealthStatus.HEALTHY.value:
            self.failure_count = 0
            self.is_healthy = True
        else:
            self.failure_count += 1
            if self.failure_count >= self.max_failures:
                self.is_healthy = False

        return result

    def _perform_check(self) -> HealthCheckResult:
        """실제 헬스 체크 수행 (오버라이드 필요)"""
        raise NotImplementedError


class SystemHealthCheck(HealthCheck):
    """시스템 헬스 체크"""

    def _perform_check(self) -> HealthCheckResult:
        """시스템 리소스 확인"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        status = HealthStatus.HEALTHY.value
        message = "시스템 정상"

        if cpu_percent > 90:
            status = HealthStatus.WARNING.value
            message = f"CPU 사용률 높음: {cpu_percent}%"
        elif memory.percent > 90:
            status = HealthStatus.WARNING.value
            message = f"메모리 사용률 높음: {memory.percent}%"
        elif disk.percent > 90:
            status = HealthStatus.CRITICAL.value
            message = f"디스크 사용률 높음: {disk.percent}%"

        return HealthCheckResult(
            component="system",
            status=status,
            message=message,
            last_check=datetime.now().isoformat(),
            details={
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent
            }
        )


class DatabaseHealthCheck(HealthCheck):
    """데이터베이스 헬스 체크"""

    def _perform_check(self) -> HealthCheckResult:
        """데이터베이스 연결 확인"""
        # 실제 환경에서는 DB 쿼리 실행
        try:
            # 시뮬레이션: DB 연결 시도
            time.sleep(0.1)
            is_connected = True
        except Exception as e:
            is_connected = False
            return HealthCheckResult(
                component="database",
                status=HealthStatus.CRITICAL.value,
                message=f"DB 연결 실패: {str(e)}",
                last_check=datetime.now().isoformat()
            )

        if is_connected:
            return HealthCheckResult(
                component="database",
                status=HealthStatus.HEALTHY.value,
                message="DB 연결 정상",
                last_check=datetime.now().isoformat(),
                details={"connection_pool_size": 10, "active_connections": 3}
            )


class AgentHealthCheck(HealthCheck):
    """에이전트 헬스 체크"""

    def __init__(self, agent_id: str):
        super().__init__(f"agent_{agent_id}")
        self.agent_id = agent_id

    def _perform_check(self) -> HealthCheckResult:
        """에이전트 상태 확인"""
        # 실제 환경에서는 에이전트 상태 조회
        agent_status = {
            "is_responsive": True,
            "message_queue_size": 5,
            "error_count": 0,
            "uptime_seconds": 3600
        }

        status = HealthStatus.HEALTHY.value
        message = f"{self.agent_id} 정상"

        if not agent_status["is_responsive"]:
            status = HealthStatus.CRITICAL.value
            message = f"{self.agent_id} 응답 없음"

        return HealthCheckResult(
            component=f"agent_{self.agent_id}",
            status=status,
            message=message,
            last_check=datetime.now().isoformat(),
            details=agent_status
        )


# ============================================================================
# 자가 복구 시스템
# ============================================================================

class SelfHealing:
    """자가 복구"""

    def __init__(self):
        """초기화"""
        self.recovery_actions: Dict[str, Callable] = {}
        self.recovery_history: List[Dict[str, Any]] = []

    def register_recovery_action(self, component: str, action: Callable):
        """복구 액션 등록"""
        self.recovery_actions[component] = action

    def attempt_recovery(self, component: str, error: str) -> bool:
        """복구 시도"""
        if component not in self.recovery_actions:
            return False

        try:
            action = self.recovery_actions[component]
            action()

            self.recovery_history.append({
                "timestamp": datetime.now().isoformat(),
                "component": component,
                "error": error,
                "success": True
            })

            print(f"✓ {component} 복구 성공")
            return True

        except Exception as e:
            self.recovery_history.append({
                "timestamp": datetime.now().isoformat(),
                "component": component,
                "error": error,
                "recovery_error": str(e),
                "success": False
            })

            print(f"✗ {component} 복구 실패: {e}")
            return False


# ============================================================================
# 헬스 체크 매니저
# ============================================================================

class HealthCheckManager:
    """헬스 체크 관리자"""

    def __init__(self, check_interval: int = 30):
        """초기화"""
        self.check_interval = check_interval
        self.health_checks: Dict[str, HealthCheck] = {}
        self.self_healing = SelfHealing()
        self.running = False
        self.monitoring_thread: Optional[threading.Thread] = None
        self.results_history: List[HealthCheckResult] = []

    def register_check(self, health_check: HealthCheck):
        """헬스 체크 등록"""
        self.health_checks[health_check.name] = health_check

    def start_monitoring(self):
        """모니터링 시작"""
        self.running = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self.monitoring_thread.start()
        print("✓ 헬스 체크 모니터링 시작")

    def stop_monitoring(self):
        """모니터링 중지"""
        self.running = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        print("✓ 헬스 체크 모니터링 중지")

    def _monitoring_loop(self):
        """모니터링 루프"""
        while self.running:
            for check in self.health_checks.values():
                result = check.check()
                self.results_history.append(result)

                # 임계값 초과시 복구 시도
                if result.status == HealthStatus.CRITICAL.value:
                    self.self_healing.attempt_recovery(
                        result.component,
                        result.message
                    )

            time.sleep(self.check_interval)

    def get_overall_health(self) -> str:
        """전체 건강도 조회"""
        if not self.health_checks:
            return HealthStatus.UNKNOWN.value

        statuses = [check.is_healthy for check in self.health_checks.values()]

        if all(statuses):
            return HealthStatus.HEALTHY.value
        elif any(statuses):
            return HealthStatus.WARNING.value
        else:
            return HealthStatus.CRITICAL.value

    def get_health_report(self) -> Dict[str, Any]:
        """헬스 리포트 생성"""
        results = []

        for check in self.health_checks.values():
            result = check.check()
            results.append({
                "component": result.component,
                "status": result.status,
                "message": result.message,
                "response_time_ms": result.response_time_ms
            })

        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": self.get_overall_health(),
            "components": results,
            "recovery_attempts": len(self.self_healing.recovery_history)
        }

    def print_report(self):
        """리포트 출력"""
        report = self.get_health_report()

        print("\n" + "=" * 80)
        print(f"헬스 체크 리포트 - {report['overall_status'].upper()}")
        print("=" * 80)

        print(f"\n전체 상태: {report['overall_status']}")
        print(f"복구 시도: {report['recovery_attempts']}")

        print(f"\n컴포넌트 상태:")
        for component in report['components']:
            status_symbol = "✓" if component['status'] == "healthy" else "✗"
            print(f"  {status_symbol} {component['component']}: {component['status']}")
            print(f"     {component['message']} ({component['response_time_ms']:.1f}ms)")


# ============================================================================
# 데모: 헬스 체크 시스템
# ============================================================================

def demo_health_check():
    """헬스 체크 시스템 데모"""
    print("=" * 80)
    print("헬스 체크 및 자가 복구 시스템 데모")
    print("=" * 80)

    # 헬스 체크 매니저 생성
    print("\n[1단계] 헬스 체크 매니저 초기화")
    print("-" * 80)

    manager = HealthCheckManager(check_interval=5)

    # 헬스 체크 등록
    print("\n[2단계] 헬스 체크 등록")
    print("-" * 80)

    manager.register_check(SystemHealthCheck("system"))
    manager.register_check(DatabaseHealthCheck("database"))
    manager.register_check(AgentHealthCheck("sena"))
    manager.register_check(AgentHealthCheck("lubit"))

    print("✓ 시스템 헬스 체크 등록")
    print("✓ 데이터베이스 헬스 체크 등록")
    print("✓ Sena 에이전트 헬스 체크 등록")
    print("✓ Lubit 에이전트 헬스 체크 등록")

    # 복구 액션 등록
    print("\n[3단계] 자가 복구 액션 등록")
    print("-" * 80)

    def recover_database():
        """DB 복구"""
        print("  → DB 연결 복구 중...")
        time.sleep(0.5)

    def recover_agent():
        """에이전트 복구"""
        print("  → 에이전트 재시작 중...")
        time.sleep(0.5)

    manager.self_healing.register_recovery_action("database", recover_database)
    manager.self_healing.register_recovery_action("agent_sena", recover_agent)

    print("✓ 복구 액션 등록 완료")

    # 헬스 체크 수행
    print("\n[4단계] 초기 헬스 체크")
    print("-" * 80)

    manager.print_report()

    # 모니터링 시작
    print("\n[5단계] 모니터링 시작")
    print("-" * 80)

    manager.start_monitoring()
    time.sleep(2)

    # 중간 리포트
    print("\n[6단계] 모니터링 중 리포트")
    print("-" * 80)

    manager.print_report()

    # 모니터링 중지
    manager.stop_monitoring()

    # 최종 리포트
    print("\n[7단계] 최종 리포트")
    print("-" * 80)

    manager.print_report()

    print("\n" + "=" * 80)
    print("헬스 체크 시스템 데모 완료!")
    print("=" * 80)


if __name__ == "__main__":
    demo_health_check()
