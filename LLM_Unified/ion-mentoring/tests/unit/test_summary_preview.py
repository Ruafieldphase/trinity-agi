import os

from fastapi.testclient import TestClient

# Ensure parallel is enabled for test
os.environ["SUMMARY_PARALLEL_ENABLED"] = "true"


def test_summaries_preview_basic(client: TestClient):
    payload = {
        "messages": [
            "첫 메시지입니다",
            "두 번째 메시지에 상세 내용이 조금 더 깁니다.",
            "세 번째 메시지로 결론을 정리합니다",
        ]
    }
    resp = client.post("/summaries/preview", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data.get("status") == "completed"
    assert "summary" in data and isinstance(data["summary"], str)
    assert data.get("parallel") in (True, False)
    assert isinstance(data.get("duration_ms"), int)
