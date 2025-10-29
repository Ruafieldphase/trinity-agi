"""
API v2 summary_light 프롬프트 모드 테스트

대상:
- POST /api/v2/process with prompt_mode=summary_light
"""

from fastapi.testclient import TestClient


def test_process_summary_light_mode(client: TestClient):
    payload = {
        "user_input": "다음 대화를 간단히 요약해줘",
        "resonance_key": {"tone": "calm", "pace": "medium", "intent": "learning"},
        "use_cache": True,
        "prompt_mode": "summary_light",
    }

    resp = client.post("/api/v2/process", json=payload)
    assert resp.status_code == 200

    data = resp.json()
    # 공통 스키마 검증
    assert data.get("success") is True
    assert isinstance(data.get("content"), str)
    assert isinstance(data.get("persona_used"), str)
    assert data.get("resonance_key") == "calm-medium-learning"
    # 메타데이터에 prompt_mode가 포함되어야 함
    meta = data.get("metadata") or {}
    assert meta.get("prompt_mode") == "summary_light"
