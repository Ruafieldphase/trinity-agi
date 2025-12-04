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
from fdo_agi_repo.universal.domain_adapter import UniversalTaskExecutor
from fdo_agi_repo.universal.resonance import ResonanceStore, derive_resonance_key


def test_executor_records_resonance_event(tmp_path):
    # Arrange
    task = create_simple_task(
        intent=AbstractIntent.ANALYZE,
        description="integration",
        input_text="# code",
        domain_id="software_engineering",
    )
    store_path = tmp_path / "events.jsonl"
    store = ResonanceStore(store_path)
    executor = UniversalTaskExecutor(resonance_store=store)

    # Act
    result = executor.execute(task)

    # Assert
    assert result.get("status") == "success"
    latest = store.latest()
    assert latest is not None
    assert latest.task_id == task.task_id
    assert latest.resonance_key == derive_resonance_key(task)
