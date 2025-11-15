#!/usr/bin/env python3
"""
Background Monitor - 동시 작업 시스템의 핵심

역할:
  1. COLLABORATION_STATE.jsonl을 계속 감시
  2. 파일 변경 감지 (협력자의 업데이트)
  3. 자동으로 필요한 에이전트 활성화
  4. 상태 동기화

구조:
  - FileWatcher: 파일 변경 감지
  - EventHandler: 이벤트 처리
  - AgentCoordinator: 에이전트 간 조율

Sena의 판단으로 구현됨 (2025-10-20)
"""

import os
import json
import time
import threading
from pathlib import Path
from typing import Dict, List, Callable, Optional, Any
from datetime import datetime, timezone
from collections import deque


class FileWatcher:
    """파일 변경을 감시하는 클래스"""

    def __init__(self, file_path: str, poll_interval: float = 2.0):
        """
        Args:
            file_path: 감시할 파일 경로
            poll_interval: 감시 주기 (초)
        """
        self.file_path = file_path
        self.poll_interval = poll_interval
        self.last_modified = 0
        self.last_size = 0
        self.callbacks = []
        self.running = False
        self.thread = None

    def add_callback(self, callback: Callable):
        """파일 변경 시 호출할 콜백 함수 등록"""
        self.callbacks.append(callback)

    def start(self):
        """감시 시작"""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._watch, daemon=True)
        self.thread.start()
        print(f"[FileWatcher] Started watching {self.file_path}")

    def stop(self):
        """감시 중지"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print(f"[FileWatcher] Stopped watching {self.file_path}")

    def _watch(self):
        """파일 감시 루프"""
        while self.running:
            try:
                if os.path.exists(self.file_path):
                    current_mtime = os.path.getmtime(self.file_path)
                    current_size = os.path.getsize(self.file_path)

                    # 파일이 수정됨 감지
                    if current_mtime > self.last_modified or current_size > self.last_size:
                        # 파일이 쓰기 중일 수 있으니 조금 대기
                        time.sleep(0.5)

                        # 콜백 함수 호출
                        for callback in self.callbacks:
                            try:
                                callback(self.file_path)
                            except Exception as e:
                                print(f"[FileWatcher] Callback error: {str(e)}")

                        self.last_modified = current_mtime
                        self.last_size = current_size

                time.sleep(self.poll_interval)

            except Exception as e:
                print(f"[FileWatcher] Error: {str(e)}")
                time.sleep(self.poll_interval)


class EventBuffer:
    """최근 이벤트를 버퍼링하는 클래스"""

    def __init__(self, max_size: int = 100):
        self.events = deque(maxlen=max_size)
        self.lock = threading.Lock()

    def add_event(self, event: Dict[str, Any]):
        """이벤트 추가"""
        with self.lock:
            self.events.append({
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                **event
            })

    def get_latest_by_agent(self, agent: str, limit: int = 10) -> List[Dict]:
        """특정 에이전트의 최근 이벤트"""
        with self.lock:
            return [
                e for e in list(self.events)[-limit:]
                if e.get("agent") == agent
            ]

    def get_latest_event(self) -> Optional[Dict]:
        """최근 이벤트"""
        with self.lock:
            return self.events[-1] if self.events else None


class BackgroundMonitor:
    """
    동시 작업을 가능하게 하는 백그라운드 모니터

    역할:
      1. COLLABORATION_STATE 감시
      2. 협력자의 업데이트 감지
      3. 필요한 에이전트 활성화
      4. 상태 동기화
    """

    def __init__(self, collab_state_path: str):
        """
        Args:
            collab_state_path: COLLABORATION_STATE.jsonl 경로
        """
        self.collab_state_path = collab_state_path
        self.watcher = FileWatcher(collab_state_path, poll_interval=2.0)
        self.event_buffer = EventBuffer(max_size=200)
        self.last_processed_line = 0
        self.agent_handlers = {}  # agent별 핸들러
        self.running = False

        # 핸들러 등록
        self._register_handlers()

    def _register_handlers(self):
        """에이전트별 핸들러 등록"""
        self.agent_handlers = {
            "sena": self._handle_sena_update,
            "lubit": self._handle_lubit_update,
            "gitcode": self._handle_gitcode_update,
        }

    def register_handler(self, agent: str, handler: Callable):
        """커스텀 핸들러 등록"""
        self.agent_handlers[agent] = handler

    def start(self):
        """모니터링 시작"""
        if self.running:
            print("[BackgroundMonitor] Already running")
            return

        self.running = True
        self.watcher.add_callback(self._on_collab_state_changed)
        self.watcher.start()
        print("[BackgroundMonitor] Started")

    def stop(self):
        """모니터링 중지"""
        self.running = False
        self.watcher.stop()
        print("[BackgroundMonitor] Stopped")

    def _on_collab_state_changed(self, file_path: str):
        """COLLABORATION_STATE 파일이 변경되었을 때 호출"""
        try:
            new_events = self._read_new_events()

            for event in new_events:
                # 이벤트 버퍼에 추가
                self.event_buffer.add_event(event)

                # 에이전트별 핸들러 호출
                agent = event.get("agent", "unknown")
                if agent in self.agent_handlers:
                    print(f"[BackgroundMonitor] Detected {agent}'s update: {event.get('event')}")
                    self.agent_handlers[agent](event)

        except Exception as e:
            print(f"[BackgroundMonitor] Error processing events: {str(e)}")

    def _read_new_events(self) -> List[Dict]:
        """COLLABORATION_STATE에서 새로운 이벤트만 읽기"""
        new_events = []

        try:
            with open(self.collab_state_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # 이전에 처리한 라인 이후의 것만
            for i in range(self.last_processed_line, len(lines)):
                try:
                    event = json.loads(lines[i].strip())
                    new_events.append(event)
                except json.JSONDecodeError:
                    continue

            self.last_processed_line = len(lines)

        except Exception as e:
            print(f"[BackgroundMonitor] Error reading file: {str(e)}")

        return new_events

    def _handle_sena_update(self, event: Dict):
        """Sena의 업데이트 처리"""
        event_type = event.get("event")

        if event_type == "status_update":
            progress = event.get("progress", 0)
            print(f"[Monitor→Lubit] Sena progress: {progress}%")

            # Lubit이 해야 할 일이 있는지 확인
            if progress >= 50 and progress < 100:
                print(f"[Monitor→Lubit] Suggested action: Start validation")

        elif event_type == "decision_request":
            print(f"[Monitor→Lubit] Sena requesting decision on: {event.get('request')}")
            print(f"[Monitor→Lubit] Lubit should review and respond")

        elif event_type == "blocker":
            print(f"[Monitor→Lubit] BLOCKER: {event.get('blocker')}")
            print(f"[Monitor→Lubit] Lubit priority increased - needs immediate attention")

    def _handle_lubit_update(self, event: Dict):
        """Lubit의 업데이트 처리"""
        event_type = event.get("event")

        if event_type == "decision":
            verdict = event.get("verdict")
            print(f"[Monitor→Sena] Lubit decision: {verdict}")

            if verdict == "approved":
                print(f"[Monitor→Sena] Blocker RESOLVED - Sena can proceed!")

        elif event_type == "validation_started":
            print(f"[Monitor→Sena] Lubit started validation")
            print(f"[Monitor→Sena] Sena should adjust pace if needed")

        elif event_type == "status_update":
            status = event.get("status")
            print(f"[Monitor→Sena] Lubit status: {status}")

    def _handle_gitcode_update(self, event: Dict):
        """GitCode의 업데이트 처리"""
        event_type = event.get("event")

        if event_type == "deployment_started":
            print(f"[Monitor→Sena,Lubit] Phase 4 deployment started!")
            print(f"[Monitor→All] Pause non-critical work, focus on monitoring")

    def get_agent_status(self, agent: str) -> Optional[Dict]:
        """특정 에이전트의 최신 상태"""
        latest_events = self.event_buffer.get_latest_by_agent(agent, limit=1)
        return latest_events[0] if latest_events else None

    def get_all_agents_status(self) -> Dict[str, Optional[Dict]]:
        """모든 에이전트의 현재 상태"""
        return {
            "sena": self.get_agent_status("sena"),
            "lubit": self.get_agent_status("lubit"),
            "gitcode": self.get_agent_status("gitcode"),
        }

    def print_status(self):
        """현재 상태 출력"""
        print("\n" + "="*70)
        print("BACKGROUND MONITOR STATUS")
        print("="*70)

        statuses = self.get_all_agents_status()
        for agent, status in statuses.items():
            if status:
                print(f"\n[{agent.upper()}]")
                print(f"  Event: {status.get('event')}")
                print(f"  Status: {status.get('status', 'N/A')}")
                print(f"  Progress: {status.get('progress', 'N/A')}%")
                print(f"  Timestamp: {status.get('timestamp', 'N/A')}")
            else:
                print(f"\n[{agent.upper()}] No activity yet")

        print("\n" + "="*70)


def demo():
    """데모: 백그라운드 모니터 작동"""
    print("="*70)
    print("Background Monitor - Demo")
    print("="*70)

    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    if (Path(__file__).parent.parent / 'fdo_agi_repo').exists():
        sys.path.insert(0, str(Path(__file__).parent.parent / 'fdo_agi_repo'))
        from workspace_utils import find_workspace_root
        workspace = find_workspace_root(Path(__file__).parent)
    else:
        workspace = Path(__file__).parent.parent
    
    collab_state_path = workspace / "session_memory" / "COLLABORATION_STATE.jsonl"

    # 모니터 생성
    monitor = BackgroundMonitor(collab_state_path)

    # 시뮬레이션: 새로운 이벤트 생성
    print("\n[SIMULATION] Adding events to COLLABORATION_STATE...\n")

    events_to_add = [
        {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "agent": "sena",
            "event": "status_update",
            "progress": 50,
            "status": "in_progress"
        },
        {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "agent": "lubit",
            "event": "validation_started",
            "target": "sena_metrics"
        },
        {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "agent": "sena",
            "event": "status_update",
            "progress": 75,
            "status": "in_progress"
        },
        {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "agent": "lubit",
            "event": "decision",
            "verdict": "approved",
            "comment": "Metrics design is correct"
        },
    ]

    # 모니터 시작
    print("[INFO] Starting background monitor...\n")
    monitor.start()

    # 이벤트 추가 (파일에 append)
    try:
        with open(collab_state_path, 'a', encoding='utf-8') as f:
            for event in events_to_add:
                f.write(json.dumps(event, ensure_ascii=False) + '\n')
                print(f"[ADDED] {event['agent']}: {event['event']}")
                time.sleep(1)  # 이벤트 사이에 간격

    except Exception as e:
        print(f"[ERROR] Cannot write to file: {str(e)}")

    # 모니터가 이벤트를 감지할 시간 제공
    print("\n[INFO] Monitor is watching for changes...\n")
    time.sleep(5)

    # 상태 출력
    monitor.print_status()

    # 정리
    monitor.stop()

    print("\n" + "="*70)
    print("[SUCCESS] Background Monitor Demo Complete!")
    print("="*70)


if __name__ == "__main__":
    demo()
