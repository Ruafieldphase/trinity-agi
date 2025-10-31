"""
Action Mapper
Phase 2.5 Week 3 Day 15

Step을 실행 가능한 Action으로 변환 (개선 버전)
- 복합 키 조합 지원 (Ctrl+S, Windows+Shift+S 등)
- 컨텍스트 기반 매핑
- 더 많은 액션 타입
"""


import re
from typing import Dict, Any, List, Optional
from .actions import Action, ClickAction, TypeAction, InstallAction
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)


class ActionMapper:
    """Step → Action 변환기 (개선 버전)"""
    
    # 액션 타입별 매핑
    ACTION_MAP = {
        'CLICK': ClickAction,
        'TYPE': TypeAction,
        'INSTALL': InstallAction,
        'DOWNLOAD': InstallAction,  # Install과 유사
        'RUN': ClickAction,          # Click과 유사
        'OPEN': ClickAction,
        'SELECT': ClickAction,
        'PRESS': ClickAction,        # 키 입력도 Click으로 (단순화)
        'WAIT': None,                # TODO: WaitAction 구현
        'VERIFY': None,              # TODO: VerifyAction 구현
    }
    
    # 키워드 → 액션 타입 매핑 (우선순위 순)
    KEYWORD_MAP = [
        # TYPE 관련
        (r'type\s+"([^"]+)"', 'TYPE'),
        (r"type\s+'([^']+)'", 'TYPE'),
        (r'type\s+([a-zA-Z0-9_\s]+)', 'TYPE'),
        (r'입력\s*[:：]?\s*["\']?([^"\'\n]+)', 'TYPE'),
        
        # PRESS 관련 (복합 키 조합)
        (r'press\s+((?:ctrl|alt|shift|windows?|win|cmd|command)\s*\+\s*)+\S+', 'PRESS'),
        (r'press\s+(enter|escape|esc|delete|del|backspace|tab|space)', 'PRESS'),
        (r'누르기?\s*[:：]?\s*([^\n]+)', 'PRESS'),
        
        # INSTALL 관련
        (r'install\s+([a-zA-Z0-9_\-\.]+)', 'INSTALL'),
        (r'download\s+([a-zA-Z0-9_\-\.]+)', 'INSTALL'),
        (r'설치\s*[:：]?\s*([^\n]+)', 'INSTALL'),
        
        # CLICK 관련 (기본)
        (r'click\s+(?:on\s+)?([^\n]+)', 'CLICK'),
        (r'open\s+([^\n]+)', 'CLICK'),
        (r'select\s+([^\n]+)', 'CLICK'),
        (r'클릭\s*[:：]?\s*([^\n]+)', 'CLICK'),
        (r'실행\s*[:：]?\s*([^\n]+)', 'CLICK'),
    ]
    
    @staticmethod
    @lru_cache(maxsize=128)
    def _extract_action_from_text(text: str) -> tuple[str, Optional[str]]:
        text_lower = text.lower().strip()
        for pattern, action_type in ActionMapper.KEYWORD_MAP:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                target = match.group(1) if match.lastindex and match.lastindex >= 1 else None
                logger.debug(f"Matched pattern '{pattern}' → {action_type}, target='{target}'")
                return action_type, target
        logger.debug(f"No pattern matched for '{text}', defaulting to CLICK")
        return 'CLICK', None
        @staticmethod
        @lru_cache(maxsize=128)
        def _extract_action_from_text(text: str) -> tuple[str, Optional[str]]:
            text_lower = text.lower().strip()
            for pattern, action_type in ActionMapper.KEYWORD_MAP:
                match = re.search(pattern, text_lower, re.IGNORECASE)
                if match:
                    target = match.group(1) if match.lastindex and match.lastindex >= 1 else None
                    logger.debug(f"Matched pattern '{pattern}' → {action_type}, target='{target}'")
                    return action_type, target
            logger.debug(f"No pattern matched for '{text}', defaulting to CLICK")
            return 'CLICK', None
        
        # 키워드 매핑 시도
        for pattern, action_type in self.KEYWORD_MAP:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                target = match.group(1) if match.lastindex and match.lastindex >= 1 else None
                logger.debug(f"Matched pattern '{pattern}' → {action_type}, target='{target}'")
                return action_type, target
        
        # 매칭 실패 시 기본값
        logger.debug(f"No pattern matched for '{text}', defaulting to CLICK")
        return 'CLICK', None
    
    @staticmethod
    @lru_cache(maxsize=64)
    def _parse_key_combination(key_string: str) -> Dict[str, Any]:
        key_string = key_string.strip()
        parts = [p.strip().lower() for p in key_string.split('+')]
        modifiers = []
        main_key = None
        modifier_map = {
            'ctrl': 'ctrl',
            'control': 'ctrl',
            'alt': 'alt',
            'shift': 'shift',
            'win': 'win',
            'windows': 'win',
            'cmd': 'command',
            'command': 'command',
        }
        for part in parts:
            if part in modifier_map:
                modifiers.append(modifier_map[part])
            else:
                main_key = part
        return {
            'modifiers': modifiers,
            'key': main_key,
            'raw': key_string,
        }
        @staticmethod
        @lru_cache(maxsize=64)
        def _parse_key_combination(key_string: str) -> Dict[str, Any]:
            key_string = key_string.strip()
            parts = [p.strip().lower() for p in key_string.split('+')]
            modifiers = []
            main_key = None
            modifier_map = {
                'ctrl': 'ctrl',
                'control': 'ctrl',
                'alt': 'alt',
                'shift': 'shift',
                'win': 'win',
                'windows': 'win',
                'cmd': 'command',
                'command': 'command',
            }
            for part in parts:
                if part in modifier_map:
                    modifiers.append(modifier_map[part])
                else:
                    main_key = part
            return {
                'modifiers': modifiers,
                'key': main_key,
                'raw': key_string,
            }
        
        # + 로 분리
        parts = [p.strip().lower() for p in key_string.split('+')]
        
        modifiers = []
        main_key = None
        
        modifier_map = {
            'ctrl': 'ctrl',
            'control': 'ctrl',
            'alt': 'alt',
            'shift': 'shift',
            'win': 'win',
            'windows': 'win',
            'cmd': 'command',
            'command': 'command',
        }
        
        for part in parts:
            if part in modifier_map:
                modifiers.append(modifier_map[part])
            else:
                main_key = part
        
        return {
            'modifiers': modifiers,
            'key': main_key,
            'raw': key_string,
        }
    
    def _enhance_step_with_context(self, step: Dict[str, Any], index: int, total: int) -> Dict[str, Any]:
        """
        Step에 컨텍스트 정보 추가
        
        Args:
            step: 원본 step
            index: 현재 인덱스 (0-based)
            total: 전체 step 수
        
        Returns:
            향상된 step
        """
        enhanced = step.copy()
        
        instruction = step.get('instruction', '').lower()
        
        # 컨텍스트 추론
        if index == 0:
            enhanced['context'] = 'first_step'
        elif index == total - 1:
            enhanced['context'] = 'last_step'
        else:
            enhanced['context'] = 'middle_step'
        
        # 액션 타입이 없으면 텍스트에서 추출
        if not step.get('action') or step.get('action') == 'UNKNOWN':
            action_type, target = self._extract_action_from_text(instruction)
            enhanced['action'] = action_type
            if target and not enhanced.get('target'):
                enhanced['target'] = target
        
        # PRESS 액션이면 키 조합 파싱
        if enhanced.get('action') == 'PRESS' and enhanced.get('target'):
            enhanced['key_info'] = self._parse_key_combination(enhanced['target'])
        
        return enhanced
    
    def map_step_to_action(self, step: Dict[str, Any]) -> Action:
        """
        Step을 Action으로 변환
        
        Args:
            step: Step Extractor/Refiner에서 생성된 단계
        
        Returns:
            Action 인스턴스
        
        Raises:
            ValueError: 알 수 없는 액션 타입
        """
        action_type = step.get('action', '').upper()
        
        if not action_type or action_type == 'UNKNOWN':
            # 텍스트에서 액션 추출 시도
            instruction = step.get('instruction', '')
            action_type, target = ActionMapper._extract_action_from_text(instruction)
            if target and not step.get('target'):
                step['target'] = target
        
        action_class = self.ACTION_MAP.get(action_type)
        
        if action_class is None:
            logger.warning(f"Action type '{action_type}' not implemented, using default Click")
            action_class = ClickAction
        
        logger.debug(f"Mapping {action_type} → {action_class.__name__}")
        
        return action_class(step)
    
    def map_steps(self, steps: List[Dict[str, Any]]) -> List[Action]:
        """
        여러 Step을 Action 리스트로 변환 (컨텍스트 인식)
        
        Args:
            steps: Step 리스트
        
        Returns:
            Action 리스트
        """
        actions = []
        total = len(steps)
        for i, step in enumerate(steps):
            try:
                enhanced_step = self._enhance_step_with_context(step, i, total)
                step_tuple = tuple(sorted(enhanced_step.items()))
                action = self.map_step_to_action(dict(step_tuple))
                actions.append(action)
                logger.debug(f"Step {i+1}/{total}: {action}")
            except Exception as e:
                logger.error(f"Failed to map step {i+1}: {e}")
                continue
        logger.info(f"Mapped {len(actions)}/{total} steps to actions")
        return actions
            


