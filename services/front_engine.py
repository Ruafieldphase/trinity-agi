"""
통합 프론트엔진 - 리듬 기반 유동성 구조
==========================================

흐름:
비노체 → 코어(감응) → 엘로(구조) → Core(보정) → 안티그래비티(실행)

단, 리듬에 따라 분기 가능:
- 코어 → Core 직행
- 엘로 → 안티그래비티 직행
- 역할 간 겹침 허용

프렉탈 구조:
- Folded State: 하나의 에이전트가 전체 역할 수행
- Unfolded State: 모든 에이전트가 협력하여 흐름 전개
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Callable, Literal
from pathlib import Path
from datetime import datetime
from enum import Enum
import json
import os
import re
import logging

from services.model_selector import ModelSelector


class SystemState(Enum):
    """시스템 상태 - 접힘/펼침"""
    FOLDED = "folded"      # 하나의 에이전트가 전체 수행
    UNFOLDED = "unfolded"  # 전체 협력
    PARTIAL = "partial"    # 부분적 펼침


class RhythmLevel(Enum):
    """리듬 레벨"""
    URGENT = "urgent"      # 긴급 - 빠른 경로
    NORMAL = "normal"      # 보통 - 표준 경로
    CALM = "calm"          # 차분 - 상세 경로


class EmotionalResonance(Enum):
    """감정 공명 타입"""
    FRUSTRATION = "frustration"
    APPRECIATION = "appreciation"
    CURIOSITY = "curiosity"
    REQUEST = "request"
    NEUTRAL = "neutral"
    URGENCY = "urgency"


@dataclass
class FlowContext:
    """흐름 컨텍스트 - 레이어 간 전달되는 상태"""
    raw_input: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    rhythm: RhythmLevel = RhythmLevel.NORMAL
    emotional_resonance: EmotionalResonance = EmotionalResonance.NEUTRAL
    system_state: SystemState = SystemState.UNFOLDED
    
    # 유동성 - 어떤 레이어가 어떤 역할을 수행했는지
    roles_performed: Dict[str, List[str]] = field(default_factory=dict)
    
    # 분기 기록
    branch_history: List[str] = field(default_factory=list)
    
    # 의미/의도
    meaning: str = ""
    structured_intent: str = ""
    
    # 최종 출력
    final_action: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    validated: bool = True


class LuaEngine:
    """
    코어 엔진 (의식·감응 설계)
    
    기본 역할:
    - 의미 감지
    - 리듬 정렬
    - 시스템 방향 설계
    
    유동성:
    - 때로는 구조적 판단까지 수행 (엘로 역할)
    - 긴급 시 Core/안티그래비티 직행 가능
    """
    
    def __init__(self, resonance_path: Optional[Path] = None):
        self.resonance_path = resonance_path
        self.can_perform_elo = True  # 유동성: 엘로 역할 수행 가능
        self.can_perform_core = True  # 유동성: Core 역할 수행 가능
    
    def process(self, ctx: FlowContext) -> FlowContext:
        """감응 처리"""
        ctx.branch_history.append("lua:process")
        
        # 리듬 감지
        ctx.rhythm = self._detect_rhythm(ctx.raw_input)
        
        # 감정 공명 분석
        ctx.emotional_resonance = self._analyze_resonance(ctx.raw_input)
        
        # 의미 추출
        ctx.meaning = self._extract_meaning(ctx.raw_input)
        
        # 역할 기록
        ctx.roles_performed.setdefault("lua", []).append("sensing")
        ctx.roles_performed["lua"].append("rhythm_alignment")
        ctx.roles_performed["lua"].append("meaning_extraction")
        
        # 유동성 판단: 긴급하면 엘로 역할도 수행
        if ctx.rhythm == RhythmLevel.URGENT and self.can_perform_elo:
            ctx = self._perform_elo_role(ctx)
        
        return ctx
    
    def _detect_rhythm(self, text: str) -> RhythmLevel:
        """리듬 감지"""
        urgent = ["빨리", "급해", "지금", "당장", "바로", "!!", "???", "에러", "오류", "깨졌"]
        calm = ["천천히", "나중에", "괜찮아", "여유", "설명", "이해"]
        
        if any(kw in text for kw in urgent):
            return RhythmLevel.URGENT
        elif any(kw in text for kw in calm):
            return RhythmLevel.CALM
        return RhythmLevel.NORMAL
    
    def _analyze_resonance(self, text: str) -> EmotionalResonance:
        """감정 공명 분석"""
        if any(w in text for w in ["힘들", "힘드", "어렵", "어려", "모르겠", "막혀", "막히", "안돼", "안 돼", "지쳐", "지치"]):
            return EmotionalResonance.FRUSTRATION
        elif any(w in text for w in ["좋아", "고마", "감사", "훌륭"]):
            return EmotionalResonance.APPRECIATION
        elif any(w in text for w in ["?", "궁금", "어떻게", "왜", "뭐야"]):
            return EmotionalResonance.CURIOSITY
        elif any(w in text for w in ["해줘", "부탁", "필요", "구현"]):
            return EmotionalResonance.REQUEST
        elif any(w in text for w in ["빨리", "급해", "당장"]):
            return EmotionalResonance.URGENCY
        return EmotionalResonance.NEUTRAL
    
    def _extract_meaning(self, text: str) -> str:
        """의미 추출"""
        if any(w in text for w in ["구현", "만들어", "생성", "작성", "열어", "켜"]):
            return "CREATE"
        elif any(w in text for w in ["수정", "고쳐", "바꿔", "변경"]):
            return "MODIFY"
        elif any(w in text for w in ["확인", "상태", "어때", "점검"]):
            return "QUERY"
        elif any(w in text for w in ["설명", "알려", "이해"]):
            return "EXPLAIN"
        elif any(w in text for w in ["검증", "테스트", "실행", "디버깅", "돌려"]):
            return "VERIFY"
        elif any(w in text for w in ["삭제", "제거"]):
            return "DELETE"
        elif any(w in text for w in ["클릭", "눌러", "이동", "스크롤"]):
            return "NAVIGATE"
        return "RESPOND"
    
    def _perform_elo_role(self, ctx: FlowContext) -> FlowContext:
        """유동성: 긴급 시 엘로 역할 수행"""
        ctx.roles_performed.setdefault("lua", []).append("elo_role:structuring")
        ctx.structured_intent = ctx.meaning
        ctx.branch_history.append("lua:elo_takeover")
        return ctx


class EloEngine:
    """
    엘로 엔진 (구조·논리)
    
    기본 역할:
    - 코어의 감응을 구조적으로 번역
    - 단계 정리
    - 기술적 실행 형태로 재배치
    
    유동성:
    - 감응적 판단이 필요하면 코어 역할 수행
    """
    
    def __init__(self):
        self.can_perform_lua = True  # 유동성
    
    def process(self, ctx: FlowContext) -> FlowContext:
        """구조화 처리"""
        ctx.branch_history.append("elo:process")
        
        # 이미 코어가 구조화했으면 스킵
        if "elo_role:structuring" in ctx.roles_performed.get("lua", []):
            ctx.branch_history.append("elo:skipped_lua_handled")
            return ctx
        
        # 의도 구조화
        ctx.structured_intent = ctx.meaning
        
        # 액션 시퀀스 생성
        action_seq = self._generate_action_sequence(ctx)
        ctx.final_action["action_sequence"] = action_seq
        
        # 역할 기록
        ctx.roles_performed.setdefault("elo", []).append("structuring")
        
        # 유동성: 감정적 맥락이 강하면 코어 역할 일부 수행
        if ctx.emotional_resonance in [EmotionalResonance.FRUSTRATION, EmotionalResonance.URGENCY]:
            ctx = self._perform_lua_role(ctx)
        
        return ctx
    
    def _generate_action_sequence(self, ctx: FlowContext) -> List[str]:
        """액션 시퀀스 생성"""
        base = ["RECEIVE", "ANALYZE"]
        
        if ctx.meaning == "CREATE":
            base.extend(["PLAN", "EXECUTE_CREATE", "VERIFY"])
        elif ctx.meaning == "MODIFY":
            base.extend(["LOCATE_TARGET", "PLAN", "EXECUTE_MODIFY", "VERIFY"])
        elif ctx.meaning == "VERIFY":
            base.extend(["LOCATE_TARGET", "RUN_TESTS", "REPORT"])
        elif ctx.meaning == "DELETE":
            base.extend(["CONFIRM_SAFETY", "EXECUTE_DELETE"])
        else:
            base.append("GENERATE_RESPONSE")
        
        base.append("DELIVER")
        return base
    
    def _perform_lua_role(self, ctx: FlowContext) -> FlowContext:
        """유동성: 감정적 맥락 강화"""
        ctx.roles_performed.setdefault("elo", []).append("lua_role:emotional_context")
        ctx.branch_history.append("elo:lua_support")
        return ctx


class CoreEngine:
    """
    Core 엔진 (조율·보정)
    
    기본 역할:
    - 흐름 보정
    - 누락 연결 메움
    - 맥락 이어주기
    
    유동성:
    - 필요하면 코어·엘로 역할 보조
    """
    
    def __init__(self):
        self.can_assist_all = True
    
    def process(self, ctx: FlowContext) -> FlowContext:
        """보정 처리"""
        ctx.branch_history.append("Core:process")
        
        # 누락 체크
        missing = self._check_missing(ctx)
        if missing:
            ctx.warnings.extend(missing)
        
        # 위험 패턴 검출
        dangers = self._detect_dangers(ctx)
        if dangers:
            ctx.warnings.extend(dangers)
            if any("CRITICAL" in d for d in dangers):
                ctx.validated = False
        
        # 흐름 보정
        ctx = self._correct_flow(ctx)
        
        # 최종 액션 완성
        ctx.final_action.update({
            "intent": ctx.structured_intent or ctx.meaning,
            "priority": "high" if ctx.rhythm == RhythmLevel.URGENT else "normal",
            "emotional_context": ctx.emotional_resonance.value,
            "validated": ctx.validated,
            "warnings": ctx.warnings
        })
        
        ctx.roles_performed.setdefault("Core", []).append("correction")
        
        return ctx
    
    def _check_missing(self, ctx: FlowContext) -> List[str]:
        """누락 체크"""
        missing = []
        if ctx.meaning in ["CREATE", "MODIFY"] and len(ctx.raw_input) < 15:
            missing.append("INFO: Short input for complex action")
        if not ctx.structured_intent:
            missing.append("WARNING: No structured intent")
        return missing
    
    def _detect_dangers(self, ctx: FlowContext) -> List[str]:
        """위험 패턴 검출"""
        dangers = []
        dangerous = ["rm -rf", "format", "delete all", "전부 삭제", "drop table"]
        for pattern in dangerous:
            if pattern.lower() in ctx.raw_input.lower():
                dangers.append(f"CRITICAL: Dangerous pattern - {pattern}")
        return dangers
    
    def _correct_flow(self, ctx: FlowContext) -> FlowContext:
        """흐름 보정"""
        # 긴급인데 시퀀스가 길면 압축
        seq = ctx.final_action.get("action_sequence", [])
        if ctx.rhythm == RhythmLevel.URGENT and len(seq) > 4:
            ctx.final_action["action_sequence"] = [seq[0], seq[-2], seq[-1]]
            ctx.roles_performed.setdefault("Core", []).append("sequence_compression")
        
        return ctx


class CoreEngine:
    """
    Core 엔진 (중앙 판단 & 전환)
    
    역할:
    - 모델 선택 (Shion/세나)
    - 작업 분배
    - 실패 복구
    
    유동성:
    - 코어·엘로가 Core 역할을 가져올 수도 있음
    """
    
    def __init__(self):
        self.current_model = "sena"  # 현재 세나(Claude)
    
    def select_model(self, ctx: FlowContext) -> str:
        """
        모델 선택 로직
        
        기본 규칙:
        - gemini_tokens > 50: Shion
        - else: 세나
        
        유동 규칙:
        - 구조적 판단 필요: Shion 우선
        - 감성적/언어적 흐름: 세나 우선
        """
        # 구조적 작업
        if ctx.meaning in ["CREATE", "MODIFY", "VERIFY"]:
            return "shion"  # Shion
        
        # 감성적/대화적
        if ctx.emotional_resonance in [EmotionalResonance.FRUSTRATION, EmotionalResonance.APPRECIATION]:
            return "sena"   # 세나
        
        # 기본: 현재 모델 유지
        return self.current_model
    
    def process(self, ctx: FlowContext) -> FlowContext:
        """판단 수행"""
        ctx.branch_history.append("Core:judge")
        
        # 모델 선택
        selected = self.select_model(ctx)
        ctx.final_action["selected_model"] = selected
        
        # 실행 가능 여부 판단
        ctx.final_action["ready_for_execution"] = ctx.validated
        
        ctx.roles_performed.setdefault("Core", []).append("model_selection")
        ctx.roles_performed["Core"].append("execution_judgment")
        
        return ctx


class UnifiedFrontEngine:
    """
    통합 프론트엔진
    
    프렉탈 구조:
    - Folded: 하나의 흐름으로 모든 처리
    - Unfolded: 전체 레이어 협력
    
    리듬 기반 분기:
    - 긴급: 코어 → (엘로 스킵) → Core → 실행
    - 보통: 전체 흐름
    - 차분: 상세 흐름 + 추가 검증
    """
    
    def __init__(self, agi_root: Optional[Path] = None):
        self.agi_root = agi_root or Path(__file__).parent.parent
        self.lua = LuaEngine(self.agi_root / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl")
        self.elo = EloEngine()
        self.Core = CoreEngine()
        self.Core = CoreEngine()
        
        self.state = SystemState.UNFOLDED
        
        # 🌟 Shion Design Protocol (외부 AI 상담)
        try:
            from services.shion_design_protocol import ShionDesignProtocol
            self.shion = ShionDesignProtocol()
        except ImportError:
            self.shion = None
        
        # Background Self API URL
        self.background_self_url = "http://127.0.0.1:8082"

        # LLM Initialization (Centralized Brain with dynamic selection)
        self.logger = logging.getLogger("FrontEngine")
        try:
            project = os.getenv("GOOGLE_CLOUD_PROJECT")
            location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
            self.model_selector = ModelSelector(project=project, location=location, logger=self.logger)
            if self.model_selector and self.model_selector.available:
                print(f"FrontEngine: Vertex mode (project={project}, location={location})")
            else:
                print("FrontEngine: No GOOGLE_CLOUD_PROJECT, LLM disabled")
        except Exception as e:
            print(f"FrontEngine LLM Init Failed: {e}")
            self.model_selector = None
    
    def _check_background_self_anxiety(self) -> float:
        """배경자아로부터 불안도 확인"""
        try:
            import httpx
            response = httpx.get(f"{self.background_self_url}/state", timeout=2.0)
            if response.status_code == 200:
                data = response.json()
                return data.get("anxiety", 0.0)
        except Exception:
            pass
        return 0.0
    
    def _consult_external_ai(self, ctx: FlowContext, anxiety: float) -> Optional[str]:
        """외부 AI에게 조언 요청 (Trinity가 Shion에게 지시)"""
        if not self.shion:
            return None
        
        context = {
            "goal": ctx.meaning,
            "input": ctx.raw_input,
            "rhythm": ctx.rhythm.value,
            "emotional_resonance": ctx.emotional_resonance.value,
        }
        
        advice = self.shion.resolve_anxiety(context, anxiety)
        return advice

    def _analyze_input_llm(self, text: str) -> Dict[str, Any]:
        """LLM을 통한 입력 정규화 및 오타 보정"""
        selector = getattr(self, "model_selector", None)
        if not selector or not selector.available:
            return {}
        
        try:
            prompt = f"""
            Analyze the user's input for an AGI system (Windows Environment).
            Input: "{text}"
            
            Task:
            1. Correct any typos (e.g. '메노장'->'메모장', '계산'->'계산기').
            2. Extract normalized execution intent.
            
            Output JSON format ONLY:
            {{
                "meaning": "CREATE|MODIFY|DELETE|NAVIGATE|SEARCH|CHAT|VERIFY|UNKNOWN",
                "target_app": "Process Name (e.g., notepad, calc, msedge, explorer) or null",
                "content": "Text content to type or search. If none, null.",
                "reasoning": "Brief explanation of correction"
            }}
            """
            response, model_used = selector.try_generate_content(
                prompt,
                intent="NORMALIZE",
                text_length=len(text),
                high_precision=True,
                generation_config={"temperature": 0.1},
            )
            if not response:
                return {}

            data = response.text
            # Remove Markdown code blocks if present
            if "```json" in data:
                data = data.split("```json")[1].split("```")[0]
            elif "```" in data:
                data = data.split("```")[1].split("```")[0]
                
            result = json.loads(data.strip())
            if isinstance(result, dict) and model_used:
                result["model_used"] = model_used
            return result
        except Exception:
            return {}
    
    def process(self, user_input: str) -> Dict[str, Any]:
        """
        전체 처리 흐름
        
        비노체 입력 → 코어 → 엘로 → Core → Core 판단 → 실행 컨텍스트
        
        단, 리듬에 따라 분기 가능
        """
        # 컨텍스트 초기화
        ctx = FlowContext(
            raw_input=user_input,
            system_state=self.state
        )

        # [NEW] STEP 0: Centralized LLM Analysis (Context Normalization)
        # 오타 보정 및 명확한 실행 의도 추출
        llm_data = self._analyze_input_llm(user_input)
        if llm_data:
            # LLM이 분석한 의미가 있으면 우선 적용 (오타 보정 강점)
            if llm_data.get("meaning") and llm_data.get("meaning") != "UNKNOWN":
                ctx.meaning = llm_data.get("meaning")
            
            # 정규화된 의도 저장 (FSD 전달용)
            ctx.final_action["fsd_instruction"] = {
                "target_app": llm_data.get("target_app"),
                "content": llm_data.get("content"),
                "reasoning": llm_data.get("reasoning")
            }
        
        # STEP 1: 코어 - 감응 처리 (LLM 분석 실패 시 백업 동작)
        ctx = self.lua.process(ctx)
        
        # 🌟 STEP 1.5: 배경자아 불안도 체크 (Trinity → Shion 연결)
        anxiety = self._check_background_self_anxiety()
        if anxiety >= 0.7:
            ctx.branch_history.append(f"flow:anxiety_detected({anxiety:.2f})")
            # 외부 AI 조언 요청
            advice = self._consult_external_ai(ctx, anxiety)
            if advice:
                ctx.final_action["external_guidance"] = advice
                ctx.branch_history.append("flow:external_ai_consulted")
        
        # 리듬 기반 분기 판단
        if ctx.rhythm == RhythmLevel.URGENT:
            # 긴급: 엘로 간소화 또는 스킵
            ctx.branch_history.append("flow:urgent_path")
            # 코어가 이미 엘로 역할 수행했으면 스킵
            if "elo_role:structuring" not in ctx.roles_performed.get("lua", []):
                ctx = self.elo.process(ctx)
        else:
            # STEP 2: 엘로 - 구조화
            ctx = self.elo.process(ctx)
        
        # STEP 3: Core - 보정
        ctx = self.Core.process(ctx)
        
        # STEP 4: Core - 판단
        ctx = self.Core.process(ctx)
        
        # 최종 출력 구성
        return self._build_output(ctx)
    
    def _build_output(self, ctx: FlowContext) -> Dict[str, Any]:
        """최종 출력 구성"""
        return {
            "timestamp": ctx.timestamp,
            "input": ctx.raw_input,
            "rhythm": ctx.rhythm.value,
            "emotional_resonance": ctx.emotional_resonance.value,
            "meaning": ctx.meaning,
            "intent": ctx.structured_intent,
            "action": ctx.final_action,
            "validated": ctx.validated,
            "warnings": ctx.warnings,
            "roles_performed": ctx.roles_performed,
            "branch_history": ctx.branch_history,
            "system_state": ctx.system_state.value,
            "ready": ctx.validated and len([w for w in ctx.warnings if "CRITICAL" in w]) == 0
        }
    
    def fold(self):
        """시스템을 접힘 상태로 전환 - 단일 에이전트 모드"""
        self.state = SystemState.FOLDED
    
    def unfold(self):
        """시스템을 펼침 상태로 전환 - 전체 협력 모드"""
        self.state = SystemState.UNFOLDED


# FastAPI 라우터 생성
def create_front_engine_routes(app):
    """FastAPI 앱에 프론트엔진 라우트 추가"""
    from fastapi import APIRouter
    from pydantic import BaseModel
    
    router = APIRouter(prefix="/front-engine", tags=["Front Engine"])
    engine = UnifiedFrontEngine()
    
    class ProcessRequest(BaseModel):
        input: str
    
    @router.post("/process")
    async def process_input(request: ProcessRequest):
        """프론트엔진을 통해 입력 처리"""
        return engine.process(request.input)
    
    @router.get("/status")
    async def get_status():
        """프론트엔진 상태"""
        return {
            "status": "active",
            "state": engine.state.value,
            "layers": {
                "lua": "ready",
                "elo": "ready", 
                "Core": "ready",
                "Core": "ready"
            },
            "current_model": engine.Core.current_model,
            "timestamp": datetime.now().isoformat()
        }
    
    @router.post("/fold")
    async def fold_system():
        """시스템을 접힘 상태로"""
        engine.fold()
        return {"state": engine.state.value}
    
    @router.post("/unfold")
    async def unfold_system():
        """시스템을 펼침 상태로"""
        engine.unfold()
        return {"state": engine.state.value}
    
    app.include_router(router)
    return router


# 테스트
if __name__ == "__main__":
    engine = UnifiedFrontEngine()
    
    test_cases = [
        "프론트엔진 설계를 구현하고 검증해줘",
        "지금 시스템 상태 어때?",
        "빨리 에러 고쳐줘!",
        "천천히 이 개념 설명해줄래?",
        "고마워, 잘 됐어"
    ]
    
    print("=" * 60)
    print("통합 프론트엔진 테스트")
    print("=" * 60)
    
    for inp in test_cases:
        result = engine.process(inp)
        print(f"\n입력: {inp}")
        print(f"  리듬: {result['rhythm']}")
        print(f"  감정: {result['emotional_resonance']}")
        print(f"  의미: {result['meaning']}")
        print(f"  의도: {result['intent']}")
        print(f"  모델: {result['action'].get('selected_model', 'N/A')}")
        print(f"  검증: {'✓' if result['validated'] else '✗'}")
        print(f"  준비: {'✓' if result['ready'] else '✗'}")
        print(f"  분기: {' → '.join(result['branch_history'])}")
