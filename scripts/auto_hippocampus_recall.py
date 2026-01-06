#!/usr/bin/env python3
"""
🧠 자동 Hippocampus 회상 시스템
GitHub Copilot의 무의식 장기기억 자동 활성화

인간처럼:
- 세션 시작 시 자동으로 관련 기억 회상
- 질문 키워드에서 자동으로 기존 시스템 탐지
- 의식적 결정 없이 자동 실행
"""

from pathlib import Path
import sys
import json
from typing import Dict, List, Any
from workspace_root import get_workspace_root

# Hippocampus 불러오기
sys.path.append(str(get_workspace_root() / "fdo_agi_repo"))
from copilot.hippocampus import CopilotHippocampus


class AutoHippocampusRecall:
    """
    자동 장기기억 회상 시스템
    
    무의식처럼 작동:
    - 세션 시작 → 자동으로 최근 3일 중요 기억 로드
    - 키워드 감지 → 자동으로 관련 시스템 찾기
    - 결정 없이 → 무의식적 자동 실행
    """
    
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.hippocampus = CopilotHippocampus(workspace)
        
        # 무의식 패턴 (자동 감지 키워드)
        self.unconscious_patterns = {
            "파일 찾기": ["everything", "search", "find", "locate"],
            "모니터링": ["monitoring", "dashboard", "report", "status"],
            "목표 관리": ["goal", "autonomous", "execute", "track"],
            "음악/리듬": ["music", "rhythm", "flow", "binaural"],
            "세션 관리": ["session", "continuity", "restore", "backup"],
            "RPA": ["rpa", "worker", "queue", "task"],
            "YouTube": ["youtube", "learn", "video", "analysis"],
        }
    
    def auto_recall_on_startup(self) -> Dict[str, Any]:
        """
        세션 시작 시 자동 회상 (무의식)
        
        Returns:
            {
                "recent_systems": [...],  # 최근 사용한 시스템들
                "important_files": [...], # 중요 파일들
                "next_actions": [...]     # 추천 다음 행동
            }
        """
        print("🧠 Auto-recalling from long-term memory...")
        
        result = {
            "recent_systems": [],
            "important_files": [],
            "next_actions": []
        }
        
        # 1. 최근 3일 중요 기억 자동 로드
        recent_memories = self.hippocampus.recall(
            query="recent important systems and tasks",
            top_k=10
        )
        
        # 2. 시스템 패턴 자동 인식
        for memory in recent_memories:
            for category, keywords in self.unconscious_patterns.items():
                if any(kw in str(memory).lower() for kw in keywords):
                    result["recent_systems"].append({
                        "category": category,
                        "memory": memory
                    })
                    break
        
        # 3. 중요 파일 자동 인덱싱 (Everything 활용)
        if self.hippocampus.everything:
            try:
                # 최근 수정된 중요 파일들
                important_exts = [".py", ".ps1", ".md", ".json"]
                for ext in important_exts:
                    recent_files = self.hippocampus.everything.search(
                        f"*{ext}",
                        max_results=5
                    )
                    result["important_files"].extend(recent_files)
            except Exception as e:
                print(f"⚠️ Everything search failed: {e}")
        
        # 4. 추천 다음 행동 (무의식적 제안)
        result["next_actions"] = self._suggest_next_actions(result["recent_systems"])
        
        return result
    
    def auto_detect_system(self, user_query: str) -> List[str]:
        """
        사용자 질문에서 자동으로 관련 시스템 감지 (무의식)
        
        Args:
            user_query: 사용자 질문
        
        Returns:
            감지된 시스템 이름 리스트
        """
        detected = []
        query_lower = user_query.lower()
        
        for category, keywords in self.unconscious_patterns.items():
            if any(kw in query_lower for kw in keywords):
                detected.append(category)
        
        return detected
    
    def auto_recall_for_query(self, user_query: str) -> Dict[str, Any]:
        """
        질문에 대한 자동 기억 회상 (무의식)
        
        Args:
            user_query: 사용자 질문
        
        Returns:
            {
                "detected_systems": [...],
                "relevant_memories": [...],
                "suggested_tools": [...]
            }
        """
        print(f"🧠 Auto-recalling for: {user_query}")
        
        # 1. 시스템 자동 감지
        detected_systems = self.auto_detect_system(user_query)
        
        # 2. 관련 기억 자동 회상
        relevant_memories = self.hippocampus.recall(user_query, top_k=5)
        
        # 3. 도구 자동 제안
        suggested_tools = self._suggest_tools(detected_systems, user_query)
        
        return {
            "detected_systems": detected_systems,
            "relevant_memories": relevant_memories,
            "suggested_tools": suggested_tools
        }
    
    def _suggest_next_actions(self, recent_systems: List[Dict]) -> List[str]:
        """최근 시스템 기반 다음 행동 제안"""
        actions = []
        
        system_categories = [s["category"] for s in recent_systems]
        
        if "목표 관리" in system_categories:
            actions.append("Check autonomous goal tracker")
        if "모니터링" in system_categories:
            actions.append("Generate latest monitoring report")
        if "RPA" in system_categories:
            actions.append("Verify RPA worker status")
        
        return actions
    
    def _suggest_tools(self, systems: List[str], query: str) -> List[str]:
        """감지된 시스템 기반 도구 제안"""
        tools = []
        
        for system in systems:
            if system == "파일 찾기":
                tools.append("Everything Search (everything_search.py)")
            elif system == "모니터링":
                tools.append("generate_monitoring_report.ps1")
            elif system == "목표 관리":
                tools.append("autonomous_goal_executor.py")
            elif system == "RPA":
                tools.append("ensure_rpa_worker.ps1")
        
        return tools
    
    def save_unconscious_state(self, output_path: Path) -> None:
        """무의식 상태 저장 (다음 세션 자동 로드용)"""
        state = {
            "timestamp": str(Path.ctime(output_path) if output_path.exists() else ""),
            "patterns": self.unconscious_patterns,
            "recent_recall": self.auto_recall_on_startup()
        }
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Unconscious state saved: {output_path}")


def main():
    """테스트 실행"""
    workspace = get_workspace_root()
    auto_recall = AutoHippocampusRecall(workspace)
    
    # 1. 세션 시작 시 자동 회상
    print("=" * 60)
    print("📍 Session Startup - Auto Recall")
    print("=" * 60)
    startup_result = auto_recall.auto_recall_on_startup()
    print(json.dumps(startup_result, indent=2, ensure_ascii=False))
    
    # 2. 질문 기반 자동 회상 테스트
    print("\n" + "=" * 60)
    print("📍 Query-based Auto Recall")
    print("=" * 60)
    test_queries = [
        "파일 찾기가 느려요",
        "모니터링 리포트 생성해줘",
        "자율 목표 실행해줘"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        result = auto_recall.auto_recall_for_query(query)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 3. 무의식 상태 저장
    output = workspace / "outputs" / "unconscious_state.json"
    auto_recall.save_unconscious_state(output)


if __name__ == "__main__":
    main()
