# Meta-Controller Architecture - Design v1.0

**Date:** 2025-11-03
**Author:** Shion (시안)
**Related Document:** `UNIVERSAL_TASK_SCHEMA.md`

## 1. 개요 (Overview)

메타 컨트롤러(Meta-Controller)는 AGI 시스템의 중앙 지휘 센터입니다. 높은 수준의 목표(goal)를 입력받아 이를 `Universal Task Schema`에 맞는 구체적인 작업들로 분해하고, 작업 간의 의존성을 관리하며, 적절한 실행기(Executor)에 분배하여 최종 목표를 달성하는 역할을 수행합니다.

## 2. 핵심 책임 (Core Responsibilities)

1.  **목표 분해 (Goal Decomposition):** 자연어로 표현된 복잡한 목표를 실행 가능한 하위 작업(sub-task)의 그래프로 변환합니다. (초기 버전에서는 이 기능이 제한적일 수 있음)
2.  **작업 스케줄링 (Task Scheduling):** 작업 의존성(`dependencies`)을 기반으로 실행 가능한 작업들을 큐에 넣고 관리합니다.
3.  **작업 라우팅 (Task Routing):** 각 작업의 `domain` 필드를 확인하여, 해당 도메인을 처리할 수 있는 적절한 실행기(Executor)에게 작업을 전달합니다.
4.  **상태 관리 (State Management):** 모든 작업의 상태(`status`)를 추적하고 전체 진행 상황을 모니터링합니다.
5.  **결과 종합 (Result Synthesis):** 완료된 작업들의 `result`를 수집하고, 모든 작업이 완료되면 최종 결과를 종합하여 보고합니다.

## 3. 아키텍처 (Architecture)

메타 컨트롤러는 다음 4가지 핵심 컴포넌트로 구성됩니다.

![Meta-Controller Architecture Diagram](https://i.imgur.com/example.png "A conceptual diagram showing Goal -> Meta-Controller -> Task Decomposer -> Task Scheduler -> Executor Registry -> Executors")
*(Note: The diagram is a conceptual placeholder)*

### 3.1. Task Registry (작업 등록소)
- **역할:** 시스템 내의 모든 작업을 저장하고 관리하는 데이터베이스입니다.
- **기능:**
    - 새로운 작업 추가, 기존 작업의 상태 및 결과 업데이트.
    - 작업 ID로 특정 작업 조회.
    - 실행 가능한 작업(모든 의존성 완료) 목록 조회.
- **구현:** 초기에는 인메모리(In-memory) 딕셔너리로 구현하며, 향후 SQLite나 파일 기반 DB로 확장할 수 있습니다.

### 3.2. Executor Registry (실행기 등록소)
- **역할:** 도메인과 실제 실행기 클래스를 매핑하는 등록소입니다.
- **기능:**
    - 시스템 시작 시, 사용 가능한 실행기들을 `domain` 키와 함께 등록합니다. (예: `{"file_system": FileSystemExecutor()}`)
    - 주어진 `domain`에 해당하는 실행기 인스턴스를 반환합니다.
- **구현:** 간단한 딕셔너리 형태로 구현합니다.

### 3.3. Task Scheduler & Execution Loop (작업 스케줄러 및 실행 루프)
- **역할:** 메타 컨트롤러의 심장(heartbeat) 역할을 하는 메인 루프입니다.
- **기능:**
    1.  주기적으로 Task Registry에서 실행 가능한 작업(`status: 'pending'`이고 `dependencies`가 충족된 작업)을 조회합니다.
    2.  실행 가능한 작업을 큐에 넣고 `status`를 `scheduled`로 변경합니다.
    3.  큐에서 작업을 꺼내 `domain`을 확인하고, Executor Registry를 통해 적절한 실행기를 찾습니다.
    4.  해당 실행기의 `execute(task)` 메소드를 비동기적으로 호출하고, 작업 `status`를 `in_progress`로 변경합니다.
    5.  실행 완료 후 `result`를 받아 Task Registry에 업데이트하고, `status`를 `completed` 또는 `failed`로 변경합니다.
    6.  모든 작업이 완료될 때까지 1-5단계를 반복합니다.

### 3.4. Goal Decomposer (목표 분해기)
- **역할:** 가장 지능적인 부분으로, 자연어 목표를 작업 그래프로 변환합니다.
- **기능:**
    - LLM(Lumen Gateway)을 활용하여 사용자의 `goal`을 분석합니다.
    - 목표 달성에 필요한 단계들을 `Universal Task Schema` 형식의 작업 목록으로 생성합니다.
    - 작업 간의 `dependencies`를 자동으로 설정합니다.
- **구현:** 초기에는 수동으로 정의된 작업 목록을 반환하는 형태로 시작하고, 점차 LLM 연동을 통해 자동화 수준을 높입니다.

## 4. 인터페이스 정의 (Interface Definitions)

### 4.1. MetaController (Class)
```python
class MetaController:
    def __init__(self):
        # ... registries initialization ...

    def register_executor(self, domain: str, executor: Executor):
        # 실행기 등록

    def submit_goal(self, goal: str) -> str:
        # 새로운 목표 제출, 전체 프로세스 시작
        # goal_id 반환

    async def run(self):
        # 메인 실행 루프 시작

    def get_goal_status(self, goal_id: str) -> Dict:
        # 특정 목표의 진행 상태 및 결과 조회
```

### 4.2. Executor (Abstract Base Class)
모든 실행기는 이 추상 클래스를 상속받아 구현해야 합니다.

```python
from abc import ABC, abstractmethod

class Executor(ABC):
    @abstractmethod
    def get_domain(self) -> str:
        # 자신의 도메인 이름을 반환

    @abstractmethod
    async def execute(self, task: Dict) -> Dict:
        # 작업을 실행하고 result 객체를 반환
```

## 5. 작업 흐름 (Workflow)

1.  **시작:** `MetaController` 인스턴스가 생성되고, 다양한 `Executor`들이 등록됩니다.
2.  **목표 제출:** `metacontroller.submit_goal("C 드라이브의 모든 .log 파일을 찾아서 /backup 폴더에 복사해줘")`가 호출됩니다.
3.  **분해:** `GoalDecomposer`가 목표를 분석하여 2개의 작업(task1: find_files, task2: copy_files)을 생성합니다. `task2`는 `task1`에 대한 의존성을 가집니다.
4.  **실행:**
    - `TaskScheduler`가 `task1`을 실행 가능한 것으로 판단하고 `FileSystemExecutor`에게 전달합니다.
    - `task1`이 성공적으로 완료되면, `TaskScheduler`는 `task2`의 의존성이 충족되었음을 확인하고 `FileSystemExecutor`에게 다시 전달합니다.
5.  **완료:** `task2`까지 완료되면, `MetaController`는 전체 목표가 성공적으로 완료되었음을 보고합니다.

## 6. 다음 단계 (Next Steps)

1.  **프로토타입 코드 작성:** 이 설계에 기반하여 `MetaController`와 `Executor`의 기본 클래스 구조를 포함하는 Python 파일(`meta_controller.py`)을 작성합니다.
2.  **`FileSystemExecutor` 구현:** 첫 번째 실행기로, `read_file`, `write_file`, `list_directory` 등의 `action`을 처리하는 `FileSystemExecutor`를 구현합니다.
3.  **단위 테스트:** `MetaController`가 단일 작업을 스케줄링하고 실행하는 간단한 시나리오에 대한 단위 테스트를 작성합니다.
