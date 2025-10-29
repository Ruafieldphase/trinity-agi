#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
모니터링 시스템 - 실시간 에이전트 및 시스템 모니터링

이 모듈은 에이전트 시스템의 실시간 모니터링과 성능 추적을 제공합니다.
"""

import sys
import io
import json
import time
import statistics
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass, asdict

# UTF-8 인코딩 강제 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# ============================================================================
# 모니터링 데이터 클래스
# ============================================================================

@dataclass
class AgentMetrics:
    """에이전트 메트릭"""
    agent_id: str
    agent_name: str
    role: str
    timestamp: str

    # 성능 메트릭
    total_messages: int = 0
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0

    # 타이밍 메트릭
    min_execution_time: float = float('inf')
    max_execution_time: float = 0.0
    total_execution_time: float = 0.0
    execution_times: List[float] = None

    # 상태
    status: str = "idle"  # idle, processing, error
    error_count: int = 0

    def __post_init__(self):
        if self.execution_times is None:
            self.execution_times = []

    def add_execution(self, execution_time: float, success: bool):
        """실행 데이터 추가"""
        self.execution_times.append(execution_time)
        self.total_execution_time += execution_time
        self.min_execution_time = min(self.min_execution_time, execution_time)
        self.max_execution_time = max(self.max_execution_time, execution_time)

        if success:
            self.successful_tasks += 1
        else:
            self.failed_tasks += 1

    def get_avg_execution_time(self) -> float:
        """평균 실행 시간"""
        if not self.execution_times:
            return 0.0
        return statistics.mean(self.execution_times)

    def get_success_rate(self) -> float:
        """성공률"""
        total = self.successful_tasks + self.failed_tasks
        if total == 0:
            return 0.0
        return self.successful_tasks / total * 100

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "role": self.role,
            "timestamp": self.timestamp,
            "total_messages": self.total_messages,
            "total_tasks": self.total_tasks,
            "successful_tasks": self.successful_tasks,
            "failed_tasks": self.failed_tasks,
            "success_rate": self.get_success_rate(),
            "min_execution_time": self.min_execution_time if self.min_execution_time != float('inf') else 0,
            "max_execution_time": self.max_execution_time,
            "avg_execution_time": self.get_avg_execution_time(),
            "total_execution_time": self.total_execution_time,
            "status": self.status,
            "error_count": self.error_count
        }


@dataclass
class SystemMetrics:
    """시스템 메트릭"""
    timestamp: str

    # 작업 메트릭
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    in_progress_tasks: int = 0

    # 메시지 메트릭
    total_messages: int = 0
    successful_messages: int = 0
    failed_messages: int = 0

    # 에이전트 메트릭
    active_agents: int = 0
    idle_agents: int = 0
    error_agents: int = 0

    # 성능 메트릭
    avg_task_time: float = 0.0
    min_task_time: float = 0.0
    max_task_time: float = 0.0

    def get_overall_success_rate(self) -> float:
        """전체 성공률"""
        total = self.completed_tasks + self.failed_tasks
        if total == 0:
            return 0.0
        return self.completed_tasks / total * 100

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "timestamp": self.timestamp,
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "in_progress_tasks": self.in_progress_tasks,
            "success_rate": self.get_overall_success_rate(),
            "total_messages": self.total_messages,
            "successful_messages": self.successful_messages,
            "failed_messages": self.failed_messages,
            "active_agents": self.active_agents,
            "idle_agents": self.idle_agents,
            "error_agents": self.error_agents,
            "avg_task_time": self.avg_task_time,
            "min_task_time": self.min_task_time,
            "max_task_time": self.max_task_time
        }


# ============================================================================
# 모니터링 시스템
# ============================================================================

class MonitoringSystem:
    """에이전트 시스템 모니터링"""

    def __init__(self, history_retention_hours: int = 24):
        """모니터링 시스템 초기화"""
        self.history_retention_hours = history_retention_hours

        # 메트릭 저장소
        self.agent_metrics: Dict[str, AgentMetrics] = {}
        self.system_metrics: List[SystemMetrics] = []

        # 이벤트 로그
        self.events: List[Dict[str, Any]] = []

        # 알림 임계값
        self.alerts: Dict[str, Any] = {
            "error_threshold": 3,  # 에러 임계값
            "slow_task_threshold": 5000,  # 느린 작업 임계값 (ms)
            "low_success_rate_threshold": 80,  # 낮은 성공률 임계값 (%)
        }

    def register_agent(self, agent_id: str, agent_name: str, role: str):
        """에이전트 등록"""
        self.agent_metrics[agent_id] = AgentMetrics(
            agent_id=agent_id,
            agent_name=agent_name,
            role=role,
            timestamp=datetime.now().isoformat()
        )

    def record_agent_action(self, agent_id: str, action_type: str, execution_time: float, success: bool = True):
        """에이전트 액션 기록"""
        if agent_id not in self.agent_metrics:
            return

        metrics = self.agent_metrics[agent_id]

        if action_type == "message":
            metrics.total_messages += 1
        elif action_type == "task":
            metrics.total_tasks += 1
            metrics.add_execution(execution_time, success)

        # 이벤트 로깅
        self.log_event(
            agent_id=agent_id,
            event_type=action_type,
            status="success" if success else "failure",
            execution_time=execution_time
        )

        # 알림 확인
        self.check_alerts(agent_id)

    def record_task_completion(self, task_id: str, success: bool, execution_time: float):
        """작업 완료 기록"""
        self.log_event(
            task_id=task_id,
            event_type="task_completion",
            status="success" if success else "failure",
            execution_time=execution_time
        )

    def log_event(self, **kwargs):
        """이벤트 로깅"""
        event = {
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }
        self.events.append(event)

    def check_alerts(self, agent_id: str):
        """알림 확인"""
        if agent_id not in self.agent_metrics:
            return

        metrics = self.agent_metrics[agent_id]

        # 에러 임계값 확인
        if metrics.error_count >= self.alerts["error_threshold"]:
            self.log_event(
                event_type="alert",
                alert_type="high_error_count",
                agent_id=agent_id,
                value=metrics.error_count
            )

        # 느린 작업 확인
        if metrics.execution_times:
            avg_time = metrics.get_avg_execution_time()
            if avg_time > self.alerts["slow_task_threshold"]:
                self.log_event(
                    event_type="alert",
                    alert_type="slow_task",
                    agent_id=agent_id,
                    value=avg_time
                )

        # 낮은 성공률 확인
        if metrics.total_tasks > 0:
            success_rate = metrics.get_success_rate()
            if success_rate < self.alerts["low_success_rate_threshold"]:
                self.log_event(
                    event_type="alert",
                    alert_type="low_success_rate",
                    agent_id=agent_id,
                    value=success_rate
                )

    def get_agent_metrics(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """에이전트 메트릭 조회"""
        if agent_id not in self.agent_metrics:
            return None
        return self.agent_metrics[agent_id].to_dict()

    def get_all_agent_metrics(self) -> List[Dict[str, Any]]:
        """모든 에이전트 메트릭 조회"""
        return [metrics.to_dict() for metrics in self.agent_metrics.values()]

    def calculate_system_metrics(self) -> SystemMetrics:
        """시스템 메트릭 계산"""
        metrics = SystemMetrics(timestamp=datetime.now().isoformat())

        # 에이전트별 메트릭 집계
        all_execution_times = []

        for agent_metrics in self.agent_metrics.values():
            metrics.total_tasks += agent_metrics.total_tasks
            metrics.completed_tasks += agent_metrics.successful_tasks
            metrics.failed_tasks += agent_metrics.failed_tasks
            metrics.total_messages += agent_metrics.total_messages

            if agent_metrics.status == "processing":
                metrics.active_agents += 1
            elif agent_metrics.status == "error":
                metrics.error_agents += 1
            else:
                metrics.idle_agents += 1

            all_execution_times.extend(agent_metrics.execution_times)

        # 평균 작업 시간 계산
        if all_execution_times:
            metrics.avg_task_time = statistics.mean(all_execution_times)
            metrics.min_task_time = min(all_execution_times)
            metrics.max_task_time = max(all_execution_times)

        # 메시지 메트릭 (간단한 추정)
        metrics.successful_messages = metrics.total_tasks
        metrics.failed_messages = metrics.failed_tasks

        self.system_metrics.append(metrics)
        self.cleanup_old_metrics()

        return metrics

    def cleanup_old_metrics(self):
        """오래된 메트릭 정리"""
        cutoff_time = datetime.now() - timedelta(hours=self.history_retention_hours)

        self.system_metrics = [
            m for m in self.system_metrics
            if datetime.fromisoformat(m.timestamp) > cutoff_time
        ]

        self.events = [
            e for e in self.events
            if datetime.fromisoformat(e["timestamp"]) > cutoff_time
        ]

    def get_system_metrics(self) -> Dict[str, Any]:
        """시스템 메트릭 조회"""
        metrics = self.calculate_system_metrics()
        return metrics.to_dict()

    def get_events(self, filter_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """이벤트 조회"""
        events = self.events

        if filter_type:
            events = [e for e in events if e.get("event_type") == filter_type]

        return events[-limit:]

    def print_dashboard(self):
        """모니터링 대시보드 출력"""
        print("\n" + "=" * 80)
        print("에이전트 시스템 모니터링 대시보드")
        print("=" * 80)

        # 시스템 요약
        system_metrics = self.get_system_metrics()

        print("\n[시스템 요약]")
        print(f"  작업:")
        print(f"    총 작업: {system_metrics['total_tasks']}")
        print(f"    완료: {system_metrics['completed_tasks']}")
        print(f"    실패: {system_metrics['failed_tasks']}")
        print(f"    진행중: {system_metrics['in_progress_tasks']}")
        print(f"    성공률: {system_metrics['success_rate']:.1f}%")

        print(f"\n  메시지:")
        print(f"    총: {system_metrics['total_messages']}")
        print(f"    성공: {system_metrics['successful_messages']}")
        print(f"    실패: {system_metrics['failed_messages']}")

        print(f"\n  성능:")
        print(f"    평균 작업 시간: {system_metrics['avg_task_time']:.2f}ms")
        print(f"    최소: {system_metrics['min_task_time']:.2f}ms")
        print(f"    최대: {system_metrics['max_task_time']:.2f}ms")

        print(f"\n  에이전트:")
        print(f"    활성: {system_metrics['active_agents']}")
        print(f"    유휴: {system_metrics['idle_agents']}")
        print(f"    에러: {system_metrics['error_agents']}")

        # 에이전트별 상세 정보
        print("\n[에이전트별 메트릭]")
        print("-" * 80)

        for agent_metrics in self.get_all_agent_metrics():
            print(f"\n{agent_metrics['agent_name']} ({agent_metrics['role']})")
            print(f"  ID: {agent_metrics['agent_id']}")
            print(f"  상태: {agent_metrics['status']}")
            print(f"  메시지: {agent_metrics['total_messages']}")
            print(f"  작업: {agent_metrics['total_tasks']} (성공: {agent_metrics['successful_tasks']}, 실패: {agent_metrics['failed_tasks']})")
            print(f"  성공률: {agent_metrics['success_rate']:.1f}%")
            if agent_metrics['total_tasks'] > 0:
                print(f"  실행 시간: 평균 {agent_metrics['avg_execution_time']:.2f}ms (범위: {agent_metrics['min_execution_time']:.2f}-{agent_metrics['max_execution_time']:.2f}ms)")
            print(f"  에러: {agent_metrics['error_count']}")

        # 최근 이벤트
        print("\n[최근 이벤트]")
        print("-" * 80)

        events = self.get_events(limit=10)
        if events:
            for event in events[-5:]:
                print(f"  [{event['timestamp']}] {event.get('event_type', 'unknown')}: {event.get('status', 'N/A')}")
        else:
            print("  이벤트 없음")

        print("\n" + "=" * 80)

    def export_metrics(self, filepath: str):
        """메트릭 내보내기"""
        metrics_data = {
            "timestamp": datetime.now().isoformat(),
            "system_metrics": self.get_system_metrics(),
            "agent_metrics": self.get_all_agent_metrics(),
            "events": self.get_events(limit=1000)
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(metrics_data, f, indent=2, ensure_ascii=False)


# ============================================================================
# 데모: 모니터링 시스템
# ============================================================================

def demo_monitoring_system():
    """모니터링 시스템 데모"""
    print("=" * 80)
    print("모니터링 시스템 데모")
    print("=" * 80)

    # 모니터링 시스템 생성
    monitoring = MonitoringSystem()

    # 에이전트 등록
    print("\n[1] 에이전트 등록")
    print("-" * 80)

    agents = [
        ("agent_001", "Sena", "분석가"),
        ("agent_002", "Lubit", "게이트키퍼"),
        ("agent_003", "GitCode", "실행자"),
        ("agent_004", "RUNE", "윤리 검증자")
    ]

    for agent_id, agent_name, role in agents:
        monitoring.register_agent(agent_id, agent_name, role)
        print(f"✓ {agent_name} ({role}) 등록")

    # 액션 기록
    print("\n[2] 액션 기록")
    print("-" * 80)

    import random

    for _ in range(20):
        agent_id = agents[random.randint(0, 3)][0]
        action_type = random.choice(["message", "task"])
        execution_time = random.uniform(0.5, 5.0)
        success = random.random() > 0.1  # 90% 성공률

        monitoring.record_agent_action(agent_id, action_type, execution_time, success)

    print("✓ 20개 액션 기록 완료")

    # 시스템 메트릭 계산
    print("\n[3] 시스템 메트릭 계산")
    print("-" * 80)

    system_metrics = monitoring.calculate_system_metrics()
    print(f"✓ 시스템 메트릭 계산 완료")
    print(f"  성공률: {system_metrics.get_overall_success_rate():.1f}%")

    # 대시보드 출력
    print("\n[4] 모니터링 대시보드")
    monitoring.print_dashboard()

    # 메트릭 내보내기
    print("\n[5] 메트릭 내보내기")
    print("-" * 80)

    monitoring.export_metrics("d:\\nas_backup\\session_memory\\monitoring_metrics.json")
    print("✓ 메트릭을 monitoring_metrics.json으로 내보냈습니다")

    print("\n" + "=" * 80)
    print("모니터링 시스템 데모 완료!")
    print("=" * 80)


if __name__ == "__main__":
    demo_monitoring_system()
