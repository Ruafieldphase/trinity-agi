"""Optimized pipeline의 running_summary 갱신 테스트"""

from persona_system.models import ChatContext
from persona_system.pipeline_optimized import get_optimized_pipeline


def test_pipeline_updates_running_summary_when_summary_light():
    pipeline = get_optimized_pipeline()

    ctx = ChatContext(
        user_id="u1",
        session_id="s1",
        message_history=[
            {"role": "user", "content": "첫 질문"},
            {"role": "assistant", "content": "첫 답변"},
        ],
        custom_context={},
    )

    # First call
    _ = pipeline.process(
        user_input="두 번째 질문",
        resonance_key="calm-medium-learning",
        context=ctx,
        prompt_mode="summary_light",
        prompt_options={"max_bullets": 6, "max_chars": 400},
        use_cache=False,
    )

    rs1 = ctx.custom_context.get("running_summary")
    assert isinstance(rs1, str) and len(rs1) > 0

    # Second call with another message
    ctx.add_message("assistant", "두 번째 답변")
    _ = pipeline.process(
        user_input="세 번째 질문",
        resonance_key="calm-medium-learning",
        context=ctx,
        prompt_mode="summary_light",
        prompt_options={"max_bullets": 6, "max_chars": 400},
        use_cache=False,
    )

    rs2 = ctx.custom_context.get("running_summary")
    assert isinstance(rs2, str) and len(rs2) >= len(rs1)
    # Should contain the latest assistant line in some form
    assert any("두 번째 답변" in ln for ln in rs2.splitlines())
