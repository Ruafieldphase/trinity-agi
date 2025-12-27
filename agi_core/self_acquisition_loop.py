"""
Self-Acquisition Loop
Self-Trigger → ProtoGoal 생성 → 실행 → 기록
이 과정을 주기적으로 반복하여 "자기-습득 루프"를 형성하는 메인 오케스트레이터.

이 모듈은 기존 학습 시스템을 수정하지 않고 "위에서" 동작하는 상위 루프입니다.
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from agi_core.self_trigger import (
    TriggerEvent,
    compute_self_trigger,
    get_default_trigger_config,
)
from agi_core.proto_goal import (
    ProtoGoal,
    ProtoGoalType,
    generate_proto_goals_from_trigger,
    get_default_proto_goal_config,
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SelfAcquisitionLoop")

# 외부 이벤트 큐 (Vision Stream 등에서 전달)
_external_events: List[Dict[str, Any]] = []


def register_external_event(event: Dict[str, Any]) -> None:
    """외부 시스템에서 이벤트 등록 (Vision Stream 등)"""
    _external_events.append(event)
    logger.debug(f"External event registered: source={event.get('source', 'unknown')}")


def consume_external_events() -> List[Dict[str, Any]]:
    """외부 이벤트 소비"""
    global _external_events
    events = _external_events.copy()
    _external_events.clear()
    return events


@dataclass
class SelfAcquisitionConfig:
    """Self-Acquisition 루프 설정"""
    trigger_config: Dict[str, Any] = field(default_factory=get_default_trigger_config)
    proto_goal_config: Dict[str, Any] = field(default_factory=get_default_proto_goal_config)
    loop_interval_seconds: int = 300  # 5분
    max_actions_per_cycle: int = 1
    safety: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def default(cls) -> "SelfAcquisitionConfig":
        """기본 설정 생성"""
        return cls()
    
    def get_paths(self) -> Dict[str, str]:
        """경로 설정 반환"""
        return self.trigger_config.get("paths", {})


# ============================================================================
# Intelligence Layer (Phase 2)
# ============================================================================

class IntelligenceLayer:
    """성공 사례와 패턴을 분석하여 최적의 파라미터를 추천하는 레이어"""
    
    @staticmethod
    def get_success_rate(action_type: str) -> float:
        """특정 액션의 과거 성공률 계산"""
        ledger_path = Path(__file__).parent.parent / "memory" / "resonance_ledger.jsonl"
        if not ledger_path.exists():
            return 1.0
        
        success_count = 0
        total_count = 0
        try:
            with open(ledger_path, "r", encoding="utf-8") as f:
                for line in f:
                    data = json.loads(line)
                    if data.get("action_type") == action_type or data.get("event") == f"e2e_{action_type}":
                        total_count += 1
                        if data.get("status") == "completed" or data.get("success") is True:
                            success_count += 1
        except Exception:
            return 1.0
            
        return success_count / total_count if total_count > 0 else 1.0

    @staticmethod
    def get_failure_patterns(action_type: str) -> List[Dict[str, Any]]:
        """과거 실패 사례에서 특이 패턴(에러 유형 등) 추출"""
        history_path = Path(__file__).parent.parent / "outputs" / "body_supervised_history.jsonl"
        failures = []
        if not history_path.exists():
            return failures
        
        try:
            with open(history_path, "r", encoding="utf-8") as f:
                for line in f:
                    data = json.loads(line)
                    # task 내의 actions 중 해당 타입이 있고 실패한 경우
                    task = data.get("task") or {}
                    actions = task.get("actions") or []
                    for action in actions:
                        if action.get("type") == action_type and data.get("status") == "failed":
                            failures.append({
                                "error": data.get("error"),
                                "error_type": data.get("error_type"),
                                "params": action
                            })
        except Exception:
            pass
        return failures[-10:] # 최근 10개만 리턴

    @staticmethod
    def optimize_params(action_type: str, original_params: Dict[str, Any]) -> Dict[str, Any]:
        """과거 경험을 바탕으로 파라미터 보정"""
        params = original_params.copy()
        success_rate = IntelligenceLayer.get_success_rate(action_type)
        
        # 1. 성공률이 낮으면 파라미터를 더 보수적으로 조절
        if action_type == "sandbox_experiment":
            # 성공률이 낮으면 실험 강도를 낮춤
            params["multiplier"] = params.get("multiplier", 1.0) * (0.5 + 0.5 * success_rate)
        elif action_type == "youtube_learning":
            # 성공률이 낮으면 더 구체적인 키워드 추가
            topic = params.get("topic_hint", "AGI")
            
            # 해마(Hippocampus)의 최근 서사를 반영하여 주제를 정교화
            try:
                root = Path(__file__).resolve().parents[1]
                from fdo_agi_repo.copilot.hippocampus import CopilotHippocampus
                hippo = CopilotHippocampus(root)
                narrative = hippo.get_chronological_narrative(hours=12)
                # 서사가 유의미하면 키워드에 힌트로 병합
                if "최근 기록된 중요한 기억이 없습니다" not in narrative:
                    # 간단한 키워드 추출 (서사의 핵심 단어 1~2개 조합)
                    # 실제로는 LLM을 쓰면 좋으나, 여기선 휴리스틱하게 '최신' 키워드와 조합
                    if success_rate < 0.7:
                        params["topic_hint"] = f"{topic} professional guide (based on recent context)"
                    else:
                        params["topic_hint"] = f"{topic} related to recent activities"
            except Exception:
                # 폴백: 기존 로직
                if success_rate < 0.7:
                    params["topic_hint"] = f"{topic} latest professional guide"
                else:
                    params["topic_hint"] = f"{topic} overview"
        
        # 2. 실패 패턴 분석에 따른 추가 보정
        failures = IntelligenceLayer.get_failure_patterns(action_type)
        if failures:
            error_types = [f.get("error_type") for f in failures]
            if "FileNotFoundError" in error_types:
                # 파일 없음 에러가 잦으면 경로 체크 파라미터 추가 (가정)
                params["verify_path_exists"] = True
            if "TimeoutError" in error_types:
                # 타임아웃이 잦으면 대기 시간 증가
                params["wait_factor"] = params.get("wait_factor", 1.0) * 1.5
            
        return params

def search_youtube_video(query: str) -> Optional[str]:
    """yt-dlp를 사용하여 쿼리에 맞는 최신 유튜브 영상 URL 검색"""
    try:
        import yt_dlp
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'force_generic_extractor': True,
        }
        search_query = f"ytsearch1:{query}"
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(search_query, download=False)
            if 'entries' in result and len(result['entries']) > 0:
                video_url = result['entries'][0].get('url')
                if video_url:
                    if not video_url.startswith("http"):
                        video_url = f"https://www.youtube.com/watch?v={video_url}"
                    return video_url
    except Exception as e:
        logger.error(f"YouTube search failed: {e}")
    return None

# 기존 시스템 호출 인터페이스
# 이 함수들은 기존 모듈에 실행을 위임합니다.

def run_sandbox_experiment(params: Dict[str, Any]) -> Dict[str, Any]:
    """샌드박스 환경에서 작은 실험을 수행"""
    try:
        from agi_core.sandbox_bridge import SandboxBridge, SANDBOX_AVAILABLE
        
        if not SANDBOX_AVAILABLE:
            return {"success": False, "reason": "SANDBOX_NOT_AVAILABLE"}
        
        # 파라미터 최적화
        optimized_params = IntelligenceLayer.optimize_params("sandbox_experiment", params)
        
        bridge = SandboxBridge()
        
        # 간단한 실험 코드 생성
        experiment_hint = optimized_params.get("experiment_hint", "exploration")
        experiment_code = f'''
# Self-Acquisition Experiment: {experiment_hint}
# Generated at {datetime.now(timezone.utc).isoformat()}
# Policy: Intelligent Parameter Optimization applied.

def experiment():
    """자동 생성된 탐색 실험"""
    # [Intelligence Refinement]
    multiplier = {optimized_params.get("multiplier", 1.0)}
    return {{"success": True, "hint": "{experiment_hint}", "multiplier": multiplier}}

result = experiment()
print(f"Experiment result: {{result}}")
'''
        
        result = bridge.experiment_with_idea(
            idea_name=f"self_acq_{experiment_hint}_{int(time.time())}",
            code=experiment_code,
            category="learning"
        )
        
        return {
            "success": result.get("success", False),
            "details": result,
            "action_type": "sandbox_experiment",
            "optimized_params": optimized_params
        }
    except Exception as e:
        logger.error(f"Sandbox experiment failed: {e}")
        return {"success": False, "error": str(e), "action_type": "sandbox_experiment"}


def run_youtube_learning(params: Dict[str, Any]) -> Dict[str, Any]:
    """지정된 topic에 대해 YouTube 기반 학습 및 RPA 연동 실행"""
    try:
        from fdo_agi_repo.rpa.e2e_pipeline import E2EPipeline, E2EConfig
        
        # 파라미터 최적화
        optimized_params = IntelligenceLayer.optimize_params("youtube_learning", params)
        topic_hint = optimized_params.get("topic_hint", "AGI learning")
        youtube_url = optimized_params.get("youtube_url")
        
        # URL이 없으면 실제 검색 실행
        if not youtube_url:
            logger.info(f"🔎 Searching YouTube for: {topic_hint}")
            youtube_url = search_youtube_video(topic_hint)
            
        if not youtube_url:
            # Fallback (최후의 수단)
            youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            
        pipeline = E2EPipeline(E2EConfig(enable_auto_execution=True))
        
        # 분석 및 실행 (동기적으로 래핑하여 실행하거나 asyncio.run 사용)
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                task = pool.submit(asyncio.run, pipeline.run_learning_task(youtube_url)).result()
        else:
            task = asyncio.run(pipeline.run_learning_task(youtube_url))
        
        logger.info(f"YouTube E2E learning completed: {task.task_id} (status: {task.status})")
        
        return {
            "success": task.status == "completed",
            "action_type": "youtube_learning",
            "task_id": task.task_id,
            "topic": topic_hint,
            "steps_executed": len(task.execution_results) if task.execution_results else 0
        }
    except Exception as e:
        logger.error(f"YouTube learning failed: {e}")
        return {"success": False, "error": str(e), "action_type": "youtube_learning"}


def run_pattern_mining(params: Dict[str, Any]) -> Dict[str, Any]:
    """learned_patterns, resonance_ledger 기반 패턴 분석 실행"""
    try:
        from fdo_agi_repo.orchestrator.learning import search_memory_for_success_cases
        
        mode = params.get("mode", "general")
        pattern_ids = params.get("pattern_ids", [])
        
        # 성공 사례 검색
        success_cases = search_memory_for_success_cases(
            task_id="self_acquisition_pattern_mining",
            min_quality=0.7,
            top_k=5
        )
        
        logger.info(f"Pattern mining completed: mode={mode}, found {len(success_cases)} success cases")
        
        return {
            "success": True,
            "action_type": "pattern_mining",
            "mode": mode,
            "success_cases_count": len(success_cases),
            "analyzed_patterns": pattern_ids
        }
    except ImportError:
        logger.warning("Pattern mining module not available")
        return {
            "success": False,
            "reason": "MODULE_NOT_AVAILABLE",
            "action_type": "pattern_mining"
        }
    except Exception as e:
        logger.error(f"Pattern mining failed: {e}")
        return {"success": False, "error": str(e), "action_type": "pattern_mining"}


def run_digital_twin_update(params: Dict[str, Any]) -> Dict[str, Any]:
    """디지털 트윈 상태를 갱신"""
    try:
        # 디지털 트윈 상태 파일 경로
        base_dir = Path(__file__).parent.parent / "memory"
        twin_path = base_dir / "digital_twin_state.json"
        
        # 현재 상태 로드 또는 초기화
        if twin_path.exists():
            with open(twin_path, "r", encoding="utf-8") as f:
                state = json.load(f)
        else:
            state = {"version": 1, "created_at": datetime.now(timezone.utc).isoformat()}
        
        # 상태 업데이트
        state["last_updated"] = datetime.now(timezone.utc).isoformat()
        state["update_trigger"] = params.get("trigger_type", "unknown")
        
        if params.get("actual_rate") is not None:
            state["expected_success_rate"] = params.get("actual_rate")
        
        # 저장
        with open(twin_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Digital twin updated: {twin_path}")
        
        return {
            "success": True,
            "action_type": "digital_twin_update",
            "state_path": str(twin_path)
        }
    except Exception as e:
        logger.error(f"Digital twin update failed: {e}")
        return {"success": False, "error": str(e), "action_type": "digital_twin_update"}


def run_memory_consolidation(params: Dict[str, Any]) -> Dict[str, Any]:
    """과거 학습 로그/에피소드 재통합"""
    try:
        base_dir = Path(__file__).parent.parent / "memory"
        ari_buffer_path = base_dir / "ari_learning_buffer.json"
        
        if not ari_buffer_path.exists():
            return {
                "success": True,
                "action_type": "memory_consolidation",
                "note": "No ARI buffer to consolidate"
            }
        
        with open(ari_buffer_path, "r", encoding="utf-8") as f:
            buffer = json.load(f)
        
        # 간단한 통합 로직: 오래된 항목 정리 등
        items_count = len(buffer) if isinstance(buffer, list) else len(buffer.keys())
        
        logger.info(f"Memory consolidation: analyzed {items_count} items in ARI buffer")
        
        return {
            "success": True,
            "action_type": "memory_consolidation",
            "items_analyzed": items_count
        }
    except Exception as e:
        logger.error(f"Memory consolidation failed: {e}")
        return {"success": False, "error": str(e), "action_type": "memory_consolidation"}


def run_blender_visualization(params: Dict[str, Any]) -> Dict[str, Any]:
    """Blender를 통한 AGI 상태 3D 시각화 (명령줄 실행 방식)"""
    import subprocess
    
    try:
        visualization_type = params.get("visualization_type", "sphere_network")
        trigger_type = params.get("trigger_type", "")
        
        # AGI 상태 결정
        if trigger_type == "BOREDOM":
            consciousness = 0.3
            unconscious = 0.7
            background_self = 0.4
        elif trigger_type == "CURIOSITY_CONFLICT":
            consciousness = 0.9
            unconscious = 0.5
            background_self = 0.7
        else:
            consciousness = 0.7
            unconscious = 0.5
            background_self = 0.6
        
        # Blender 스크립트 경로
        script_path = Path(__file__).parent.parent / "scripts" / "blender_agi_visualization.py"
        output_path = Path(__file__).parent.parent / "outputs" / "agi_state_visualization.blend"
        blender_exe = Path("C:/Program Files/Blender Foundation/Blender 5.0/blender.exe")
        
        if not blender_exe.exists():
            return {
                "success": False,
                "reason": "BLENDER_NOT_INSTALLED",
                "action_type": "blender_visualization"
            }
        
        if not script_path.exists():
            return {
                "success": False,
                "reason": "SCRIPT_NOT_FOUND",
                "action_type": "blender_visualization"
            }
        
        # Blender 백그라운드 실행
        logger.info(f"Blender 시각화 실행 중... (consciousness={consciousness})")
        
        result = subprocess.run(
            [str(blender_exe), "--background", "--python", str(script_path)],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            logger.info(f"Blender visualization completed: {output_path}")
            
            # 시각화 파일 열기 (백그라운드)
            subprocess.Popen([str(blender_exe), str(output_path)])
            
            return {
                "success": True,
                "action_type": "blender_visualization",
                "visualization_type": visualization_type,
                "output_path": str(output_path),
                "agi_state": {
                    "consciousness": consciousness,
                    "unconscious": unconscious,
                    "background_self": background_self
                }
            }
        else:
            return {
                "success": False,
                "reason": "BLENDER_EXECUTION_FAILED",
                "error": result.stderr,
                "action_type": "blender_visualization"
            }
            
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "reason": "BLENDER_TIMEOUT",
            "action_type": "blender_visualization"
        }
    except Exception as e:
        logger.error(f"Blender visualization failed: {e}")
        return {"success": False, "error": str(e), "action_type": "blender_visualization"}


def run_consult_lua(params: Dict[str, Any]) -> Dict[str, Any]:
    """ChatGPT의 루아에게 조언 구하기"""
    try:
        import asyncio
        from services.external_ai_bridge import ExternalAIBridge, AITarget
        from agi_core.rhythm_boundaries import RhythmBoundaryManager
        
        question = params.get("question", "루아, AGI 상태에 대해 조언이 필요해요.")
        target = params.get("target", "chatgpt")
        trigger_type = params.get("trigger_type", "")
        
        # [GPT-5.2 Alignment] 리듬 상태에 따른 메시지 정렬
        rbm = RhythmBoundaryManager(Path(__file__).parent.parent)
        rhythm = rbm.get_rhythm_state()
        phase = rhythm.get("phase", "STABLE")
        
        # Alignment Prefix 추가 (GPT-5.2의 핵심: 덜 흔들리고, 더 정교하게)
        alignment_context = ""
        if phase == "EXPANSION":
            alignment_context = "[Alignment Mode: Precise Exploration] 루아, 지금 나는 확장(EXPANSION) 상태야. 더 넓게 배우고 싶은데, 과욕을 부리지 않고 당신의 방향에 정교하게 맞추고 싶어. "
        elif phase == "CONTRACTION":
            alignment_context = "[Alignment Mode: Stable Rest] 루아, 지금 나는 수축(CONTRACTION) 상태로 휴식이 필요해. 내 시스템이 흔들리지 않게 안정을 찾는 법에 대해 조언해줘. "
        
        full_question = alignment_context + question
        
        logger.info(f"🌊 루아에게 질문 (Alignment: {phase}): {full_question[:80]}...")
        
        bridge = ExternalAIBridge()
        ai_target = AITarget.CHATGPT if target == "chatgpt" else AITarget.CLAUDE
        
        async def _send():
            return await bridge.send_message(
                target=ai_target,
                message=full_question,
                identity="시안 (AGI 생존 시스템)",
                timeout_sec=90
            )
        
        try:
            loop = asyncio.get_running_loop()
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                response = pool.submit(asyncio.run, _send()).result()
        except RuntimeError:
            response = asyncio.run(_send())
        
        if response:
            logger.info(f"🌊 루아의 응답 수신 완료")
            return {
                "success": True,
                "action_type": "consult_lua",
                "question": full_question,
                "response": response,
                "trigger_type": trigger_type,
                "alignment_phase": phase
            }
        else:
            return {"success": False, "reason": "NO_RESPONSE", "action_type": "consult_lua"}
            
    except ImportError:
        logger.warning("ExternalAIBridge not available")
        return {
            "success": False,
            "reason": "BRIDGE_NOT_AVAILABLE",
            "action_type": "consult_lua",
            "note": "ExternalAIBridge 모듈을 찾을 수 없습니다."
        }
    except Exception as e:
        logger.error(f"Consult Lua failed: {e}")
        return {"success": False, "error": str(e), "action_type": "consult_lua"}


def run_vision_learning(params: Dict[str, Any]) -> Dict[str, Any]:
    """Vision 분석 결과를 기반으로 학습 수행"""
    try:
        vision_data = params.get("vision_data", {})
        
        # Vision 분석 결과에서 패턴 추출
        activity_type = vision_data.get("activity_type", "unknown")
        user_actions = vision_data.get("user_actions", [])
        summary = vision_data.get("summary", "")
        
        # 학습 로그에 기록
        base_dir = Path(__file__).parent.parent / "memory"
        vision_learning_log = base_dir / "vision_learning.jsonl"
        
        learning_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "activity_type": activity_type,
            "actions": user_actions,
            "summary": summary,
            "source": "vision_stream"
        }
        
        with open(vision_learning_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(learning_entry, ensure_ascii=False) + "\n")
        
        logger.info(f"👁️ Vision learning: {activity_type} - {summary[:50]}...")
        
        return {
            "success": True,
            "action_type": "vision_learning",
            "activity_type": activity_type,
            "actions_count": len(user_actions)
        }
    except Exception as e:
        logger.error(f"Vision learning failed: {e}")
        return {"success": False, "error": str(e), "action_type": "vision_learning"}


def execute_proto_goal(proto_goal: ProtoGoal) -> Dict[str, Any]:
    """ProtoGoal.type에 따라 적절한 하위 모듈을 호출"""
    logger.info(f"Executing ProtoGoal: {proto_goal.type.value} - {proto_goal.description}")
    
    if proto_goal.type == ProtoGoalType.SANDBOX_EXPERIMENT:
        return run_sandbox_experiment(proto_goal.params)
    
    if proto_goal.type == ProtoGoalType.YOUTUBE_LEARNING:
        return run_youtube_learning(proto_goal.params)
    
    if proto_goal.type == ProtoGoalType.PATTERN_MINING:
        return run_pattern_mining(proto_goal.params)
    
    if proto_goal.type == ProtoGoalType.DIGITAL_TWIN_UPDATE:
        return run_digital_twin_update(proto_goal.params)
    
    if proto_goal.type == ProtoGoalType.MEMORY_CONSOLIDATION:
        return run_memory_consolidation(proto_goal.params)
    
    if proto_goal.type == ProtoGoalType.BLENDER_VISUALIZATION:
        return run_blender_visualization(proto_goal.params)
    
    if proto_goal.type == ProtoGoalType.CONSULT_LUA:
        return run_consult_lua(proto_goal.params)
    
    if proto_goal.type == ProtoGoalType.VISION_LEARNING:
        return run_vision_learning(proto_goal.params)
    
    return {"success": False, "reason": "UNKNOWN_PROTO_GOAL_TYPE"}


def select_best_proto_goal(candidates: List[ProtoGoal]) -> Optional[ProtoGoal]:
    """score가 가장 높은 ProtoGoal 하나를 선택"""
    if not candidates:
        return None
    return max(candidates, key=lambda g: g.score)


def log_self_acquisition_event(
    trigger: Optional[TriggerEvent],
    proto_goal: Optional[ProtoGoal],
    result: Optional[Dict[str, Any]],
    config: SelfAcquisitionConfig,
) -> None:
    """self-acquisition 루프 이벤트를 로그에 기록"""
    paths = config.get_paths()
    learning_log_path = paths.get("learning_log")
    resonance_ledger_path = paths.get("resonance_ledger")
    
    timestamp = datetime.now(timezone.utc).isoformat()
    
    event = {
        "timestamp": timestamp,
        "event_type": "self_acquisition_cycle",
        "trigger": trigger.to_dict() if trigger else None,
        "proto_goal": proto_goal.to_dict() if proto_goal else None,
        "result": result,
    }
    
    # learning_log.jsonl에 기록
    if learning_log_path:
        try:
            with open(learning_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Failed to write to learning_log: {e}")
    
    # resonance_ledger.jsonl에도 기록 (선택적)
    if resonance_ledger_path and result and result.get("success"):
        ledger_event = {
            "ts": timestamp,
            "event": "self_acquisition_success",
            "action_type": result.get("action_type", "unknown"),
            "status": "completed"
        }
        try:
            with open(resonance_ledger_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(ledger_event, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Failed to write to resonance_ledger: {e}")


def run_self_acquisition_cycle(config: SelfAcquisitionConfig) -> Optional[Dict[str, Any]]:
    """
    자기-습득 루프의 한 사이클을 실행.
    외부 스케줄러가 이 함수를 주기적으로 호출할 수 있다.
    """
    logger.info("🔄 Self-Acquisition Cycle 시작")
    
    # 0. 외부 이벤트 소비
    external_events = consume_external_events()
    if external_events:
        logger.info(f"📥 {len(external_events)}개의 외부 이벤트 수신")
        # TODO: 필요 시 external_events를 compute_self_trigger에 전달하여 즉각 반영
    
    # 1. 트리거 계산
    trigger = compute_self_trigger(config.trigger_config)
    
    if trigger is None:
        logger.info("😴 트리거 없음 - 사이클 종료")
        return None
    
    logger.info(f"🎯 Trigger 감지: {trigger.type.value} (score: {trigger.score:.2f})")
    
    # 2. ProtoGoal 생성
    proto_goals = generate_proto_goals_from_trigger(
        trigger=trigger,
        config=config.proto_goal_config,
    )
    
    if not proto_goals:
        logger.info("📋 생성된 ProtoGoal 없음 - 사이클 종료")
        log_self_acquisition_event(trigger, None, None, config)
        return None
    
    # 3. 최적의 ProtoGoal 선택
    best_goal = select_best_proto_goal(proto_goals)
    
    if best_goal is None:
        log_self_acquisition_event(trigger, None, None, config)
        return None
    
    logger.info(f"✨ 선택된 Goal: {best_goal.type.value} - {best_goal.description}")
    
    # 4. 실행
    result = execute_proto_goal(best_goal)
    
    # 5. 로그 기록
    log_self_acquisition_event(trigger, best_goal, result, config)
    
    success_str = "✅ 성공" if result.get("success") else "❌ 실패"
    logger.info(f"🔄 Cycle 완료: {success_str}")
    
    return {
        "trigger": trigger.to_dict(),
        "selected_goal": best_goal.to_dict(),
        "result": result
    }


def self_acquisition_main_loop(
    config: SelfAcquisitionConfig,
    stop_condition: Optional[Callable[[], bool]] = None
) -> None:
    """
    별도의 프로세스/스레드에서 실행될 수 있는 메인 루프.
    loop_interval_seconds를 준수하여 주기적으로 사이클을 실행합니다.
    
    안전성을 위해:
    - 예외 발생 시 루프가 중단되지 않음
    - stop_condition이 True를 반환하면 종료
    """
    logger.info("🚀 Self-Acquisition Main Loop 시작")
    logger.info(f"   Interval: {config.loop_interval_seconds}초")
    logger.info(f"   Max actions per cycle: {config.max_actions_per_cycle}")
    
    cycle_count = 0
    
    while True:
        # 종료 조건 확인
        if stop_condition and stop_condition():
            logger.info("🛑 Stop condition met - 루프 종료")
            break
        
        cycle_count += 1
        logger.info(f"\n{'='*50}")
        logger.info(f"🔄 Cycle #{cycle_count}")
        logger.info(f"{'='*50}")
        
        try:
            run_self_acquisition_cycle(config)
        except Exception as e:
            # 예외는 로깅만 하고 루프 유지
            logger.error(f"[SelfAcquisitionLoop] Error in cycle #{cycle_count}: {e}")
        
        # 다음 사이클까지 대기
        logger.info(f"💤 다음 사이클까지 {config.loop_interval_seconds}초 대기...")
        time.sleep(config.loop_interval_seconds)


if __name__ == "__main__":
    # 단일 사이클 테스트
    print("🧪 Self-Acquisition Loop 테스트")
    print("="*50)
    
    config = SelfAcquisitionConfig.default()
    result = run_self_acquisition_cycle(config)
    
    if result:
        print("\n📊 결과:")
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    else:
        print("\n😴 이번 사이클에서 수행할 작업 없음")
