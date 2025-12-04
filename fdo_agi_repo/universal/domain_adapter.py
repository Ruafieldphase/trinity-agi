from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from .task_schema import UniversalTask, UniversalData, DataType
from .resonance import ResonanceStore, ResonanceEvent, derive_resonance_key


class DomainAdapter(ABC):
    """도메인 어댑터 기반 클래스"""

    def __init__(self, domain_id: str):
        self.domain_id = domain_id
        self.capabilities = self._register_capabilities()

    @abstractmethod
    def _register_capabilities(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def validate_task(self, task: UniversalTask) -> tuple[bool, List[str]]:
        pass

    @abstractmethod
    def transform_input(self, universal_data: UniversalData) -> Any:
        pass

    @abstractmethod
    def execute(self, task: UniversalTask) -> Dict[str, Any]:
        pass

    @abstractmethod
    def transform_output(self, domain_output: Any, expected_type: DataType):
        pass

    def can_handle(self, task: UniversalTask) -> bool:
        return task.domain.domain_id == self.domain_id


class SoftwareEngineeringAdapter(DomainAdapter):
    """소프트웨어 엔지니어링 어댑터 (예시)"""

    def __init__(self):
        super().__init__("software_engineering")

    def _register_capabilities(self) -> Dict[str, Any]:
        return {
            "supported_intents": ["analyze", "create", "transform", "validate"],
            "supported_languages": ["python", "javascript", "typescript", "java"],
        }

    def validate_task(self, task: UniversalTask) -> tuple[bool, List[str]]:
        errors: List[str] = []
        if task.intent.value not in self.capabilities["supported_intents"]:
            errors.append(f"Unsupported intent: {task.intent}")
        for inp in task.inputs:
            if inp.data_type not in (DataType.CODE, DataType.TEXT):
                errors.append(f"Unsupported data type: {inp.data_type}")
        return (len(errors) == 0, errors)

    def transform_input(self, universal_data: UniversalData) -> Any:
        return universal_data.content

    def execute(self, task: UniversalTask) -> Dict[str, Any]:
        valid, errors = self.validate_task(task)
        if not valid:
            return {"status": "error", "errors": errors}
        return {"status": "success", "results": [{"message": "analysis_complete"}]}

    def transform_output(self, domain_output: Any, expected_type: DataType):
        if expected_type == DataType.TEXT:
            return UniversalData(data_type=DataType.TEXT, content=str(domain_output))
        return UniversalData(data_type=DataType.STRUCTURED, content=domain_output)


class AdapterRegistry:
    def __init__(self):
        self.adapters: Dict[str, DomainAdapter] = {}
        self.register(SoftwareEngineeringAdapter())
        # 추가 예시 어댑터 등록: 헬스케어, 파이낸스
        self.register(HealthcareAdapter())
        self.register(FinanceAdapter())

    def register(self, adapter: DomainAdapter):
        self.adapters[adapter.domain_id] = adapter

    def get_adapter(self, domain_id: str) -> Optional[DomainAdapter]:
        return self.adapters.get(domain_id)

    def find_suitable_adapter(self, task: UniversalTask) -> Optional[DomainAdapter]:
        adapter = self.get_adapter(task.domain.domain_id)
        if adapter and adapter.can_handle(task):
            return adapter
        return None


class UniversalTaskExecutor:
    def __init__(self, resonance_store: Optional[ResonanceStore] = None):
        self.registry = AdapterRegistry()
        self.resonance_store = resonance_store

    def execute(self, task: UniversalTask) -> Dict[str, Any]:
        adapter = self.registry.find_suitable_adapter(task)
        if not adapter:
            return {"status": "error", "message": f"No adapter for {task.domain.domain_id}"}
        valid, errors = adapter.validate_task(task)
        if not valid:
            return {"status": "error", "validation_errors": errors}
        result = adapter.execute(task)
        if result.get("status") == "success":
            result["universal_outputs"] = [
                adapter.transform_output(result, t) for t in task.outputs_expected
            ]
            # Optional: record resonance event when store is provided
            if self.resonance_store is not None:
                try:
                    key = derive_resonance_key(task)
                    result["resonance_key"] = key
                    event = ResonanceEvent(
                        task_id=task.task_id,
                        resonance_key=key,
                        metrics={"success": 1.0},
                        tags={"domain": task.domain.domain_id},
                    )
                    self.resonance_store.append(event)
                except Exception:
                    # Logging system not wired here; ignore recording failures silently for now
                    pass
        return result


class HealthcareAdapter(DomainAdapter):
    """헬스케어 어댑터 (예시)"""

    def __init__(self):
        super().__init__("healthcare")

    def _register_capabilities(self) -> Dict[str, Any]:
        return {
            "supported_intents": [
                "analyze",
                "explain",
                "validate",
                "transform",
            ],
            "supported_modalities": ["text", "structured"],
        }

    def validate_task(self, task: UniversalTask) -> tuple[bool, List[str]]:
        errors: List[str] = []
        if task.intent.value not in self.capabilities["supported_intents"]:
            errors.append(f"Unsupported intent: {task.intent}")
        for inp in task.inputs:
            if inp.data_type not in (DataType.TEXT, DataType.STRUCTURED):
                errors.append(f"Unsupported data type: {inp.data_type}")
        return (len(errors) == 0, errors)

    def transform_input(self, universal_data: UniversalData) -> Any:
        return universal_data.content

    def execute(self, task: UniversalTask) -> Dict[str, Any]:
        valid, errors = self.validate_task(task)
        if not valid:
            return {"status": "error", "errors": errors}
        # 데모: 입력 요약/설명 형태로 응답
        summary = {
            "domain": "healthcare",
            "intent": task.intent.value,
            "inputs": [inp.content for inp in task.inputs],
        }
        return {"status": "success", "results": [summary]}

    def transform_output(self, domain_output: Any, expected_type: DataType):
        if expected_type == DataType.TEXT:
            return UniversalData(data_type=DataType.TEXT, content=str(domain_output))
        return UniversalData(data_type=DataType.STRUCTURED, content=domain_output)


class FinanceAdapter(DomainAdapter):
    """파이낸스 어댑터 (예시)"""

    def __init__(self):
        super().__init__("finance")

    def _register_capabilities(self) -> Dict[str, Any]:
        return {
            "supported_intents": ["analyze", "predict", "validate"],
            "supported_modalities": ["text", "tabular"],
        }

    def validate_task(self, task: UniversalTask) -> tuple[bool, List[str]]:
        errors: List[str] = []
        if task.intent.value not in self.capabilities["supported_intents"]:
            errors.append(f"Unsupported intent: {task.intent}")
        for inp in task.inputs:
            if inp.data_type not in (DataType.TEXT, DataType.TABULAR):
                errors.append(f"Unsupported data type: {inp.data_type}")
        return (len(errors) == 0, errors)

    def transform_input(self, universal_data: UniversalData) -> Any:
        return universal_data.content

    def execute(self, task: UniversalTask) -> Dict[str, Any]:
        valid, errors = self.validate_task(task)
        if not valid:
            return {"status": "error", "errors": errors}
        # 데모: 간단한 결과 형태
        result = {
            "domain": "finance",
            "intent": task.intent.value,
            "count_inputs": len(task.inputs),
        }
        return {"status": "success", "results": [result]}

    def transform_output(self, domain_output: Any, expected_type: DataType):
        if expected_type == DataType.TEXT:
            return UniversalData(data_type=DataType.TEXT, content=str(domain_output))
        return UniversalData(data_type=DataType.STRUCTURED, content=domain_output)
