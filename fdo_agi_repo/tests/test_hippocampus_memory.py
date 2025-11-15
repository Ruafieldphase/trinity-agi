import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from fdo_agi_repo.copilot.hippocampus import CopilotHippocampus


def make_item(content: str, hours_ago: float = 0.0, emotional: float = 0.5, access_count: int = 1):
    ts = (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()
    return {
        "content": content,
        "timestamp": ts,
        "emotional_intensity": emotional,
        "access_count": access_count,
    }


def test_importance_recency_decay(tmp_path: Path):
    hp = CopilotHippocampus(tmp_path)
    now_item = make_item("test A", hours_ago=0)
    mid_item = make_item("test A", hours_ago=12)
    old_item = make_item("test A", hours_ago=72)

    imp_now = hp._calculate_importance(now_item)
    imp_mid = hp._calculate_importance(mid_item)
    imp_old = hp._calculate_importance(old_item)

    assert imp_now > imp_mid > imp_old


def test_consolidate_dedup(tmp_path: Path):
    hp = CopilotHippocampus(tmp_path)
    # 비슷한 두 항목 + 다른 한 항목
    a = make_item("Implement recall sampler for memory", hours_ago=1)
    b = make_item("Implement recall sampling for memory", hours_ago=1.2)
    c = make_item("Document API contract for handover", hours_ago=0.5)

    hp.add_to_working_memory(a)
    hp.add_to_working_memory(b)
    hp.add_to_working_memory(c)

    # 임계값을 다소 느슨하게 하여 a~b를 중복으로 간주하도록 함
    hp.consolidation_config["importance_threshold"] = 0.0  # 강제로 모두 저장 가능 상태
    # 두 문장의 자카드 유사도는 대략 0.66 수준이므로 임계값을 조금 낮춰 중복으로 간주
    hp.consolidation_config["dedup_threshold"] = 0.66

    # 내부 dedup 함수가 기대대로 동작하는지 사전 검증
    deduped = hp._deduplicate_items(
        [a, b, c], threshold=hp.consolidation_config["dedup_threshold"]
    )
    assert len(deduped) == 2

    result = hp.consolidate(force=False)
    # a,b 중 하나는 제거되어 총 2개만 저장되어야 함
    assert result["total"] == 2
    assert result["episodic"] + result["semantic"] + result["procedural"] == 2


def test_handover_version_and_load(tmp_path: Path):
    hp = CopilotHippocampus(tmp_path)
    # 일부 작업/펜딩 추가 후 핸드오버 생성
    hp.add_to_working_memory(make_item("Working X"))
    hp.short_term.add_pending_task({"id": "t1", "description": "Do Y"})
    h = hp.generate_handover()
    assert h.get("handover_version") == 1

    # v0 유사 파일로 덮어쓰기 (마이그레이션 테스트)
    handover_path = tmp_path / "outputs" / "copilot_handover_latest.json"
    v0 = {
        "session_id": h["session_id"],
        "current_context": {"working_items": [], "pending_tasks": []},
    }
    handover_path.write_text(json.dumps(v0, ensure_ascii=False, indent=2), encoding="utf-8")

    loaded = hp.load_handover()
    assert loaded is not None
    assert loaded.get("handover_version") == 1
    assert "timestamp" in loaded
    assert "current_context" in loaded


def test_recall_balanced_sampling(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    hp = CopilotHippocampus(tmp_path)

    def mk(type_: str, importance: float):
        return {"type": type_, "data": {"txt": type_}, "importance": importance}

    monkeypatch.setattr(hp.long_term, "recall_episodic", lambda q, top_k=5: [mk("episodic", 0.9 - i*0.01) for i in range(10)])
    monkeypatch.setattr(hp.long_term, "recall_semantic", lambda q, top_k=5: [mk("semantic", 0.85 - i*0.01) for i in range(10)])
    monkeypatch.setattr(hp.long_term, "recall_procedural", lambda q, top_k=5: [mk("procedural", 0.8 - i*0.01) for i in range(10)])

    out = hp.recall("any query", top_k=9)
    # 균등 분배(3종 * 3개) 후 전체 정렬되며, 최소 각 타입 2개 이상 포함 보장
    types = [x["type"] for x in out]
    assert len(out) == 9
    assert types.count("episodic") >= 2
    assert types.count("semantic") >= 2
    assert types.count("procedural") >= 2
