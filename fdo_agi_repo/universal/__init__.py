# Universal AGI package

from .task_schema import (
	AbstractIntent,
	DataType,
	UniversalData,
	UniversalConstraint,
	UniversalCriteria,
	DomainMetadata,
	TaskRelation,
	UniversalTask,
	create_simple_task,
)
from .domain_adapter import (
	DomainAdapter,
	SoftwareEngineeringAdapter,
	AdapterRegistry,
	UniversalTaskExecutor,
)
from .resonance import (
	ResonanceEvent,
	derive_resonance_key,
	ResonanceStore,
)

__all__ = [
	"AbstractIntent",
	"DataType",
	"UniversalData",
	"UniversalConstraint",
	"UniversalCriteria",
	"DomainMetadata",
	"TaskRelation",
	"UniversalTask",
	"create_simple_task",
	"DomainAdapter",
	"SoftwareEngineeringAdapter",
	"AdapterRegistry",
	"UniversalTaskExecutor",
	"ResonanceEvent",
	"derive_resonance_key",
	"ResonanceStore",
]
