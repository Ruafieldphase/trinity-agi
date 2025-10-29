"""
Agent Handoff Tools - LangGraph 패턴 적용
==========================================

목적:
1. 에이전트 간 작업 전달 도구 (transfer_to_{agent})
2. LangGraph의 handoff-as-tool 패턴 구현
3. 타입 안전성 및 검증 로직 포함

통합:
- LangGraph Command 패턴
- agent_base.AgentBase
"""

import uuid
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from agent_base import AGENT_FOLDERS, create_task

# ============================================================================
# Handoff Tool 타입 정의
# ============================================================================


@dataclass
class HandoffTool:
    """
    Handoff 도구 정의

    LangGraph의 handoff tool과 동일한 개념
    """

    name: str
    target_agent: str
    description: str
    handler: Callable


# ============================================================================
# Handoff Tool 생성 함수
# ============================================================================


def create_handoff_tool(
    source_agent: str, target_agent: str, description: Optional[str] = None
) -> HandoffTool:
    """
    Handoff 도구 생성

    LangGraph의 create_handoff_tool 패턴 적용

    Args:
        source_agent: 작업을 전달하는 에이전트
        target_agent: 작업을 받을 에이전트
        description: 도구 설명 (옵션)

    Returns:
        HandoffTool 객체

    Example:
        >>> tool = create_handoff_tool("sian", "lubit")
        >>> result = tool.handler("코드 리뷰 부탁합니다", workflow_id="WF_001")
    """
    if target_agent not in AGENT_FOLDERS:
        raise ValueError(f"Unknown target agent: {target_agent}")

    default_desc = f"Transfer task from {source_agent} to {target_agent}"

    def handler(
        task_description: str,
        workflow_id: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        depends_on: Optional[list] = None,
    ) -> str:
        """
        Handoff 실행

        Args:
            task_description: 전달할 작업 설명
            workflow_id: 워크플로우 ID (옵션)
            params: 추가 파라미터 (옵션)
            depends_on: 의존성 작업 ID 리스트 (옵션)

        Returns:
            생성된 작업 ID
        """
        # 작업 생성
        task = create_task(
            agent=target_agent,
            description=task_description,
            params=params or {},
            workflow_id=workflow_id,
            created_by=source_agent,
        )

        if depends_on:
            task.depends_on = depends_on

        # INBOX에 작업 파일 생성
        target_inbox = AGENT_FOLDERS[target_agent]
        task_file = target_inbox / f"{task.task_id}.json"

        import json
        from dataclasses import asdict

        with open(task_file, "w", encoding="utf-8") as f:
            json.dump(asdict(task), f, indent=2, ensure_ascii=False)

        print(f"✅ [{source_agent}] → [{target_agent}] Handoff: {task_description[:50]}...")

        return task.task_id

    return HandoffTool(
        name=f"transfer_to_{target_agent}",
        target_agent=target_agent,
        description=description or default_desc,
        handler=handler,
    )


# ============================================================================
# 각 에이전트용 Handoff Tools 정의
# ============================================================================


# Gitko의 도구들
def create_gitko_tools():
    """Gitko가 사용할 수 있는 Handoff 도구들"""
    return [
        create_handoff_tool(
            source_agent="gitko",
            target_agent="sian",
            description="Sian에게 코드 개선/리팩터링 작업 전달",
        ),
        create_handoff_tool(
            source_agent="gitko",
            target_agent="lubit",
            description="Lubit에게 코드 리뷰/검증 작업 전달",
        ),
    ]


# Sian의 도구들
def create_sian_tools():
    """Sian이 사용할 수 있는 Handoff 도구들"""
    return [
        create_handoff_tool(
            source_agent="sian",
            target_agent="lubit",
            description="개선한 코드를 Lubit에게 리뷰 요청",
        ),
        create_handoff_tool(
            source_agent="sian", target_agent="gitko", description="작업 완료를 Gitko에게 보고"
        ),
    ]


# Lubit의 도구들
def create_lubit_tools():
    """Lubit이 사용할 수 있는 Handoff 도구들"""
    return [
        create_handoff_tool(
            source_agent="lubit",
            target_agent="sian",
            description="리뷰 중 발견한 개선 사항을 Sian에게 요청",
        ),
        create_handoff_tool(
            source_agent="lubit", target_agent="gitko", description="리뷰 완료를 Gitko에게 보고"
        ),
    ]


# ============================================================================
# 도구 레지스트리
# ============================================================================

AGENT_TOOLS = {
    "gitko": create_gitko_tools(),
    "sian": create_sian_tools(),
    "lubit": create_lubit_tools(),
}


def get_tools_for_agent(agent_name: str) -> list[HandoffTool]:
    """
    특정 에이전트가 사용할 수 있는 도구 목록 반환

    Args:
        agent_name: 'gitko', 'sian', 'lubit' 중 하나

    Returns:
        HandoffTool 리스트

    Example:
        >>> tools = get_tools_for_agent("sian")
        >>> for tool in tools:
        ...     print(tool.name, tool.description)
    """
    agent_name = agent_name.lower()
    if agent_name not in AGENT_TOOLS:
        raise ValueError(f"Unknown agent: {agent_name}")

    return AGENT_TOOLS[agent_name]


def execute_handoff(tool_name: str, agent_name: str, task_description: str, **kwargs) -> str:
    """
    편의 함수: 도구 이름으로 Handoff 실행

    Args:
        tool_name: 'transfer_to_lubit' 등
        agent_name: 도구를 실행하는 에이전트
        task_description: 작업 설명
        **kwargs: 추가 파라미터

    Returns:
        생성된 작업 ID

    Example:
        >>> task_id = execute_handoff(
        ...     "transfer_to_lubit",
        ...     "sian",
        ...     "이 코드 리뷰해주세요",
        ...     workflow_id="WF_001"
        ... )
    """
    tools = get_tools_for_agent(agent_name)

    for tool in tools:
        if tool.name == tool_name:
            return tool.handler(task_description, **kwargs)

    raise ValueError(f"Tool not found: {tool_name} for agent {agent_name}")


# ============================================================================
# 병렬 Handoff (Send 패턴)
# ============================================================================


def send_to_multiple_agents(
    source_agent: str,
    target_agents: list[str],
    task_descriptions: Dict[str, str],
    workflow_id: Optional[str] = None,
) -> Dict[str, str]:
    """
    여러 에이전트에게 동시에 작업 전달 (LangGraph Send 패턴)

    Args:
        source_agent: 작업을 전달하는 에이전트
        target_agents: 대상 에이전트 리스트
        task_descriptions: {agent_name: task_description} 매핑
        workflow_id: 워크플로우 ID (옵션)

    Returns:
        {agent_name: task_id} 매핑

    Example:
        >>> task_ids = send_to_multiple_agents(
        ...     "gitko",
        ...     ["sian", "lubit"],
        ...     {
        ...         "sian": "코드 개선",
        ...         "lubit": "보안 점검"
        ...     },
        ...     workflow_id="WF_001"
        ... )
        >>> print(task_ids)
        {'sian': 'task-xxx', 'lubit': 'task-yyy'}
    """
    workflow_id = workflow_id or str(uuid.uuid4())
    task_ids = {}

    print(f"\n🔀 [{source_agent}] 병렬 Handoff 시작:")

    for target_agent in target_agents:
        if target_agent not in task_descriptions:
            raise ValueError(f"No task description for {target_agent}")

        task_description = task_descriptions[target_agent]

        # Handoff 도구 생성 및 실행
        tool = create_handoff_tool(source_agent, target_agent)
        task_id = tool.handler(task_description, workflow_id=workflow_id)

        task_ids[target_agent] = task_id
        print(f"  → [{target_agent}]: {task_description[:40]}...")

    print(f"✅ 총 {len(task_ids)}개 에이전트에게 작업 전달 완료\n")

    return task_ids


# ============================================================================
# 조건부 Handoff
# ============================================================================


def conditional_handoff(
    source_agent: str,
    condition: bool,
    true_agent: str,
    false_agent: str,
    true_task: str,
    false_task: str,
    workflow_id: Optional[str] = None,
) -> str:
    """
    조건에 따라 다른 에이전트에게 작업 전달

    Args:
        source_agent: 작업을 전달하는 에이전트
        condition: 조건 (True/False)
        true_agent: 조건이 True일 때 대상
        false_agent: 조건이 False일 때 대상
        true_task: True일 때 작업 설명
        false_task: False일 때 작업 설명
        workflow_id: 워크플로우 ID (옵션)

    Returns:
        생성된 작업 ID

    Example:
        >>> task_id = conditional_handoff(
        ...     "gitko",
        ...     review_passed,
        ...     true_agent="sian",
        ...     false_agent="lubit",
        ...     true_task="배포 준비",
        ...     false_task="재리뷰 요청",
        ...     workflow_id="WF_001"
        ... )
    """
    target_agent = true_agent if condition else false_agent
    task_description = true_task if condition else false_task

    print(f"🔀 조건부 Handoff: {'TRUE' if condition else 'FALSE'} → [{target_agent}]")

    tool = create_handoff_tool(source_agent, target_agent)
    return tool.handler(task_description, workflow_id=workflow_id)


# ============================================================================
# 도구 정보 출력
# ============================================================================


def print_all_tools():
    """모든 에이전트의 도구 목록 출력"""
    print("\n" + "=" * 60)
    print("📦 Agent Handoff Tools Registry")
    print("=" * 60)

    for agent_name, tools in AGENT_TOOLS.items():
        print(f"\n🤖 {agent_name.upper()}")
        for tool in tools:
            print(f"  • {tool.name}")
            print(f"    → {tool.description}")

    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    # 도구 목록 출력
    print_all_tools()

    # 간단한 테스트
    print("🧪 Handoff Tool 테스트:\n")

    # 1. 단일 Handoff
    sian_tools = get_tools_for_agent("sian")
    transfer_to_lubit = sian_tools[0]  # transfer_to_lubit

    task_id = transfer_to_lubit.handler("테스트 코드 리뷰 부탁합니다", workflow_id="TEST_WF")
    print(f"✅ 생성된 작업 ID: {task_id}\n")

    # 2. 병렬 Handoff
    task_ids = send_to_multiple_agents(
        "gitko",
        ["sian", "lubit"],
        {"sian": "코드 개선 작업", "lubit": "보안 점검 작업"},
        workflow_id="PARALLEL_TEST",
    )
    print(f"✅ 병렬 작업 ID들: {task_ids}\n")
