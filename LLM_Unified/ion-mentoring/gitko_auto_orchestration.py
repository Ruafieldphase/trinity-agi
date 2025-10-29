"""
Gitko Auto-Orchestration Engine
================================

Deep integration layer that allows Gitko to automatically orchestrate Lubit and Sian
during conversation flow without explicit user commands.

Based on AGI patterns from:
- LangGraph multi-agent supervisor/orchestrator-worker
- naeda-ai-core dispatch system
- AutoGPT autonomous task execution

Key Capabilities:
- Context-aware task detection
- Async background dispatch
- Result integration into conversation flow
- No user intervention required
"""

import asyncio
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Literal, Optional


@dataclass
class TaskContext:
    """Represents a detected task from conversation analysis"""

    task_type: Literal["review", "refactor", "parallel", "none"]
    description: str
    confidence: float  # 0.0 to 1.0
    files_mentioned: List[str]
    keywords: List[str]


@dataclass
class DispatchResult:
    """Result from background task execution"""

    agent: str  # lubit, sian, parallel
    status: Literal["success", "error", "timeout"]
    artifacts: List[Path]
    summary: str
    elapsed_ms: int


class ConversationAnalyzer:
    """Analyzes conversation context to detect orchestration opportunities"""

    # Pattern definitions based on actual work keywords
    PATTERNS = {
        "review": [
            r"\b(review|validate|check|audit|inspect|verify)\b",
            r"\b(문서|리뷰|검토|확인|검증|점검)\b",
        ],
        "refactor": [
            r"\b(refactor|optimize|improve|enhance|modernize)\b",
            r"\b(개선|리팩터|최적화|성능)\b",
        ],
        "parallel": [
            r"\b(review.*improve|improve.*review)\b",
            r"\b(리뷰.*개선|개선.*리뷰)\b",
            r"\b(both|comprehensive|thorough)\b",
        ],
    }

    def __init__(self, threshold: float = 0.6):
        """
        Args:
            threshold: Minimum confidence score to trigger auto-dispatch
        """
        self.threshold = threshold

    def analyze(self, message: str, context: Optional[str] = None) -> TaskContext:
        """
        Analyze a user message to detect potential orchestration needs.

        Args:
            message: User's message text
            context: Optional additional context (file paths, error messages, etc.)

        Returns:
            TaskContext with detected task type and confidence
        """
        full_text = f"{message} {context or ''}".lower()

        scores = {"review": 0.0, "refactor": 0.0, "parallel": 0.0}

        matched_keywords = []

        # Score each pattern type
        for task_type, patterns in self.PATTERNS.items():
            for pattern in patterns:
                matches = re.findall(pattern, full_text, re.IGNORECASE)
                if matches:
                    scores[task_type] += len(matches) * 0.3
                    matched_keywords.extend(matches)

        # Normalize scores
        for task_type in scores:
            scores[task_type] = min(scores[task_type], 1.0)

        # Determine task type
        if scores["parallel"] > self.threshold:
            task_type = "parallel"
            confidence = scores["parallel"]
        elif scores["review"] > self.threshold and scores["refactor"] > self.threshold:
            task_type = "parallel"
            confidence = (scores["review"] + scores["refactor"]) / 2
        elif scores["review"] > self.threshold:
            task_type = "review"
            confidence = scores["review"]
        elif scores["refactor"] > self.threshold:
            task_type = "refactor"
            confidence = scores["refactor"]
        else:
            task_type = "none"
            confidence = 0.0

        # Extract file mentions
        file_pattern = r"[a-zA-Z0-9_\-/\\]+\.(?:py|js|ts|md|json|ps1)"
        files_mentioned = re.findall(file_pattern, full_text)

        return TaskContext(
            task_type=task_type,
            description=message[:200],  # truncate for summary
            confidence=confidence,
            files_mentioned=list(set(files_mentioned)),
            keywords=list(set(matched_keywords)),
        )


class BackgroundDispatcher:
    """Handles async dispatch of Lubit/Sian tasks without blocking conversation"""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.scripts_dir = repo_root / "scripts"
        self.outputs_dir = repo_root / "outputs"

    async def dispatch_review(self, context: TaskContext) -> DispatchResult:
        """Dispatch Lubit review packet generation"""
        start = datetime.now(timezone.utc)
        script = self.scripts_dir / "prepare_lubit_review_packet.ps1"

        try:
            proc = await asyncio.create_subprocess_exec(
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60.0)

            # Find generated artifacts
            artifacts = list(self.outputs_dir.glob("review_packet_*"))

            elapsed = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)

            return DispatchResult(
                agent="lubit",
                status="success" if proc.returncode == 0 else "error",
                artifacts=artifacts[-2:] if artifacts else [],  # latest folder + zip
                summary=f"Review packet prepared: {len(artifacts)} artifacts",
                elapsed_ms=elapsed,
            )
        except asyncio.TimeoutError:
            return DispatchResult(
                agent="lubit",
                status="timeout",
                artifacts=[],
                summary="Review packet generation timed out after 60s",
                elapsed_ms=60000,
            )

    async def dispatch_refactor(self, context: TaskContext, issue: str) -> DispatchResult:
        """Dispatch Sian code assist generation"""
        start = datetime.now(timezone.utc)
        poc_script = self.repo_root / "tools" / "gemini_code_assist_poc.py"
        venv_python = self.repo_root / "LLM_Unified" / ".venv" / "Scripts" / "python.exe"

        python_exe = str(venv_python) if venv_python.exists() else "python"

        try:
            proc = await asyncio.create_subprocess_exec(
                python_exe,
                str(poc_script),
                "--issue",
                issue,
                "--out",
                str(
                    self.outputs_dir
                    / f"sian_auto_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}Z.md"
                ),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=90.0)

            artifacts = sorted(
                self.outputs_dir.glob("sian_auto_*.md"), key=lambda p: p.stat().st_mtime
            )

            elapsed = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)

            return DispatchResult(
                agent="sian",
                status="success" if proc.returncode == 0 else "error",
                artifacts=artifacts[-1:] if artifacts else [],
                summary=f"Code assist generated: {artifacts[-1].name if artifacts else 'none'}",
                elapsed_ms=elapsed,
            )
        except asyncio.TimeoutError:
            return DispatchResult(
                agent="sian",
                status="timeout",
                artifacts=[],
                summary="Code assist generation timed out after 90s",
                elapsed_ms=90000,
            )

    async def dispatch_parallel(self, context: TaskContext, issue: str) -> DispatchResult:
        """Dispatch both Lubit + Sian in parallel"""
        start = datetime.now(timezone.utc)
        script = self.scripts_dir / "dispatch_to_lubit_and_sian.ps1"

        try:
            proc = await asyncio.create_subprocess_exec(
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script),
                "-Issue",
                issue,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120.0)

            # Find all recent artifacts
            review_artifacts = sorted(
                self.outputs_dir.glob("review_packet_*"), key=lambda p: p.stat().st_mtime
            )[-2:]
            sian_artifacts = sorted(
                self.outputs_dir.glob("gemini_assist_*.md"), key=lambda p: p.stat().st_mtime
            )[-1:]
            summary_artifacts = sorted(
                self.outputs_dir.glob("collaboration_summary_*.md"), key=lambda p: p.stat().st_mtime
            )[-1:]

            all_artifacts = review_artifacts + sian_artifacts + summary_artifacts

            elapsed = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)

            return DispatchResult(
                agent="parallel",
                status="success" if proc.returncode == 0 else "error",
                artifacts=all_artifacts,
                summary=f"Parallel dispatch completed: {len(all_artifacts)} artifacts",
                elapsed_ms=elapsed,
            )
        except asyncio.TimeoutError:
            return DispatchResult(
                agent="parallel",
                status="timeout",
                artifacts=[],
                summary="Parallel dispatch timed out after 120s",
                elapsed_ms=120000,
            )


class GitkoOrchestrator:
    """
    Main orchestration engine for Gitko's autonomous agent coordination.

    Usage in conversation flow:
    1. Gitko receives user message
    2. Analyzer detects orchestration opportunity
    3. If confidence > threshold, auto-dispatch in background
    4. Continue conversation immediately (non-blocking)
    5. When results ready, integrate into next response
    """

    def __init__(
        self, repo_root: Path, auto_dispatch: bool = True, confidence_threshold: float = 0.7
    ):
        self.analyzer = ConversationAnalyzer(threshold=confidence_threshold)
        self.dispatcher = BackgroundDispatcher(repo_root)
        self.auto_dispatch = auto_dispatch
        self.pending_tasks: Dict[str, asyncio.Task] = {}

    def should_orchestrate(
        self, message: str, context: Optional[str] = None
    ) -> tuple[bool, TaskContext]:
        """
        Determine if orchestration should happen for this message.

        Returns:
            (should_dispatch, task_context)
        """
        task_ctx = self.analyzer.analyze(message, context)
        should_dispatch = (
            self.auto_dispatch
            and task_ctx.task_type != "none"
            and task_ctx.confidence >= self.analyzer.threshold
        )
        return should_dispatch, task_ctx

    async def orchestrate_async(self, task_ctx: TaskContext) -> DispatchResult:
        """
        Execute orchestration based on detected task type.
        Non-blocking - returns immediately and runs in background.
        """
        if task_ctx.task_type == "review":
            return await self.dispatcher.dispatch_review(task_ctx)
        elif task_ctx.task_type == "refactor":
            return await self.dispatcher.dispatch_refactor(task_ctx, task_ctx.description)
        elif task_ctx.task_type == "parallel":
            return await self.dispatcher.dispatch_parallel(task_ctx, task_ctx.description)
        else:
            raise ValueError(f"Unknown task type: {task_ctx.task_type}")

    def dispatch_background(self, task_id: str, task_ctx: TaskContext) -> None:
        """
        Start background orchestration task (fire-and-forget).

        Args:
            task_id: Unique identifier for this task
            task_ctx: Detected task context
        """
        if task_id in self.pending_tasks:
            return  # already dispatched

        task = asyncio.create_task(self.orchestrate_async(task_ctx))
        self.pending_tasks[task_id] = task

    async def get_result(self, task_id: str, timeout: float = 5.0) -> Optional[DispatchResult]:
        """
        Get result of a background task if completed within timeout.

        Args:
            task_id: Task identifier
            timeout: Max seconds to wait for completion

        Returns:
            DispatchResult if ready, None if still pending
        """
        if task_id not in self.pending_tasks:
            return None

        task = self.pending_tasks[task_id]

        try:
            result = await asyncio.wait_for(task, timeout=timeout)
            del self.pending_tasks[task_id]
            return result
        except asyncio.TimeoutError:
            return None  # still running

    def format_result_summary(self, result: DispatchResult) -> str:
        """Format dispatch result for inclusion in conversation"""
        lines = [
            f"[Background Task: {result.agent.upper()}]",
            f"Status: {result.status}",
            f"Time: {result.elapsed_ms}ms",
            f"Summary: {result.summary}",
        ]

        if result.artifacts:
            lines.append("Artifacts:")
            for artifact in result.artifacts:
                lines.append(f"  - {artifact.name}")

        return "\n".join(lines)


# Example integration into Gitko's conversation loop:
"""
# In Gitko's main response handler:

orchestrator = GitkoOrchestrator(
    repo_root=Path('d:/nas_backup'),
    auto_dispatch=True,
    confidence_threshold=0.7
)

def handle_user_message(user_msg: str, conversation_context: str) -> str:
    # 1. Check if orchestration needed
    should_dispatch, task_ctx = orchestrator.should_orchestrate(user_msg, conversation_context)

    task_id = None
    if should_dispatch:
        # 2. Start background task immediately
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        orchestrator.dispatch_background(task_id, task_ctx)

        # 3. Inform user (optional)
        print(f"[Gitko] Detected {task_ctx.task_type} opportunity (confidence: {task_ctx.confidence:.0%})")
        print(f"[Gitko] Dispatching to {task_ctx.task_type} agent in background...")

    # 4. Continue with main response (non-blocking!)
    gitko_response = generate_gitko_response(user_msg)

    # 5. Try to get result if ready quickly
    if task_id:
        result = await orchestrator.get_result(task_id, timeout=2.0)
        if result:
            gitko_response += "\n\n" + orchestrator.format_result_summary(result)
        else:
            gitko_response += "\n\n[Orchestration in progress, will integrate results in next response]"

    return gitko_response
"""

if __name__ == "__main__":
    # Quick test
    import asyncio

    async def test():
        orch = GitkoOrchestrator(repo_root=Path("d:/nas_backup"), auto_dispatch=True)

        test_messages = [
            "Please review the deployment scripts",
            "Suggest refactoring for better performance",
            "Review code and propose improvements",
            "Fix the bug in auth module",  # should not trigger
        ]

        for msg in test_messages:
            should, ctx = orch.should_orchestrate(msg)
            print(f"\nMessage: {msg}")
            print(f"  Should dispatch: {should}")
            print(f"  Task type: {ctx.task_type}")
            print(f"  Confidence: {ctx.confidence:.0%}")
            print(f"  Keywords: {ctx.keywords}")

    asyncio.run(test())
