"""
API v2 멀티 페르소나 엔드포인트 테스트

대상:
- POST /api/v2/chat/multi-persona
"""

from fastapi.testclient import TestClient


def test_multi_persona_happy_path(client: TestClient):
    # given
    payload = {
        "user_input": "두 관점에서 장단점을 비교해 요약해줘",
    }

    # when
    resp = client.post("/api/v2/chat/multi-persona", json=payload)

    # then
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert data.get("success") is True
    assert isinstance(data.get("content"), str)
    assert isinstance(data.get("persona_used"), str)
    # 공통 응답 스키마 필드 일부 확인
    assert data.get("resonance_key") is not None
    assert data.get("request_id") is not None


def test_multi_persona_validation_empty_input(client: TestClient):
    # given
    payload = {
        "user_input": "",
    }

    # when
    resp = client.post("/api/v2/chat/multi-persona", json=payload)

    # then
    assert resp.status_code == 400
    data = resp.json()
    assert data.get("success") is False
    assert data.get("error", {}).get("code") == "INVALID_INPUT"


def test_multi_persona_force_multi_flag(client: TestClient):
    # given
    payload = {
        "user_input": "두 모델의 답변을 비교해서 최종 결론을 내려줘",
        "force_multi": True,
    }

    # when
    resp = client.post("/api/v2/chat/multi-persona", json=payload)

    # then
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("success") is True
    # 멀티 페르소나 블렌딩 결과로 persona_used가 채워지는지 확인
    assert isinstance(data.get("persona_used"), str) and len(data["persona_used"]) > 0
