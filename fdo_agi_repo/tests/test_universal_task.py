import sys
import pathlib
from datetime import datetime, timezone

# Ensure repository root and fdo_agi_repo are importable
ROOT = pathlib.Path(__file__).resolve().parents[2]
FDO = ROOT / "fdo_agi_repo"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(FDO))

from fdo_agi_repo.universal.task_schema import (
    UniversalTask,
    AbstractIntent,
    DataType,
    UniversalData,
    DomainMetadata,
    create_simple_task,
)
from fdo_agi_repo.universal.domain_adapter import UniversalTaskExecutor


def test_universal_task_serialization_roundtrip():
    task = UniversalTask(
        task_id="task_test",
        created_at=datetime.now(timezone.utc),
        intent=AbstractIntent.ANALYZE,
        intent_description="analyze sample text",
        inputs=[UniversalData(data_type=DataType.TEXT, content="hello")],
        outputs_expected=[DataType.TEXT],
        domain=DomainMetadata(domain_id="general"),
    )
    d = task.model_dump()
    assert d["intent"] == AbstractIntent.ANALYZE
    assert d["inputs"][0]["data_type"] == DataType.TEXT
    assert d["domain"]["domain_id"] == "general"


def test_executor_with_software_adapter_success():
    task = create_simple_task(
        intent=AbstractIntent.ANALYZE,
        description="simple analysis",
        input_text="print('hi')",
        domain_id="software_engineering",
    )
    execu = UniversalTaskExecutor()
    result = execu.execute(task)
    assert result.get("status") == "success"
    ups = result.get("universal_outputs")
    assert isinstance(ups, list) and len(ups) == 1
    assert ups[0].data_type == DataType.TEXT


def test_executor_no_adapter_error():
    task = create_simple_task(
        intent=AbstractIntent.ANALYZE,
        description="no adapter domain",
        input_text="data",
        domain_id="unknown_domain",
    )
    execu = UniversalTaskExecutor()
    result = execu.execute(task)
    assert result.get("status") == "error"
    assert "No adapter" in result.get("message", "")
