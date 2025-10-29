import time

from fastapi.testclient import TestClient


def test_session_message_summary_flow(client: TestClient):
    sid = "session-unit-123"

    # Add messages
    msgs = [
        "첫 메시지입니다",
        "두 번째 메시지에 상세 내용이 조금 더 깁니다.",
        "세 번째 메시지로 결론을 정리합니다",
    ]
    for m in msgs:
        r = client.post(f"/sessions/{sid}/messages", json={"message": m})
        assert r.status_code == 200
        assert r.json().get("session_id") == sid

    # Request end chat (enqueue background summary)
    r = client.post(f"/chat/end?session_id={sid}")
    assert r.status_code == 200
    assert r.json().get("status") == "ended"

    # Poll for summary result
    summary_url = f"/summaries/{sid}"
    for _ in range(20):  # up to ~2s
        res = client.get(summary_url)
        assert res.status_code == 200
        data = res.json()
        if data.get("status") == "completed":
            assert isinstance(data.get("summary"), str)
            assert data.get("generated_at")
            break
        time.sleep(0.1)
    else:
        raise AssertionError("Summary did not complete in time")
