"""
Metadata analyzer unit test.

샘플 JSONL 파일을 분석하여 집계 결과가 예상과 일치하는지 확인합니다.
"""

from pathlib import Path

import pytest

from scripts.analyze_chat_metadata import load_records, summarize


def test_metadata_analyzer_sample_file():
    """샘플 로그 분석 결과를 검증합니다."""
    sample_path = Path(__file__).parent.parent / "samples" / "chat_responses_sample.jsonl"
    assert sample_path.exists(), "샘플 JSONL 파일이 존재해야 합니다."

    with sample_path.open("r", encoding="utf-8") as handle:
        summary = summarize(load_records(handle))

    assert summary["total_records"] == 3
    assert summary["persona_distribution"]["Lua"] == 1
    assert summary["persona_distribution"]["Elro"] == 1
    assert summary["persona_distribution"]["Nana"] == 1

    assert summary["phase_distribution"]["Attune"] == 1
    assert summary["phase_distribution"]["Structure"] == 1
    assert summary["phase_distribution"]["Elevate"] == 1

    assert summary["rune_regenerate_count"] == 1
    assert summary["rune_quality_average"] == pytest.approx(0.7333333, rel=1e-6)
