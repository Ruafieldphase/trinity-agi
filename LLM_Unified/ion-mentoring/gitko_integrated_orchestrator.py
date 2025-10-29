"""
Gitko Integrated Orchestrator - 기존 구조 통합 버전
====================================================

기존 시스템 통합:
1. naeda-ai-core: /dispatch-agent-task 패턴 (자연어 → JSON → INBOX)
2. orchestrator_main: TaskDefinition, TaskExecution, State Management
3. local_file_agent: CLI 도구 통합, Context Storage
4. LangGraph: Send() 기반 병렬 디스패치

목표: Gitko가 대화 중 자동으로 작업을 감지하고 기존 인프라를 활용하여 실행
"""

import asyncio
import json
import subprocess
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Literal, Optional

# ============================================================================
# 1. 기존 orchestrator_main의 TaskDefinition/TaskStatus 재사용
# ============================================================================


class TaskStatus(Enum):
    """작업 상태 (orchestrator_main과 동일)"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class AgentType(Enum):
    """에이전트 타입"""

    GITKO = "gitko"  # 직접 구현
    LUBIT = "lubit"  # 리뷰/검증
    SIAN = "sian"  # 리팩터링/개선
    PARALLEL = "parallel"  # Lubit + Sian 병렬


@dataclass
class TaskContext:
    """작업 컨텍스트 (naeda-ai-core의 AgentTaskRequest와 유사)"""

    task_id: str = field(
        default_factory=lambda: f"task_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')}"
    )
    task_type: Literal["review", "refactor", "parallel", "none"] = "none"
    description: str = ""
    confidence: float = 0.0
    files_mentioned: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    agent: AgentType = AgentType.GITKO

    # orchestrator_main과의 통합
    status: TaskStatus = TaskStatus.PENDING
    max_retries: int = 2
    timeout_seconds: int = 120

    # 실행 메타데이터
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


@dataclass
class DispatchResult:
    """작업 실행 결과 (orchestrator_main의 TaskExecution과 유사)"""

    task_id: str
    agent: str
    status: Literal["success", "error", "timeout"]
    artifacts: List[Path] = field(default_factory=list)
    summary: str = ""
    elapsed_ms: int = 0
    error_message: Optional[str] = None

    # orchestrator_main 통합
    execution_id: str = field(default_factory=lambda: f"exec_{uuid.uuid4().hex[:8]}")
    retry_count: int = 0


# ============================================================================
# 2. INBOX 기반 작업 디스패치 (naeda-ai-core 패턴)
# ============================================================================


class AgentInboxDispatcher:
    """
    naeda-ai-core의 /dispatch-agent-task 패턴을 로컬에서 구현
    - 자연어 설명 → JSON 변환
    - INBOX에 작업 파일 생성
    - 에이전트가 INBOX를 모니터링하여 작업 수행
    """

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root

        # local_file_agent의 CONTEXT_STORAGE 패턴 활용
        self.inbox_path = repo_root / "LLM_Unified" / "agent_inbox_local"
        self.inbox_path.mkdir(parents=True, exist_ok=True)

        self.outputs_path = repo_root / "outputs"
        self.outputs_path.mkdir(parents=True, exist_ok=True)

        self.scripts_path = repo_root / "scripts"

    def create_task_json(self, task_ctx: TaskContext) -> Path:
        """
        작업 컨텍스트를 JSON 파일로 변환하여 INBOX에 저장
        (naeda-ai-core의 dispatch_agent_task 로직)
        """
        task_json = {
            "task_id": task_ctx.task_id,
            "action": f"DISPATCH_{task_ctx.agent.value.upper()}",
            "payload": {
                "task_type": task_ctx.task_type,
                "description": task_ctx.description,
                "confidence": task_ctx.confidence,
                "files": task_ctx.files_mentioned,
                "keywords": task_ctx.keywords,
                "max_retries": task_ctx.max_retries,
                "timeout_seconds": task_ctx.timeout_seconds,
            },
            "metadata": {"created_at": task_ctx.created_at, "status": task_ctx.status.value},
        }

        task_file = self.inbox_path / f"{task_ctx.task_id}.json"
        with open(task_file, "w", encoding="utf-8") as f:
            json.dump(task_json, f, ensure_ascii=False, indent=2)

        return task_file

    async def dispatch_to_inbox(self, task_ctx: TaskContext) -> Path:
        """INBOX에 작업 파일 생성 (비동기)"""
        return await asyncio.to_thread(self.create_task_json, task_ctx)

    def check_task_completion(self, task_id: str) -> Optional[DispatchResult]:
        """
        INBOX에서 완료된 작업 결과 확인
        (에이전트가 작업 완료 시 {task_id}_result.json 생성한다고 가정)
        """
        result_file = self.inbox_path / f"{task_id}_result.json"
        if not result_file.exists():
            return None

        with open(result_file, "r", encoding="utf-8") as f:
            result_data = json.load(f)

        return DispatchResult(
            task_id=task_id,
            agent=result_data.get("agent", "unknown"),
            status=result_data.get("status", "error"),
            artifacts=[Path(p) for p in result_data.get("artifacts", [])],
            summary=result_data.get("summary", ""),
            elapsed_ms=result_data.get("elapsed_ms", 0),
            error_message=result_data.get("error_message"),
        )


# ============================================================================
# 3. PowerShell 스크립트 실행기 (기존 스크립트 활용)
# ============================================================================


class PowerShellScriptExecutor:
    """
    기존 PowerShell 스크립트를 실행하는 어댑터
    (gitko_auto_dispatch.ps1, dispatch_to_lubit_and_sian.ps1 등)
    """

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.scripts_dir = repo_root / "scripts"
        self.outputs_dir = repo_root / "outputs"

    async def execute_script(
        self, script_name: str, args: List[str], timeout: int = 120
    ) -> DispatchResult:
        """PowerShell 스크립트 실행"""
        start = datetime.now(timezone.utc)
        script_path = self.scripts_dir / script_name

        cmd = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script_path),
        ] + args

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                # PowerShell 인코딩 문제 해결
                creationflags=(
                    subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
                ),
            )

            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)

            elapsed = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)

            # 인코딩 안전하게 처리
            try:
                stdout.decode("utf-8", errors="replace")
                stderr_text = stderr.decode("utf-8", errors="replace")
            except Exception:
                str(stdout)
                stderr_text = str(stderr)

            # 생성된 아티팩트 검색
            artifacts = list(self.outputs_dir.glob("*"))
            recent_artifacts = sorted(artifacts, key=lambda p: p.stat().st_mtime, reverse=True)[
                :5
            ]  # 최근 5개

            return DispatchResult(
                task_id=f"ps_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
                agent=script_name.replace(".ps1", ""),
                status="success" if proc.returncode == 0 else "error",
                artifacts=recent_artifacts,
                summary=f"Script {script_name} completed",
                elapsed_ms=elapsed,
                error_message=stderr_text if proc.returncode != 0 else None,
            )

        except asyncio.TimeoutError:
            return DispatchResult(
                task_id=f"ps_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
                agent=script_name.replace(".ps1", ""),
                status="timeout",
                summary=f"Script {script_name} timed out after {timeout}s",
                elapsed_ms=timeout * 1000,
            )
        except Exception as e:
            return DispatchResult(
                task_id=f"ps_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
                agent=script_name.replace(".ps1", ""),
                status="error",
                summary=f"Script execution failed: {str(e)}",
                elapsed_ms=0,
                error_message=str(e),
            )


# ============================================================================
# 4. 통합 오케스트레이터 (LangGraph Send() 패턴)
# ============================================================================


class GitkoIntegratedOrchestrator:
    """
    모든 기존 구조를 통합한 중앙 오케스트레이터

    통합 요소:
    - orchestrator_main: 작업 상태 관리
    - naeda-ai-core: INBOX 기반 디스패치
    - local_file_agent: CLI 도구 및 Context Storage
    - gitko_auto_dispatch.ps1: 기존 PowerShell 로직
    """

    def __init__(self, repo_root: Path, use_inbox: bool = True, use_powershell: bool = True):
        self.repo_root = repo_root
        self.use_inbox = use_inbox
        self.use_powershell = use_powershell

        # 기존 시스템 통합
        self.inbox_dispatcher = AgentInboxDispatcher(repo_root)
        self.ps_executor = PowerShellScriptExecutor(repo_root)

        # 작업 추적 (orchestrator_main 패턴)
        self.active_tasks: Dict[str, TaskContext] = {}
        self.pending_results: Dict[str, asyncio.Task] = {}

    async def dispatch_task(self, task_ctx: TaskContext) -> str:
        """
        작업 디스패치 (LangGraph Send() 패턴)

        두 가지 실행 방식:
        1. INBOX 기반 (naeda-ai-core 패턴): 느슨한 결합, 에이전트가 독립 실행
        2. PowerShell 직접 실행: 빠른 피드백, 기존 스크립트 활용
        """
        self.active_tasks[task_ctx.task_id] = task_ctx
        task_ctx.status = TaskStatus.RUNNING
        task_ctx.started_at = datetime.now(timezone.utc).isoformat()

        if self.use_inbox:
            # INBOX 방식: 작업 파일 생성
            await self.inbox_dispatcher.dispatch_to_inbox(task_ctx)
            # 에이전트가 백그라운드에서 처리하도록 대기
            result_task = asyncio.create_task(
                self._wait_for_inbox_result(task_ctx.task_id, task_ctx.timeout_seconds)
            )
        else:
            # PowerShell 직접 실행
            result_task = asyncio.create_task(self._execute_powershell_task(task_ctx))

        self.pending_results[task_ctx.task_id] = result_task
        return task_ctx.task_id

    async def _wait_for_inbox_result(self, task_id: str, timeout: int) -> DispatchResult:
        """INBOX에서 결과 폴링"""
        start = datetime.now(timezone.utc)
        poll_interval = 2  # 2초마다 체크

        while (datetime.now(timezone.utc) - start).total_seconds() < timeout:
            result = self.inbox_dispatcher.check_task_completion(task_id)
            if result:
                return result
            await asyncio.sleep(poll_interval)

        # 타임아웃
        return DispatchResult(
            task_id=task_id,
            agent="inbox_timeout",
            status="timeout",
            summary=f"Task did not complete within {timeout}s",
            elapsed_ms=timeout * 1000,
        )

    async def _execute_powershell_task(self, task_ctx: TaskContext) -> DispatchResult:
        """PowerShell 스크립트 직접 실행"""
        # 에이전트 타입에 따라 적절한 스크립트 선택
        script_map = {
            AgentType.LUBIT: "prepare_lubit_review_packet.ps1",
            AgentType.SIAN: None,  # Python 도구 사용
            AgentType.PARALLEL: "dispatch_to_lubit_and_sian.ps1",
            AgentType.GITKO: "gitko_auto_dispatch.ps1",
        }

        script_name = script_map.get(task_ctx.agent)

        if script_name:
            # 스크립트별 파라미터 매핑
            if script_name == "dispatch_to_lubit_and_sian.ps1":
                args = ["-Issue", task_ctx.description]
            else:
                args = ["-WorkRequest", task_ctx.description]

            return await self.ps_executor.execute_script(
                script_name, args, task_ctx.timeout_seconds
            )
        else:
            # Python 도구 실행 (Sian의 경우)
            return await self._execute_python_tool(task_ctx)

    async def _execute_python_tool(self, task_ctx: TaskContext) -> DispatchResult:
        """Python 도구 실행 (gemini_code_assist_poc.py 등)"""
        start = datetime.now(timezone.utc)
        tool_script = self.repo_root / "tools" / "gemini_code_assist_poc.py"
        venv_python = self.repo_root / "LLM_Unified" / ".venv" / "Scripts" / "python.exe"

        python_exe = str(venv_python) if venv_python.exists() else "python"
        out_file = self.inbox_dispatcher.outputs_path / f"sian_{task_ctx.task_id}.md"

        cmd = [
            python_exe,
            str(tool_script),
            "--issue",
            task_ctx.description,
            "--out",
            str(out_file),
        ]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=task_ctx.timeout_seconds
            )

            elapsed = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)

            return DispatchResult(
                task_id=task_ctx.task_id,
                agent="sian",
                status="success" if proc.returncode == 0 else "error",
                artifacts=[out_file] if out_file.exists() else [],
                summary="Python tool completed",
                elapsed_ms=elapsed,
                error_message=stderr.decode() if proc.returncode != 0 else None,
            )

        except asyncio.TimeoutError:
            return DispatchResult(
                task_id=task_ctx.task_id,
                agent="sian",
                status="timeout",
                summary="Python tool timed out",
                elapsed_ms=task_ctx.timeout_seconds * 1000,
            )

    async def get_result(self, task_id: str, timeout: float = 5.0) -> Optional[DispatchResult]:
        """작업 결과 확인 (타임아웃 내에 완료되면 반환)"""
        if task_id not in self.pending_results:
            return None

        result_task = self.pending_results[task_id]

        try:
            result = await asyncio.wait_for(result_task, timeout=timeout)

            # 작업 완료 처리
            if task_id in self.active_tasks:
                self.active_tasks[task_id].status = TaskStatus.COMPLETED
                self.active_tasks[task_id].completed_at = datetime.now(timezone.utc).isoformat()

            del self.pending_results[task_id]
            return result

        except asyncio.TimeoutError:
            return None  # 아직 진행 중

    def format_result_summary(self, result: DispatchResult) -> str:
        """결과를 대화용 텍스트로 포맷"""
        lines = [
            f"## 🤖 {result.agent.upper()} 에이전트 작업 완료",
            "",
            f"**상태**: {result.status}",
            f"**소요 시간**: {result.elapsed_ms}ms",
            f"**요약**: {result.summary}",
        ]

        if result.artifacts:
            lines.append("")
            lines.append("**생성된 파일**:")
            for artifact in result.artifacts:
                lines.append(f"- `{artifact.name}`")

        if result.error_message:
            lines.append("")
            lines.append("**오류**:")
            lines.append(f"```\n{result.error_message}\n```")

        return "\n".join(lines)


# ============================================================================
# 5. 대화 분석기 (기존 ConversationAnalyzer 개선)
# ============================================================================


class IntegratedConversationAnalyzer:
    """
    대화 컨텍스트 분석 (기존 패턴 유지 + 향상)
    """

    PATTERNS = {
        "review": [
            r"\b(review|validate|check|audit|inspect|verify)\b",
            r"(리뷰|검토|확인|검증|점검|검사)",
        ],
        "refactor": [
            r"\b(refactor|optimize|improve|enhance|modernize)\b",
            r"(개선|리팩터|최적화|성능|향상)",
        ],
        "parallel": [
            r"\b(review.*improve|improve.*review)\b",
            r"(리뷰.*개선|개선.*리뷰)",
            r"\b(both|comprehensive|thorough)\b",
            r"(전체|종합|포괄)",
        ],
    }

    def __init__(self, confidence_threshold: float = 0.6):
        self.threshold = confidence_threshold

    def analyze(self, message: str, context: Optional[str] = None) -> TaskContext:
        """대화 분석 → TaskContext 생성"""
        import re

        full_text = f"{message} {context or ''}".lower()

        scores = {"review": 0.0, "refactor": 0.0, "parallel": 0.0}
        matched_keywords = []

        for task_type, patterns in self.PATTERNS.items():
            for pattern in patterns:
                matches = re.findall(pattern, full_text, re.IGNORECASE)
                if matches:
                    scores[task_type] += len(matches) * 0.5  # 0.3 → 0.5로 증가
                    matched_keywords.extend(matches)

        # 점수 정규화
        for task_type in scores:
            scores[task_type] = min(scores[task_type], 1.0)

        # 작업 타입 결정
        if scores["parallel"] > self.threshold:
            task_type = "parallel"
            confidence = scores["parallel"]
            agent = AgentType.PARALLEL
        elif scores["review"] > self.threshold and scores["refactor"] > self.threshold:
            task_type = "parallel"
            confidence = (scores["review"] + scores["refactor"]) / 2
            agent = AgentType.PARALLEL
        elif scores["review"] > self.threshold:
            task_type = "review"
            confidence = scores["review"]
            agent = AgentType.LUBIT
        elif scores["refactor"] > self.threshold:
            task_type = "refactor"
            confidence = scores["refactor"]
            agent = AgentType.SIAN
        else:
            task_type = "none"
            confidence = 0.0
            agent = AgentType.GITKO

        # 파일 패턴 추출
        file_pattern = r"[a-zA-Z0-9_\-/\\]+\.(?:py|js|ts|md|json|ps1)"
        files_mentioned = re.findall(file_pattern, full_text)

        return TaskContext(
            task_type=task_type,
            description=message[:200],
            confidence=confidence,
            files_mentioned=list(set(files_mentioned)),
            keywords=list(set(matched_keywords)),
            agent=agent,
        )


# ============================================================================
# 6. 테스트 및 사용 예시
# ============================================================================


async def test_integrated_orchestrator():
    """통합 오케스트레이터 테스트"""

    repo_root = Path("d:/nas_backup")

    # 1. 오케스트레이터 초기화
    orchestrator = GitkoIntegratedOrchestrator(
        repo_root=repo_root, use_inbox=False, use_powershell=True  # PowerShell 직접 실행 모드
    )

    # 2. 분석기 초기화
    analyzer = IntegratedConversationAnalyzer(confidence_threshold=0.6)

    # 3. 테스트 메시지들
    test_messages = [
        "Please review the deployment scripts and suggest improvements",
        "배포 스크립트를 검토해주세요",
        "코드 성능을 개선해주세요",
    ]

    for msg in test_messages:
        print(f"\n{'='*60}")
        print(f"메시지: {msg}")
        print(f"{'='*60}")

        # 분석
        task_ctx = analyzer.analyze(msg)
        print(f"감지된 작업: {task_ctx.task_type}")
        print(f"신뢰도: {task_ctx.confidence:.0%}")
        print(f"에이전트: {task_ctx.agent.value}")

        if task_ctx.task_type != "none":
            # 디스패치
            print("\n작업 디스패치 중...")
            task_id = await orchestrator.dispatch_task(task_ctx)

            # 결과 대기 (최대 5초)
            result = await orchestrator.get_result(task_id, timeout=5.0)

            if result:
                print(f"\n{orchestrator.format_result_summary(result)}")
            else:
                print("\n⏳ 작업이 백그라운드에서 계속 실행 중입니다...")


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_integrated_orchestrator())
