"""
Agent Extended Tools - PowerShell 스크립트 통합
================================================

목적:
1. 기존 270개 PowerShell 스크립트를 에이전트 작업으로 활용
2. run_powershell_script 도구
3. 스크립트 실행 결과를 TaskResult로 변환

통합:
- agent_base.TaskContext, TaskResult
- 기존 PowerShell 스크립트들
"""

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent_base import TaskContext, TaskResult, TaskStatus

# ============================================================================
# PowerShell 스크립트 경로
# ============================================================================

REPO_ROOT = Path(__file__).parent.parent.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts"
ION_SCRIPTS = REPO_ROOT / "LLM_Unified" / "ion-mentoring" / "scripts"


# ============================================================================
# PowerShell 도구
# ============================================================================


@dataclass
class PowerShellScriptTool:
    """PowerShell 스크립트 도구 정의"""

    name: str
    script_path: Path
    description: str
    default_args: Optional[Dict[str, Any]] = None


async def run_powershell_script(
    script_path: Path,
    args: Optional[Dict[str, Any]] = None,
    timeout_seconds: int = 300,
    capture_output: bool = True,
) -> TaskResult:
    """
    PowerShell 스크립트를 비동기로 실행하고 결과 반환

    Args:
        script_path: 스크립트 파일 경로
        args: 스크립트 인자 딕셔너리
        timeout_seconds: 타임아웃 (초)
        capture_output: True이면 출력 캡처, False이면 실시간 출력

    Returns:
        TaskResult 객체

    Example:
        >>> result = await run_powershell_script(
        ...     Path("scripts/deploy.ps1"),
        ...     args={"CanaryPercentage": 5, "ProjectId": "my-project"}
        ... )
    """
    import uuid

    task_id = str(uuid.uuid4())

    if not script_path.exists():
        return TaskResult(
            task_id=task_id,
            status=TaskStatus.FAILED,
            error_message=f"Script not found: {script_path}",
        )

    # PowerShell 명령어 구성
    cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script_path)]

    # 인자 추가
    if args:
        for key, value in args.items():
            cmd.extend([f"-{key}", str(value)])

    print(f"🔧 PowerShell 실행: {script_path.name}")
    if args:
        print(f"   인자: {args}")

    try:
        # 비동기 실행
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE if capture_output else None,
            stderr=asyncio.subprocess.PIPE if capture_output else None,
            cwd=str(script_path.parent),
        )

        # 타임아웃 적용
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout_seconds)

        # 결과 처리
        output = ""
        if capture_output:
            if stdout:
                output = stdout.decode("utf-8", errors="ignore")
            if stderr and process.returncode != 0:
                error_output = stderr.decode("utf-8", errors="ignore")
                output += f"\n\nErrors:\n{error_output}"

        # 성공/실패 판단
        if process.returncode == 0:
            return TaskResult(
                task_id=task_id,
                status=TaskStatus.COMPLETED,
                output=output.strip() if output else "스크립트 실행 완료",
                metrics={
                    "exit_code": process.returncode,
                    "script": str(script_path),
                },
            )
        else:
            return TaskResult(
                task_id=task_id,
                status=TaskStatus.FAILED,
                error_message=f"Exit code: {process.returncode}",
                error_details={
                    "exit_code": process.returncode,
                    "output": output.strip() if output else None,
                },
            )

    except asyncio.TimeoutError:
        return TaskResult(
            task_id=task_id,
            status=TaskStatus.FAILED,
            error_message=f"Timeout after {timeout_seconds}s",
        )

    except Exception as e:
        return TaskResult(task_id=task_id, status=TaskStatus.FAILED, error_message=str(e))


# ============================================================================
# 자주 사용하는 스크립트 도구들
# ============================================================================


def create_common_script_tools() -> List[PowerShellScriptTool]:
    """자주 사용하는 PowerShell 스크립트 도구 목록"""

    tools = []

    # 배포 관련
    deploy_script = ION_SCRIPTS / "deploy_phase4_canary.ps1"
    if deploy_script.exists():
        tools.append(
            PowerShellScriptTool(
                name="deploy_canary",
                script_path=deploy_script,
                description="Phase4 Canary 배포",
                default_args={"ProjectId": "naeda-genesis", "CanaryPercentage": 5},
            )
        )

    # 롤백 관련
    rollback_script = ION_SCRIPTS / "rollback_phase4_canary.ps1"
    if rollback_script.exists():
        tools.append(
            PowerShellScriptTool(
                name="rollback_canary",
                script_path=rollback_script,
                description="Phase4 Canary 롤백",
                default_args={"ProjectId": "naeda-genesis"},
            )
        )

    # 모니터링 관련
    monitor_script = ION_SCRIPTS / "check_monitoring_status.ps1"
    if monitor_script.exists():
        tools.append(
            PowerShellScriptTool(
                name="check_monitoring",
                script_path=monitor_script,
                description="모니터링 상태 확인",
            )
        )

    # 테스트 관련
    test_script = ION_SCRIPTS / "compare_canary_vs_legacy.ps1"
    if test_script.exists():
        tools.append(
            PowerShellScriptTool(
                name="compare_endpoints",
                script_path=test_script,
                description="Canary vs Legacy 비교",
                default_args={"Method": "POST", "RequestsPerSide": 10},
            )
        )

    return tools


# ============================================================================
# 스크립트 검색
# ============================================================================


def find_scripts(pattern: str = "*.ps1") -> List[Path]:
    """
    PowerShell 스크립트 검색

    Args:
        pattern: 파일 패턴 (예: "deploy*.ps1")

    Returns:
        스크립트 경로 리스트
    """
    scripts = []

    # scripts/ 폴더
    if SCRIPTS_ROOT.exists():
        scripts.extend(SCRIPTS_ROOT.glob(pattern))

    # ion-mentoring/scripts/ 폴더
    if ION_SCRIPTS.exists():
        scripts.extend(ION_SCRIPTS.glob(pattern))

    return sorted(scripts)


def list_available_scripts() -> Dict[str, List[str]]:
    """
    사용 가능한 스크립트 목록 반환

    Returns:
        {category: [script_names]} 딕셔너리
    """
    all_scripts = find_scripts()

    categorized = {"deploy": [], "monitoring": [], "test": [], "cleanup": [], "other": []}

    for script in all_scripts:
        name = script.name.lower()

        if "deploy" in name or "rollback" in name:
            categorized["deploy"].append(script.name)
        elif "monitor" in name or "check" in name or "probe" in name:
            categorized["monitoring"].append(script.name)
        elif "test" in name or "compare" in name:
            categorized["test"].append(script.name)
        elif "cleanup" in name or "generate" in name:
            categorized["cleanup"].append(script.name)
        else:
            categorized["other"].append(script.name)

    return categorized


# ============================================================================
# 에이전트 통합
# ============================================================================


async def execute_script_as_task(
    task: TaskContext, script_name: str, args: Optional[Dict[str, Any]] = None
) -> TaskResult:
    """
    TaskContext를 받아 PowerShell 스크립트 실행

    Args:
        task: TaskContext 객체
        script_name: 스크립트 이름 (예: "deploy_phase4_canary.ps1")
        args: 스크립트 인자 (task.params와 병합됨)

    Returns:
        TaskResult 객체
    """
    # 스크립트 찾기
    scripts = find_scripts(script_name)

    if not scripts:
        return TaskResult(
            task_id=task.task_id,
            status=TaskStatus.FAILED,
            error_message=f"Script not found: {script_name}",
        )

    script_path = scripts[0]

    # 인자 병합 (task.params + args)
    merged_args = {**task.params, **(args or {})}

    # 실행
    result = await run_powershell_script(
        script_path, args=merged_args, timeout_seconds=task.timeout_seconds
    )

    # task_id 덮어쓰기
    result.task_id = task.task_id

    return result


# ============================================================================
# 편의 함수
# ============================================================================


async def quick_deploy(canary_percentage: int = 5, project_id: str = "naeda-genesis") -> TaskResult:
    """
    빠른 배포 (편의 함수)

    Args:
        canary_percentage: Canary 트래픽 비율 (%)
        project_id: GCP 프로젝트 ID

    Returns:
        TaskResult
    """
    script = ION_SCRIPTS / "deploy_phase4_canary.ps1"

    return await run_powershell_script(
        script, args={"CanaryPercentage": canary_percentage, "ProjectId": project_id}
    )


async def quick_rollback(project_id: str = "naeda-genesis") -> TaskResult:
    """
    빠른 롤백 (편의 함수)

    Args:
        project_id: GCP 프로젝트 ID

    Returns:
        TaskResult
    """
    script = ION_SCRIPTS / "rollback_phase4_canary.ps1"

    return await run_powershell_script(script, args={"ProjectId": project_id, "AutoApprove": True})


# ============================================================================
# 도구 정보 출력
# ============================================================================


def print_script_tools():
    """사용 가능한 스크립트 도구 목록 출력"""
    print("\n" + "=" * 60)
    print("📜 PowerShell Script Tools")
    print("=" * 60)

    categorized = list_available_scripts()

    for category, scripts in categorized.items():
        if scripts:
            print(f"\n📁 {category.upper()} ({len(scripts)}개)")
            for script in scripts[:5]:  # 상위 5개만
                print(f"  • {script}")
            if len(scripts) > 5:
                print(f"  ... 외 {len(scripts) - 5}개")

    print("\n" + "=" * 60)
    print(f"총 {sum(len(s) for s in categorized.values())}개 스크립트 사용 가능")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    import asyncio

    # 스크립트 목록 출력
    print_script_tools()

    # 간단한 테스트
    async def test():
        print("\n🧪 PowerShell Tool 테스트:\n")

        # 모니터링 상태 확인 (실제로 실행해보기)
        script = ION_SCRIPTS / "check_monitoring_status.ps1"
        if script.exists():
            print(f"1️⃣  {script.name} 실행 중...")
            result = await run_powershell_script(script)
            print(f"   상태: {result.status.value}")
            if result.output:
                print(f"   출력: {result.output[:200]}...")
        else:
            print(f"⚠️  {script.name} 파일이 없습니다.")

    asyncio.run(test())
