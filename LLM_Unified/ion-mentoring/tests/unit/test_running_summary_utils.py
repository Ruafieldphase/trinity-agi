"""running_summary 유틸 테스트"""

from persona_system.utils.summary_utils import update_running_summary


def test_update_running_summary_basic_append_and_dedup():
    rs = "- U: Hello\n- A: Hi there"
    new_msgs = [
        {"role": "user", "content": "Hello"},  # duplicate
        {"role": "assistant", "content": "How can I help you today?"},
    ]
    out = update_running_summary(rs, new_msgs, max_bullets=10, max_chars=1000)
    lines = out.splitlines()
    # Should contain deduped entries, keeping the recent assistant line
    assert any("A: How can I help you today?" in ln for ln in lines)
    # Duplicate "U: Hello" should not create two entries
    assert sum(1 for ln in lines if "U: Hello" in ln) == 1


def test_update_running_summary_limits():
    rs = None
    # Create more than max_bullets messages
    new_msgs = [{"role": "user", "content": f"msg {i}"} for i in range(12)]
    out = update_running_summary(rs, new_msgs, max_bullets=8, max_chars=1000)
    lines = [ln for ln in out.splitlines() if ln.strip()]
    assert len(lines) <= 8

    # Now enforce char limit
    long_msgs = [{"role": "assistant", "content": "x" * 500} for _ in range(10)]
    out2 = update_running_summary(out, long_msgs, max_bullets=20, max_chars=300)
    assert len(out2) <= 300
