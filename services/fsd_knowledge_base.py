"""
패턴 기반 습득 시스템 (Pattern-Based Acquisition System)
==========================================================

리듬 구조 철학:
- 모든 것을 학습하지 않는다
- 공통 패턴을 인식하고, 차이만 습득한다
- 실패 경험을 장기 기억으로 저장한다

예시:
- "앱 열기" = Win → 이름 입력 → Enter (공통)
- 앱마다 이름만 다름 (차이)
- VSCode ≈ Cursor ≈ Antigravity (유사 패턴)
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field, asdict

# 경험 저장 경로
EXPERIENCE_PATH = Path("c:/workspace/agi/memory/fsd_experiences.json")
EXPERIENCE_PATH.parent.mkdir(parents=True, exist_ok=True)


@dataclass
class Experience:
    """실패/성공 경험 기록"""
    timestamp: str
    pattern: str        # 사용된 패턴
    context: str        # 목표/상황
    success: bool
    error_type: str = ""
    recovery_used: str = ""
    learned_variation: Dict = field(default_factory=dict)  # 습득된 차이


# ============================================================================
# 공통 패턴 정의
# ============================================================================

COMMON_PATTERNS = {
    "app_launch": {
        "description": "앱 실행 (시작 메뉴)",
        "base_steps": [
            {"action": "press_key", "key": "win"},
            {"action": "wait", "duration": 0.5},
            {"action": "type", "text": "{app_name}"},
            {"action": "wait", "duration": 0.5},
            {"action": "press_key", "key": "enter"}
        ],
        "variables": ["app_name"]
    },
    
    "app_launch_hotkey": {
        "description": "앱 실행 (단축키)",
        "base_steps": [
            {"action": "hotkey", "keys": "{hotkeys}"}
        ],
        "variables": ["hotkeys"]
    },
    
    "menu_navigate": {
        "description": "메뉴 탐색",
        "base_steps": [
            {"action": "press_key", "key": "alt"},
            {"action": "wait", "duration": 0.3},
            {"action": "type", "text": "{menu_key}"}
        ],
        "variables": ["menu_key"]
    },
    
    "text_input": {
        "description": "텍스트 입력",
        "base_steps": [
            {"action": "type", "text": "{text}"}
        ],
        "variables": ["text"]
    },
    
    "clipboard_action": {
        "description": "클립보드 작업",
        "base_steps": [
            {"action": "hotkey", "keys": "{hotkeys}"}
        ],
        "variables": ["hotkeys"],
        "variants": {
            "copy": ["ctrl", "c"],
            "paste": ["ctrl", "v"],
            "cut": ["ctrl", "x"]
        }
    },
    
    "file_action": {
        "description": "파일 작업",
        "base_steps": [
            {"action": "hotkey", "keys": "{hotkeys}"}
        ],
        "variables": ["hotkeys"],
        "variants": {
            "save": ["ctrl", "s"],
            "open": ["ctrl", "o"],
            "new": ["ctrl", "n"],
            "close": ["ctrl", "w"]
        }
    },
    
    "edit_action": {
        "description": "편집 작업",
        "base_steps": [
            {"action": "hotkey", "keys": "{hotkeys}"}
        ],
        "variables": ["hotkeys"],
        "variants": {
            "undo": ["ctrl", "z"],
            "redo": ["ctrl", "y"],
            "select_all": ["ctrl", "a"],
            "find": ["ctrl", "f"]
        }
    }
}

# ============================================================================
# 앱별 차이 (Variations)
# ============================================================================

APP_VARIATIONS = {
    # 앱 이름 매핑 (공통 패턴의 변수 값)
    "메모장": {"pattern": "app_launch", "app_name": "notepad"},
    "notepad": {"pattern": "app_launch", "app_name": "notepad"},
    
    "크롬": {"pattern": "app_launch", "app_name": "chrome"},
    "chrome": {"pattern": "app_launch", "app_name": "chrome"},
    "구글": {"pattern": "app_launch", "app_name": "chrome"},
    
    "탐색기": {"pattern": "app_launch_hotkey", "hotkeys": ["win", "e"]},
    "explorer": {"pattern": "app_launch_hotkey", "hotkeys": ["win", "e"]},
    
    "vscode": {"pattern": "app_launch", "app_name": "code"},
    "visual studio code": {"pattern": "app_launch", "app_name": "code"},
    "코드": {"pattern": "app_launch", "app_name": "code"},
    
    "커서": {"pattern": "app_launch", "app_name": "cursor"},
    "cursor": {"pattern": "app_launch", "app_name": "cursor"},
    
    "터미널": {"pattern": "app_launch", "app_name": "terminal"},
    "cmd": {"pattern": "app_launch", "app_name": "cmd"},
    "powershell": {"pattern": "app_launch", "app_name": "powershell"},
    
    # 단축키 작업
    "복사": {"pattern": "clipboard_action", "variant": "copy"},
    "붙여넣기": {"pattern": "clipboard_action", "variant": "paste"},
    "잘라내기": {"pattern": "clipboard_action", "variant": "cut"},
    
    "저장": {"pattern": "file_action", "variant": "save"},
    "열기": {"pattern": "file_action", "variant": "open"},
    "새로만들기": {"pattern": "file_action", "variant": "new"},
    
    "실행취소": {"pattern": "edit_action", "variant": "undo"},
    "되돌리기": {"pattern": "edit_action", "variant": "undo"},
    "다시실행": {"pattern": "edit_action", "variant": "redo"},
    "전체선택": {"pattern": "edit_action", "variant": "select_all"},
    "찾기": {"pattern": "edit_action", "variant": "find"},
}

# 유사 앱 그룹 (같은 패턴 공유)
SIMILAR_APP_GROUPS = {
    "code_editors": ["vscode", "cursor", "sublime", "atom", "notepad++"],
    "browsers": ["chrome", "firefox", "edge", "brave"],
    "terminals": ["cmd", "powershell", "terminal", "wt"],
}


class PatternAcquisitionSystem:
    """
    패턴 기반 습득 시스템
    
    철학:
    - 공통 패턴 인식 → 차이만 습득
    - 실패 경험 → 장기 기억 저장
    - 유사 앱 → 같은 패턴 적용
    """
    
    def __init__(self):
        self.patterns = COMMON_PATTERNS.copy()
        self.variations = APP_VARIATIONS.copy()
        self.experiences: List[Experience] = []
        self._load_experiences()
    
    def _load_experiences(self):
        """저장된 경험 로드"""
        if EXPERIENCE_PATH.exists():
            try:
                with open(EXPERIENCE_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.experiences = [Experience(**e) for e in data]
            except Exception:
                self.experiences = []
    
    def _save_experiences(self):
        """경험 저장"""
        try:
            with open(EXPERIENCE_PATH, 'w', encoding='utf-8') as f:
                json.dump([asdict(e) for e in self.experiences[-100:]], f, 
                         ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def find_pattern(self, goal: str) -> Optional[Dict]:
        """
        목표에서 패턴 찾기
        
        1. 직접 매칭된 변형 확인
        2. 유사 앱 그룹에서 찾기
        3. 일반 패턴으로 폴백
        """
        goal_lower = goal.lower()
        
        # 1. 직접 매칭
        for keyword, variation in self.variations.items():
            if keyword in goal_lower or keyword in goal:
                return self._apply_pattern(variation)
        
        # 2. 유사 앱 그룹 검색
        for group_name, apps in SIMILAR_APP_GROUPS.items():
            for app in apps:
                if app in goal_lower:
                    # 그룹 내 첫 번째 앱의 패턴 사용
                    if apps[0] in self.variations:
                        base_variation = self.variations[apps[0]].copy()
                        base_variation["app_name"] = app  # 실제 앱 이름으로 교체
                        return self._apply_pattern(base_variation)
        
        # 3. "열어" 패턴 → 앱 실행 추론
        if "열어" in goal or "실행" in goal or "켜" in goal:
            # 앱 이름 추출 시도
            for word in goal.split():
                if len(word) > 1 and word not in ["열어", "줘", "해줘", "실행", "켜"]:
                    return self._apply_pattern({
                        "pattern": "app_launch",
                        "app_name": word
                    })
        
        return None
    
    def _apply_pattern(self, variation: Dict) -> Dict:
        """패턴에 변수 적용"""
        pattern_name = variation.get("pattern")
        if pattern_name not in self.patterns:
            return None
        
        pattern = self.patterns[pattern_name]
        steps = []
        
        # 변형(variant) 확인
        if "variant" in variation and "variants" in pattern:
            variant_keys = pattern["variants"].get(variation["variant"], [])
            variation["hotkeys"] = variant_keys
        
        # 스텝 복사 및 변수 치환
        for step in pattern["base_steps"]:
            new_step = step.copy()
            
            # 변수 치환
            for key, value in new_step.items():
                if isinstance(value, str) and "{" in value:
                    for var_name, var_value in variation.items():
                        placeholder = "{" + var_name + "}"
                        if placeholder in value:
                            # 배열은 그대로 유지
                            if isinstance(var_value, list):
                                new_step[key] = var_value
                            else:
                                new_step[key] = value.replace(placeholder, str(var_value))
                elif key == "keys" and value == "{hotkeys}":
                    new_step["keys"] = variation.get("hotkeys", [])
            
            # reason 추가
            if "reason" not in new_step:
                new_step["reason"] = pattern.get("description", "")
            
            steps.append(new_step)
        
        return {
            "pattern": pattern_name,
            "description": pattern.get("description", ""),
            "steps": steps,
            "variation": variation
        }
    
    def record_experience(
        self,
        pattern: str,
        context: str,
        success: bool,
        error_type: str = "",
        recovery_used: str = "",
        learned_variation: Dict = None
    ):
        """
        경험 기록 (성공/실패)
        
        실패 경험은 특히 중요 - 다음에 같은 실수 안 하도록
        """
        exp = Experience(
            timestamp=datetime.now().isoformat(),
            pattern=pattern,
            context=context,
            success=success,
            error_type=error_type,
            recovery_used=recovery_used,
            learned_variation=learned_variation or {}
        )
        self.experiences.append(exp)
        self._save_experiences()
        
        # 실패에서 배운 변형 저장
        if not success and learned_variation:
            # 새로운 변형 습득
            self._acquire_variation(context, learned_variation)
    
    def _acquire_variation(self, context: str, variation: Dict):
        """새로운 변형 습득 (실패에서 배움)"""
        # 간단한 키워드 추출
        keywords = [w for w in context.split() if len(w) > 1]
        if keywords:
            key = keywords[0].lower()
            if key not in self.variations:
                self.variations[key] = variation
    
    def get_failure_insights(self, pattern: str = None) -> List[str]:
        """실패 경험에서 인사이트 추출"""
        failures = [e for e in self.experiences 
                   if not e.success and (pattern is None or e.pattern == pattern)]
        
        insights = []
        error_counts = {}
        
        for f in failures:
            err = f.error_type or "unknown"
            error_counts[err] = error_counts.get(err, 0) + 1
        
        for err, count in sorted(error_counts.items(), key=lambda x: -x[1]):
            insights.append(f"{err}: {count}회 발생")
        
        return insights
    
    def get_summary(self) -> Dict:
        """시스템 요약"""
        return {
            "patterns_count": len(self.patterns),
            "variations_count": len(self.variations),
            "experiences_count": len(self.experiences),
            "success_rate": (
                sum(1 for e in self.experiences if e.success) / max(len(self.experiences), 1)
            ),
            "patterns": list(self.patterns.keys()),
            "recent_failures": self.get_failure_insights()[:5]
        }


# 싱글톤
_acquisition_system = None

def get_acquisition_system() -> PatternAcquisitionSystem:
    """패턴 습득 시스템 인스턴스"""
    global _acquisition_system
    if _acquisition_system is None:
        _acquisition_system = PatternAcquisitionSystem()
    return _acquisition_system


# 하위 호환성 (기존 코드 지원)
_knowledge_base_wrapper = None

def get_knowledge_base():
    """레거시 호환 - FSDKnowledgeBase 래퍼 반환"""
    global _knowledge_base_wrapper
    if _knowledge_base_wrapper is None:
        _knowledge_base_wrapper = FSDKnowledgeBase()
    return _knowledge_base_wrapper


class FSDKnowledgeBase:
    """레거시 호환 래퍼"""
    def __init__(self):
        self._system = get_acquisition_system()
    
    def find_procedure(self, goal: str):
        return self._system.find_pattern(goal)
    
    def get_app_launch_procedure(self, app_name: str):
        result = self._system.find_pattern(f"{app_name} 열어줘")
        return result.get("steps", []) if result else []
    
    def get_knowledge_summary(self):
        return self._system.get_summary()


# 테스트
if __name__ == "__main__":
    system = get_acquisition_system()
    
    print("=== 패턴 기반 습득 시스템 ===")
    print(f"요약: {system.get_summary()}")
    
    # 테스트 케이스
    tests = [
        "메모장 열어줘",
        "크롬 열어줘",
        "VSCode 열어줘",
        "복사해줘",
        "저장해줘",
        "Sublime Text 열어줘",  # 유사 앱 그룹에서 추론
    ]
    
    for test in tests:
        result = system.find_pattern(test)
        print(f"\n[{test}]")
        if result:
            print(f"  패턴: {result['pattern']}")
            print(f"  설명: {result['description']}")
            for i, step in enumerate(result['steps'], 1):
                print(f"  {i}. {step}")
        else:
            print("  패턴 없음 → Gemini 분석 필요")
