"""
summary_light 모드 캐시 키 동작 테스트

요구사항:
- summary_light 모드에서는 최근 메시지 해시가 캐시 키에 반영되어야 한다
- 동일한 최근 N 메시지면 같은 키, 마지막 메시지가 바뀌면 다른 키가 되어야 한다
"""

from persona_system.models import ChatContext
from persona_system.pipeline_optimized import get_optimized_pipeline, reset_optimized_pipeline


def test_summary_light_cache_key_changes_with_history():
    reset_optimized_pipeline()
    pipe = get_optimized_pipeline()

    ctx1 = ChatContext(
        user_id="user-1",
        session_id="s-1",
        message_history=[
            {"role": "user", "content": "안녕"},
            {"role": "assistant", "content": "무엇을 도와드릴까요"},
            {"role": "user", "content": "대화를 요약해줘"},
        ],
    )

    # 동일한 히스토리로 두 번 호출 → 같은 키
    r1 = pipe.process(
        user_input="요약 부탁해",
        resonance_key="calm-medium-learning",
        context=ctx1,
        use_cache=True,
        prompt_mode="summary_light",
    )
    r2 = pipe.process(
        user_input="요약 부탁해",
        resonance_key="calm-medium-learning",
        context=ctx1,
        use_cache=True,
        prompt_mode="summary_light",
    )

    k1 = r1.metadata.get("cache_key")
    k2 = r2.metadata.get("cache_key")
    assert k1 == k2 and k1 is not None

    # 마지막 메시지만 변경 → 다른 키
    ctx2 = ChatContext(
        user_id="user-1",
        session_id="s-1",
        message_history=[
            {"role": "user", "content": "안녕"},
            {"role": "assistant", "content": "무엇을 도와드릴까요"},
            {"role": "user", "content": "대화를 아주 간략히 요약"},
        ],
    )

    r3 = pipe.process(
        user_input="요약 부탁해",
        resonance_key="calm-medium-learning",
        context=ctx2,
        use_cache=True,
        prompt_mode="summary_light",
    )
    k3 = r3.metadata.get("cache_key")
    assert k3 is not None and k3 != k1
