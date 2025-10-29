"""
Tool Registry 통합

fdo_agi_repo의 5개 도구를 ION API에 통합합니다.

작성자: Gitco (GitHub Copilot)
날짜: 2025-10-21

통합 도구:
- RAG: 문서 검색
- WebSearch: 웹 검색 (현재 더미)
- FileIO: 파일 읽기/쓰기
- CodeExec: Python 코드 실행
- Tabular: CSV 파일 분석
"""

import os
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

# fdo_agi_repo Tool Registry 통합
FDO_AGI_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "fdo_agi_repo")
if os.path.exists(FDO_AGI_PATH):
    sys.path.insert(0, FDO_AGI_PATH)
    from orchestrator.tool_registry import ToolRegistry as FDOToolRegistry
else:
    # Fallback: Tool 기능 없이 동작
    class FDOToolRegistry:
        def __init__(self, cfg):
            pass

        def call(self, name, args):
            return {"ok": False, "error": "FDO Tool Registry not available"}


class ToolType(Enum):
    """도구 유형"""

    RAG = "rag"  # 문서 검색
    WEB = "web"  # 웹 검색
    FILEIO = "fileio"  # 파일 읽기/쓰기
    CODEEXEC = "codeexec"  # 코드 실행
    TABULAR = "tabular"  # 데이터 분석


@dataclass
class ToolResult:
    """도구 실행 결과"""

    success: bool
    data: Any
    error: Optional[str] = None
    tool_used: Optional[str] = None


class IONToolRegistry:
    """ION API용 Tool Registry 래퍼"""

    def __init__(self, enable_tools: bool = True):
        """
        Tool Registry 초기화

        Args:
            enable_tools: 도구 활성화 여부
        """
        self.enable_tools = enable_tools
        self.fdo_registry = None

        if self.enable_tools:
            try:
                self.fdo_registry = FDOToolRegistry(cfg={})
            except Exception as e:
                print(f"[WARNING] FDO Tool Registry 초기화 실패: {e}")
                self.enable_tools = False

    def call_tool(
        self, tool_type: ToolType, args: Dict[str, Any], fallback: bool = True
    ) -> ToolResult:
        """
        도구 호출

        Args:
            tool_type: 도구 유형
            args: 도구 인자
            fallback: 실패 시 대체 도구 시도 여부

        Returns:
            ToolResult: 실행 결과

        Examples:
            >>> registry = IONToolRegistry()
            >>> result = registry.call_tool(ToolType.RAG, {"query": "AGI란?"})
            >>> result.success
            True
        """
        if not self.enable_tools or not self.fdo_registry:
            return ToolResult(
                success=False, data=None, error="Tool Registry가 비활성화되었습니다", tool_used=None
            )

        try:
            # FDO Tool Registry 호출
            fdo_result = self.fdo_registry.call(tool_type.value, args)

            if fdo_result.get("ok"):
                return ToolResult(
                    success=True, data=fdo_result, error=None, tool_used=tool_type.value
                )
            else:
                # 도구 실패 시 fallback 시도
                if fallback:
                    fallback_result = self._try_fallback(tool_type, args)
                    if fallback_result.success:
                        return fallback_result

                return ToolResult(
                    success=False,
                    data=None,
                    error=fdo_result.get("error", "Unknown error"),
                    tool_used=tool_type.value,
                )

        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e), tool_used=tool_type.value)

    def _try_fallback(self, tool_type: ToolType, args: Dict[str, Any]) -> ToolResult:
        """
        대체 도구 시도

        Args:
            tool_type: 원래 도구 유형
            args: 도구 인자

        Returns:
            ToolResult: 대체 도구 실행 결과
        """
        # RAG 실패 시 → Web 검색 시도
        if tool_type == ToolType.RAG:
            return self.call_tool(ToolType.WEB, args, fallback=False)

        # 기타 도구는 fallback 없음
        return ToolResult(
            success=False, data=None, error=f"{tool_type.value} fallback 없음", tool_used=None
        )

    def select_tool_for_query(self, query: str, context: Optional[Dict] = None) -> ToolType:
        """
        쿼리 분석하여 적절한 도구 자동 선택

        Args:
            query: 사용자 쿼리
            context: 추가 컨텍스트

        Returns:
            ToolType: 선택된 도구

        Examples:
            >>> registry = IONToolRegistry()
            >>> tool = registry.select_tool_for_query("AGI 개념 설명해줘")
            >>> tool == ToolType.RAG
            True

            >>> tool = registry.select_tool_for_query("1+1 계산해줘")
            >>> tool == ToolType.CODEEXEC
            True
        """
        query_lower = query.lower()

        # 코드 실행 키워드
        code_keywords = ["계산", "실행", "run", "calculate", "compute", "python"]
        if any(kw in query_lower for kw in code_keywords):
            return ToolType.CODEEXEC

        # 파일 관련 키워드
        file_keywords = ["파일", "읽기", "쓰기", "file", "read", "write", ".txt", ".csv"]
        if any(kw in query_lower for kw in file_keywords):
            # CSV인 경우 Tabular 우선
            if ".csv" in query_lower or "csv" in query_lower:
                return ToolType.TABULAR
            return ToolType.FILEIO

        # 웹 검색 키워드
        web_keywords = ["검색", "최신", "search", "google", "웹"]
        if any(kw in query_lower for kw in web_keywords):
            return ToolType.WEB

        # 기본값: RAG (문서 검색)
        return ToolType.RAG

    def get_tool_chain(self, query: str, context: Optional[Dict] = None) -> List[ToolType]:
        """
        복잡한 쿼리를 위한 도구 체인 생성

        Args:
            query: 사용자 쿼리
            context: 추가 컨텍스트

        Returns:
            List[ToolType]: 실행할 도구 순서

        Examples:
            >>> registry = IONToolRegistry()
            >>> chain = registry.get_tool_chain("문서 읽고 데이터 분석해줘")
            >>> len(chain) >= 2
            True
        """
        query_lower = query.lower()
        chain = []

        # "읽고" + "분석" → FileIO → Tabular
        if ("읽" in query_lower or "read" in query_lower) and (
            "분석" in query_lower or "analyze" in query_lower
        ):
            chain.append(ToolType.FILEIO)
            chain.append(ToolType.TABULAR)

        # "검색하고" + "정리" → RAG → CodeExec
        elif ("검색" in query_lower or "search" in query_lower) and (
            "정리" in query_lower or "summarize" in query_lower
        ):
            chain.append(ToolType.RAG)
            chain.append(ToolType.CODEEXEC)

        # 단일 도구로 충분
        else:
            primary_tool = self.select_tool_for_query(query, context)
            chain.append(primary_tool)

        return chain


# 간단한 사용 예시
if __name__ == "__main__":
    registry = IONToolRegistry()

    # 테스트 쿼리
    test_queries = [
        "AGI 개념 설명해줘",
        "1+1 계산해줘",
        "data.csv 파일 읽어줘",
        "최신 AI 뉴스 검색해줘",
    ]

    print("=== ION Tool Registry 테스트 ===\n")
    for query in test_queries:
        tool = registry.select_tool_for_query(query)
        print(f"쿼리: {query}")
        print(f"  → 선택된 도구: {tool.value}\n")
