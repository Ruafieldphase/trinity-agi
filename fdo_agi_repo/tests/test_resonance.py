import sys
import pathlib
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[2]
FDO = ROOT / "fdo_agi_repo"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(FDO))

from fdo_agi_repo.universal.task_schema import (
    create_simple_task,
    AbstractIntent,
)
from fdo_agi_repo.universal.resonance import (
    derive_resonance_key,
    ResonanceEvent,
    ResonanceStore,
)


def test_derive_resonance_key_basic():
    task = create_simple_task(
        intent=AbstractIntent.ANALYZE,
        description="demo",
        input_text="text",
        domain_id="software_engineering",
    )
    key = derive_resonance_key(task)
    assert key.startswith("software_engineering:analyze")


def test_resonance_store_roundtrip(tmp_path):
    store = ResonanceStore(tmp_path / "res.jsonl")
    ev = ResonanceEvent(task_id="t1", resonance_key="software_engineering:analyze")
    store.append(ev)
    latest = store.latest()
    assert latest is not None
    assert latest.task_id == "t1"
    assert latest.resonance_key == "software_engineering:analyze"
