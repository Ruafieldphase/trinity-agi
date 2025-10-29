"""
Agent INBOX Watcher - 실시간 작업 감지 및 자동 실행
====================================================

목적:
1. 각 에이전트의 INBOX 폴더 모니터링
2. 새 작업 파일 감지 시 자동 실행
3. 백그라운드에서 지속 실행

통합:
- watchdog 라이브러리: 파일 시스템 이벤트 감지
- agent_base.AgentBase: 작업 처리
"""

import asyncio
import json
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from agent_base import AgentBase, TaskContext

# ============================================================================
# INBOX 파일 이벤트 핸들러
# ============================================================================


class InboxFileHandler(FileSystemEventHandler):
    """
    INBOX 폴더의 파일 생성 이벤트를 감지하는 핸들러
    """

    def __init__(self, agent: AgentBase, process_immediately: bool = True):
        """
        Args:
            agent: AgentBase 인스턴스
            process_immediately: True이면 파일 감지 즉시 처리, False이면 큐에만 추가
        """
        super().__init__()
        self.agent = agent
        self.process_immediately = process_immediately
        self.pending_tasks = []  # 처리 대기 작업 큐

    def on_created(self, event):
        """
        파일 생성 이벤트 핸들러

        Args:
            event: FileSystemEvent
        """
        # 디렉토리 무시
        if event.is_directory:
            return

        # .json 파일만 처리
        file_path = Path(event.src_path)
        if file_path.suffix != ".json":
            return

        print(f"📬 [{self.agent.agent_name}] 새 작업 파일 감지: {file_path.name}")

        try:
            # 파일이 완전히 쓰여질 때까지 대기 (짧은 지연)
            time.sleep(0.1)

            # 작업 파일 읽기
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                task = TaskContext(**data)

            if self.process_immediately:
                # 즉시 처리 (비동기 실행)
                asyncio.create_task(self._process_task(task, file_path))
            else:
                # 큐에 추가
                self.pending_tasks.append((task, file_path))
                print(f"📋 [{self.agent.agent_name}] 작업 큐에 추가: {task.task_id}")

        except Exception as e:
            print(f"❌ [{self.agent.agent_name}] 작업 파일 읽기 실패: {file_path.name} - {e}")

    async def _process_task(self, task: TaskContext, file_path: Path):
        """
        작업을 비동기로 처리

        Args:
            task: TaskContext
            file_path: 작업 파일 경로
        """
        try:
            print(f"⚙️  [{self.agent.agent_name}] 작업 실행 시작: {task.description}")

            # 작업 실행
            result = await self.agent.execute_task(task)

            # 결과 저장
            self.agent.write_result(result)

            # 작업 파일 삭제
            if file_path.exists():
                file_path.unlink()

            print(f"✅ [{self.agent.agent_name}] 작업 완료: {task.task_id} ({result.status.value})")

            # Handoff 처리
            if result.next_agent and result.next_task:
                import uuid

                next_task = TaskContext(
                    task_id=str(uuid.uuid4()),
                    agent=result.next_agent,
                    description=result.next_task,
                    created_by=self.agent.agent_name,
                    workflow_id=task.workflow_id,
                    depends_on=[task.task_id],
                    depends_on_results={task.task_id: result.output},
                )
                self.agent.dispatch_to_agent(result.next_agent, next_task)

        except Exception as e:
            print(f"❌ [{self.agent.agent_name}] 작업 실패: {task.task_id} - {e}")

            # 에러 결과 저장
            from agent_base import TaskResult, TaskStatus

            error_result = TaskResult(
                task_id=task.task_id, status=TaskStatus.FAILED, error_message=str(e)
            )
            self.agent.write_result(error_result)

            # 작업 파일 삭제
            if file_path.exists():
                file_path.unlink()


# ============================================================================
# INBOX Watcher
# ============================================================================


class InboxWatcher:
    """
    에이전트 INBOX 폴더를 모니터링하고 새 작업을 자동 처리
    """

    def __init__(self, agent: AgentBase, process_immediately: bool = True):
        """
        Args:
            agent: AgentBase 인스턴스
            process_immediately: True이면 파일 감지 즉시 처리
        """
        self.agent = agent
        self.observer = Observer()
        self.handler = InboxFileHandler(agent, process_immediately)
        self.running = False

    def start(self):
        """Watcher 시작"""
        if self.running:
            print(f"⚠️  [{self.agent.agent_name}] Watcher already running")
            return

        # Observer 설정
        self.observer.schedule(self.handler, path=str(self.agent.inbox_path), recursive=False)

        # 시작
        self.observer.start()
        self.running = True

        print(f"👁️  [{self.agent.agent_name}] INBOX Watcher 시작: {self.agent.inbox_path}")
        print(f"    모드: {'즉시 처리' if self.handler.process_immediately else '큐 방식'}")

    def stop(self):
        """Watcher 중지"""
        if not self.running:
            return

        self.observer.stop()
        self.observer.join(timeout=5)
        self.running = False

        print(f"🛑 [{self.agent.agent_name}] INBOX Watcher 중지")

    def run_forever(self):
        """
        Watcher를 지속 실행 (블로킹)

        Ctrl+C로 중지
        """
        self.start()

        try:
            print(f"\n⏳ [{self.agent.agent_name}] 작업 대기 중... (Ctrl+C로 중지)")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"\n\n🛑 [{self.agent.agent_name}] 종료 신호 수신")
            self.stop()

    async def run_forever_async(self):
        """
        Watcher를 지속 실행 (비동기, 논블로킹)
        """
        self.start()

        try:
            print(f"\n⏳ [{self.agent.agent_name}] 작업 대기 중... (비동기 모드)")
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            print(f"\n\n🛑 [{self.agent.agent_name}] 종료 신호 수신")
            self.stop()


# ============================================================================
# 다중 에이전트 Watcher
# ============================================================================


class MultiAgentWatcher:
    """
    여러 에이전트의 INBOX를 동시에 모니터링
    """

    def __init__(self, agents: list[AgentBase]):
        """
        Args:
            agents: AgentBase 인스턴스 리스트
        """
        self.agents = agents
        self.watchers = [InboxWatcher(agent) for agent in agents]

    def start_all(self):
        """모든 Watcher 시작"""
        for watcher in self.watchers:
            watcher.start()

        print(f"\n✅ {len(self.watchers)}개 에이전트 Watcher 시작 완료")

    def stop_all(self):
        """모든 Watcher 중지"""
        for watcher in self.watchers:
            watcher.stop()

        print("\n🛑 모든 Watcher 중지 완료")

    def run_forever(self):
        """
        모든 Watcher를 지속 실행 (블로킹)

        Ctrl+C로 중지
        """
        self.start_all()

        try:
            print("\n⏳ Multi-Agent 시스템 실행 중... (Ctrl+C로 중지)\n")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n🛑 종료 신호 수신")
            self.stop_all()

    async def run_forever_async(self):
        """
        모든 Watcher를 지속 실행 (비동기)
        """
        self.start_all()

        try:
            print("\n⏳ Multi-Agent 시스템 실행 중... (비동기 모드)\n")

            # 모든 watcher를 비동기로 실행
            tasks = [watcher.run_forever_async() for watcher in self.watchers]
            await asyncio.gather(*tasks)

        except asyncio.CancelledError:
            print("\n\n🛑 종료 신호 수신")
            self.stop_all()


# ============================================================================
# 편의 함수
# ============================================================================


def watch_agent(agent: AgentBase, process_immediately: bool = True):
    """
    단일 에이전트 INBOX 모니터링 시작 (블로킹)

    Args:
        agent: AgentBase 인스턴스
        process_immediately: True이면 파일 감지 즉시 처리
    """
    watcher = InboxWatcher(agent, process_immediately)
    watcher.run_forever()


async def watch_agent_async(agent: AgentBase, process_immediately: bool = True):
    """
    단일 에이전트 INBOX 모니터링 시작 (비동기)

    Args:
        agent: AgentBase 인스턴스
        process_immediately: True이면 파일 감지 즉시 처리
    """
    watcher = InboxWatcher(agent, process_immediately)
    await watcher.run_forever_async()


def watch_all_agents(agents: list[AgentBase]):
    """
    여러 에이전트 INBOX 모니터링 시작 (블로킹)

    Args:
        agents: AgentBase 인스턴스 리스트
    """
    multi_watcher = MultiAgentWatcher(agents)
    multi_watcher.run_forever()


async def watch_all_agents_async(agents: list[AgentBase]):
    """
    여러 에이전트 INBOX 모니터링 시작 (비동기)

    Args:
        agents: AgentBase 인스턴스 리스트
    """
    multi_watcher = MultiAgentWatcher(agents)
    await multi_watcher.run_forever_async()
