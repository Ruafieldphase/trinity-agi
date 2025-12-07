"""
Exploration Policy - 인간 행동 패턴 기반 탐색 정책
================================================

비노체의 OBS 행동 패턴을 기반으로 탐색 전략을 관리합니다.

Human-like Exploration Loop:
1. 프로그램 열기
2. 관찰 (Observation)
3. 추측 (Hypothesis)
4. 행동 (Action)
5. 실패 (Fail)
6. 수정 (Adjust)

하이브리드 정책:
- MCP/API 가능 → 자동화
- 불가능 → 인간식 탐색
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class ExecutionMode(Enum):
    """실행 모드"""
    API = "api"              # API/MCP 자동화
    UI_EXPLORATION = "ui"    # 인간식 UI 탐색
    HYBRID = "hybrid"        # 혼합


class ExplorationPhase(Enum):
    """탐색 단계"""
    OBSERVE = "observe"      # 관찰
    HYPOTHESIZE = "hypothesize"  # 추측
    ACT = "act"              # 행동
    EVALUATE = "evaluate"    # 평가
    ADJUST = "adjust"        # 수정


@dataclass
class ExplorationStep:
    """탐색 단계 기록"""
    phase: ExplorationPhase
    action: str
    result: str
    success: bool
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ExplorationSession:
    """탐색 세션"""
    goal: str
    mode: ExecutionMode
    steps: List[ExplorationStep] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    success: bool = False


class ExplorationPolicy:
    """
    Exploration Policy
    
    비노체의 행동 패턴을 기반으로 탐색 전략을 관리합니다.
    
    핵심 원칙:
    - 학습보다 탐색 기반 습득
    - 유사한 구조 예측 및 시도
    - 실패는 문제가 아닌 학습 기회
    """
    
    # UI 패턴 분류
    UI_PATTERNS = {
        "editor": ["File", "Edit", "View", "Help"],
        "player": ["Play", "Pause", "Stop", "Settings"],
        "browser": ["Back", "Forward", "Refresh", "Address"],
        "installer": ["Next", "Back", "Install", "Cancel"],
    }
    
    # 공통 단축키
    COMMON_SHORTCUTS = {
        "save": ["ctrl+s"],
        "undo": ["ctrl+z"],
        "redo": ["ctrl+y"],
        "copy": ["ctrl+c"],
        "paste": ["ctrl+v"],
        "new": ["ctrl+n"],
        "open": ["ctrl+o"],
        "search": ["ctrl+f"],
    }
    
    def __init__(self):
        self.sessions: List[ExplorationSession] = []
        self.learned_patterns: Dict[str, List[str]] = {}
        logger.info("Exploration Policy initialized")
    
    def decide_mode(self, goal: str, available_apis: List[str]) -> ExecutionMode:
        """
        실행 모드 결정
        
        Args:
            goal: 목표
            available_apis: 사용 가능한 API 목록
            
        Returns:
            ExecutionMode: 결정된 실행 모드
        """
        # API로 가능한지 확인
        goal_lower = goal.lower()
        
        for api in available_apis:
            if api.lower() in goal_lower or goal_lower in api.lower():
                logger.info(f"API mode selected: {api}")
                return ExecutionMode.API
        
        # 파일 조작 등 API 가능한 패턴 확인
        api_keywords = ["file", "create", "delete", "read", "write", "http", "api"]
        if any(kw in goal_lower for kw in api_keywords):
            return ExecutionMode.HYBRID
        
        # 기본: UI 탐색
        return ExecutionMode.UI_EXPLORATION
    
    def start_exploration(self, goal: str, mode: ExecutionMode) -> ExplorationSession:
        """탐색 세션 시작"""
        session = ExplorationSession(goal=goal, mode=mode)
        self.sessions.append(session)
        logger.info(f"Exploration session started: {goal[:50]}...")
        return session
    
    def suggest_next_action(
        self, 
        session: ExplorationSession,
        current_ui_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        다음 행동 제안 (Human-like Exploration Loop)
        
        Args:
            session: 현재 세션
            current_ui_state: 현재 UI 상태
            
        Returns:
            Dict: 제안된 행동
        """
        # 현재 단계 파악
        last_phase = session.steps[-1].phase if session.steps else None
        
        # Phase 진행
        if last_phase is None:
            return self._suggest_observe(current_ui_state)
        elif last_phase == ExplorationPhase.OBSERVE:
            return self._suggest_hypothesize(session, current_ui_state)
        elif last_phase == ExplorationPhase.HYPOTHESIZE:
            return self._suggest_action(session, current_ui_state)
        elif last_phase == ExplorationPhase.ACT:
            return self._suggest_evaluate(session, current_ui_state)
        elif last_phase == ExplorationPhase.EVALUATE:
            last_step = session.steps[-1]
            if last_step.success:
                return {"phase": "complete", "action": "done"}
            else:
                return self._suggest_adjust(session, current_ui_state)
        elif last_phase == ExplorationPhase.ADJUST:
            return self._suggest_observe(current_ui_state)  # 루프 재시작
        
        return {"phase": "unknown", "action": "observe"}
    
    def _suggest_observe(self, ui_state: Dict[str, Any]) -> Dict[str, Any]:
        """관찰 단계 제안"""
        return {
            "phase": ExplorationPhase.OBSERVE.value,
            "action": "scan_ui",
            "description": "화면을 스캔하여 UI 요소 파악",
            "look_for": ["메뉴", "버튼", "입력창", "아이콘"]
        }
    
    def _suggest_hypothesize(self, session: ExplorationSession, ui_state: Dict[str, Any]) -> Dict[str, Any]:
        """추측 단계 제안"""
        # UI 패턴 매칭
        matched_pattern = self._match_ui_pattern(ui_state)
        
        return {
            "phase": ExplorationPhase.HYPOTHESIZE.value,
            "action": "predict_path",
            "matched_pattern": matched_pattern,
            "description": f"이 앱은 {matched_pattern or 'unknown'} 계열로 추정",
            "suggested_paths": self._get_common_paths(matched_pattern)
        }
    
    def _suggest_action(self, session: ExplorationSession, ui_state: Dict[str, Any]) -> Dict[str, Any]:
        """행동 단계 제안"""
        # 이전 학습된 패턴 확인
        goal_key = self._normalize_goal(session.goal)
        if goal_key in self.learned_patterns:
            return {
                "phase": ExplorationPhase.ACT.value,
                "action": "use_learned_pattern",
                "description": "학습된 패턴 사용",
                "steps": self.learned_patterns[goal_key]
            }
        
        # 새로운 시도
        return {
            "phase": ExplorationPhase.ACT.value,
            "action": "try_interaction",
            "description": "UI 요소와 상호작용 시도",
            "try_first": ["메뉴 클릭", "설정 열기", "검색 사용"]
        }
    
    def _suggest_evaluate(self, session: ExplorationSession, ui_state: Dict[str, Any]) -> Dict[str, Any]:
        """평가 단계 제안"""
        return {
            "phase": ExplorationPhase.EVALUATE.value,
            "action": "check_result",
            "description": "행동 결과 확인",
            "check_for": ["목표 달성 여부", "UI 변화", "오류 메시지"]
        }
    
    def _suggest_adjust(self, session: ExplorationSession, ui_state: Dict[str, Any]) -> Dict[str, Any]:
        """수정 단계 제안"""
        failed_actions = [s.action for s in session.steps if not s.success]
        
        return {
            "phase": ExplorationPhase.ADJUST.value,
            "action": "modify_approach",
            "description": "접근 방식 수정",
            "avoid": failed_actions[-3:] if len(failed_actions) >= 3 else failed_actions,
            "suggest": "다른 경로나 방법 시도"
        }
    
    def _match_ui_pattern(self, ui_state: Dict[str, Any]) -> Optional[str]:
        """UI 상태로 패턴 매칭"""
        elements = ui_state.get("elements", [])
        element_names = [str(e).lower() for e in elements]
        
        for pattern_name, keywords in self.UI_PATTERNS.items():
            matches = sum(1 for kw in keywords if kw.lower() in " ".join(element_names))
            if matches >= 2:
                return pattern_name
        
        return None
    
    def _get_common_paths(self, pattern: Optional[str]) -> List[str]:
        """패턴별 공통 경로"""
        paths = {
            "editor": ["File > Open", "Edit > Preferences", "View > Settings"],
            "player": ["Settings > Audio", "Settings > Subtitles"],
            "browser": ["Settings > Privacy", "Tools > Options"],
            "installer": ["Next > Next > Install"],
        }
        return paths.get(pattern, ["메뉴 탐색", "설정 확인", "검색 사용"])
    
    def _normalize_goal(self, goal: str) -> str:
        """목표 정규화"""
        return goal.lower().strip()[:50]
    
    def record_success(self, session: ExplorationSession, steps: List[str]):
        """성공 패턴 기록"""
        goal_key = self._normalize_goal(session.goal)
        self.learned_patterns[goal_key] = steps
        session.success = True
        session.completed_at = datetime.now().isoformat()
        logger.info(f"Pattern learned for: {goal_key}")
    
    def get_stats(self) -> Dict[str, Any]:
        """통계 반환"""
        return {
            "total_sessions": len(self.sessions),
            "learned_patterns": len(self.learned_patterns),
            "success_rate": (
                sum(1 for s in self.sessions if s.success) / len(self.sessions)
                if self.sessions else 0
            )
        }


# 모듈 레벨 인스턴스
_policy_instance: Optional[ExplorationPolicy] = None

def get_exploration_policy() -> ExplorationPolicy:
    """Exploration Policy 싱글톤 인스턴스 반환"""
    global _policy_instance
    if _policy_instance is None:
        _policy_instance = ExplorationPolicy()
    return _policy_instance
