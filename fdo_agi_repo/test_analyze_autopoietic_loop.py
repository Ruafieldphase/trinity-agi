
import pytest
import time
from fdo_agi_repo.analysis.analyze_autopoietic_loop import summarize, load_events


def test_analyze_autopoietic_loop_runs(tmp_path):
    # 임시 ledger 파일 생성 (folding/unfolding/integration/symmetry 모두 포함)
    ledger_path = tmp_path / "resonance_ledger.jsonl"
    now = time.time()
    ledger_path.write_text(f'''
{{"event": "thesis_start", "task_id": "t1", "ts": {now} }}
{{"event": "thesis_end", "task_id": "t1", "ts": {now+5} }}
{{"event": "antithesis_start", "task_id": "t1", "ts": {now+6} }}
{{"event": "antithesis_end", "task_id": "t1", "ts": {now+15} }}
{{"event": "synthesis_start", "task_id": "t1", "ts": {now+16} }}
{{"event": "synthesis_end", "task_id": "t1", "ts": {now+30} }}
{{"event": "evidence_gate_triggered", "task_id": "t1", "ts": {now+30.002} }}
''', encoding="utf-8")
    # 이벤트 로드 및 분석
    events = load_events(ledger_path)
    summary = summarize(events, hours=24)
    # 최소한 complete_loops 1개 검출되는지 확인
    assert summary["counts"]["complete_loops"] == 1
    # phase duration이 정상적으로 계산되는지 확인
    assert summary["durations_avg_sec"]["integration"] > 0


def test_analyze_autopoietic_loop_second_pass(tmp_path):
    ledger_path = tmp_path / "resonance_ledger_second_pass.jsonl"
    now = time.time()
    ledger_path.write_text(f'''
{{"event": "thesis_start", "task_id": "t2", "ts": {now} }}
{{"event": "thesis_end", "task_id": "t2", "ts": {now+5} }}
{{"event": "antithesis_start", "task_id": "t2", "ts": {now+6} }}
{{"event": "antithesis_end", "task_id": "t2", "ts": {now+15} }}
{{"event": "synthesis_start", "task_id": "t2", "ts": {now+16} }}
{{"event": "synthesis_end", "task_id": "t2", "ts": {now+30} }}
{{"event": "second_pass", "task_id": "t2", "ts": {now+31} }}
{{"event": "evidence_gate_triggered", "task_id": "t2", "ts": {now+32} }}
{{"event": "task_complete", "task_id": "t2", "ts": {now+33}, "quality": 0.95, "evidence_ok": true }}
''', encoding="utf-8")
    events = load_events(ledger_path)
    summary = summarize(events, hours=24)
    assert summary["counts"]["complete_loops"] == 1
    assert summary["counts"]["second_pass"] == 1
    assert summary["counts"]["evidence_gate_triggered"] == 1
    assert summary["quality"]["final_quality_avg"] > 0.9
    assert summary["quality"]["final_evidence_ok_rate"] == 100.0

def test_analyze_autopoietic_loop_dual_synthesis(tmp_path):
    ledger_path = tmp_path / "resonance_ledger_dual_synth.jsonl"
    now = time.time()
    ledger_path.write_text(f'''
{{"event": "thesis_start", "task_id": "t3", "ts": {now} }}
{{"event": "thesis_end", "task_id": "t3", "ts": {now+5} }}
{{"event": "antithesis_start", "task_id": "t3", "ts": {now+6} }}
{{"event": "antithesis_end", "task_id": "t3", "ts": {now+15} }}
{{"event": "synthesis_start", "task_id": "t3", "ts": {now+16} }}
{{"event": "synthesis_end", "task_id": "t3", "ts": {now+30} }}
{{"event": "synthesis_start", "task_id": "t3", "ts": {now+31} }}
{{"event": "synthesis_end", "task_id": "t3", "ts": {now+45} }}
{{"event": "evidence_gate_triggered", "task_id": "t3", "ts": {now+46} }}
''', encoding="utf-8")
    events = load_events(ledger_path)
    summary = summarize(events, hours=24)
    assert summary["counts"]["complete_loops"] == 1
    # integration은 첫 번째 synthesis_start~synthesis_end, symmetry는 두 번째 synthesis_end~evidence_gate
    assert summary["durations_avg_sec"]["integration"] == pytest.approx(14.0, abs=0.1)
    assert summary["durations_avg_sec"]["symmetry"] == pytest.approx(1.0, abs=0.1)
