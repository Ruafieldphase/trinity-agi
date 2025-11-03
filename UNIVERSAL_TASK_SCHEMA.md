# Universal Task Schema - Design v1.0

**Date:** 2025-11-03
**Author:** Shion (시안)
**Status:** Proposed

## 1. 개요 (Overview)

이 문서는 도메인에 독립적인(Domain-Agnostic) 작업 표현을 위한 범용 작업 스키마(Universal Task Schema)를 정의합니다. 이 스키마는 AGI 시스템의 Meta-Controller가 모든 종류의 작업을 이해하고, 분해하며, 적절한 실행기(Executor)에 전달할 수 있는 표준화된 구조를 제공하는 것을 목표로 합니다.

## 2. 설계 원칙 (Design Principles)

- **범용성 (Universality):** 파일 시스템 조작, 웹 브라우징, 코드 실행, RPA 등 모든 종류의 작업을 표현할 수 있어야 합니다.
- **분해성 (Decomposability):** 복잡한 작업을 더 작은 하위 작업(sub-task)들로 쉽게 분해할 수 있어야 합니다.
- **확장성 (Extensibility):** 새로운 도메인과 작업 유형을 쉽게 추가할 수 있는 플러그인 아키텍처를 지원해야 합니다.
- **명확성 (Clarity):** 각 필드는 명확한 목적을 가지며, 기계와 사람 모두가 쉽게 이해할 수 있어야 합니다.

## 3. 스키마 정의 (Schema Definition)

작업은 JSON 객체로 표현됩니다. 다음은 제안하는 기본 스키마 구조입니다.

```json
{
  "schema_version": "1.0",
  "task_id": "uuid-string-placeholder",
  "goal": "A high-level, human-readable description of the task.",
  "domain": "file_system | web | code | rpa | communication | planning",
  "action": "specific_action_within_domain",
  "parameters": {
    "key1": "value1",
    "key2": "value2"
  },
  "dependencies": [
    "uuid-of-task-1",
    "uuid-of-task-2"
  ],
  "status": "pending | scheduled | in_progress | completed | failed | waiting_for_dependency",
  "result": {
    "success": true,
    "output_path": "/path/to/output/file.txt",
    "summary": "A brief summary of the task outcome.",
    "error_message": null
  },
  "metadata": {
    "created_at": "timestamp",
    "started_at": "timestamp",
    "completed_at": "timestamp",
    "requested_by": "user_id or system_component",
    "priority": "normal | high | low"
  }
}
```

## 4. 필드 상세 설명 (Field Descriptions)

- **`schema_version` (String):**
  - 스키마의 버전. 향후 스키마 변경에 따른 호환성 관리를 위해 사용됩니다.

- **`task_id` (String - UUID):**
  - 각 작업을 고유하게 식별하는 ID. UUIDv4 사용을 권장합니다.

- **`goal` (String):**
  - 사용자가 요청한 작업의 최종 목표를 자연어로 설명합니다. Meta-Controller가 작업의 전체적인 맥락을 이해하는 데 사용됩니다.

- **`domain` (String - Enum):**
  - 작업이 속한 큰 영역을 지정합니다. Meta-Controller는 이 값을 보고 어떤 종류의 실행기(Executor)를 사용해야 할지 결정합니다.
  - **초기 제안 도메인:**
    - `file_system`: 파일 읽기, 쓰기, 복사, 삭제 등
    - `web`: URL 접속, 스크래핑, API 호출 등
    - `code`: 스크립트 실행, 컴파일, 테스트 등
    - `rpa`: GUI 자동화, 브라우저 조작 등
    - `communication`: 이메일 전송, 슬랙 메시지 등
    - `planning`: 복잡한 목표를 하위 작업으로 분해하는 작업 자체.

- **`action` (String):**
  - `domain` 내에서 수행할 구체적인 행동을 정의합니다. (예: `domain: 'file_system'` 이면 `action: 'read_file'`)

- **`parameters` (Object):**
  - `action`을 수행하는 데 필요한 파라미터들을 Key-Value 형태로 전달합니다. (예: `read_file` 액션의 경우 `{"path": "/path/to/file"}`)

- **`dependencies` (Array of Strings):**
  - 이 작업이 시작되기 전에 반드시 완료되어야 하는 다른 작업들의 `task_id` 목록. 작업 실행 순서를 관리하는 핵심 필드입니다.

- **`status` (String - Enum):**
  - 작업의 현재 상태를 나타냅니다.

- **`result` (Object):**
  - 작업 완료 후 결과를 저장하는 객체입니다.
    - `success` (Boolean): 작업 성공 여부.
    - `output_path` (String): 결과물이 파일로 생성된 경우 그 경로.
    - `summary` (String): 작업 결과에 대한 간략한 요약.
    - `error_message` (String): 실패 시 에러 메시지.

- **`metadata` (Object):**
  - 작업 자체의 데이터는 아니지만, 추적 및 관리를 위한 추가 정보들을 담습니다.

## 5. 다음 단계 (Next Steps)

1.  **스키마 확정:** 이 제안에 대한 피드백을 받고 스키마를 확정합니다.
2.  **Meta-Controller 설계:** 이 스키마를 입력받아 작업을 처리하는 Meta-Controller의 기본 구조를 설계합니다.
3.  **Executor 프로토타입 구현:** `file_system` 도메인에 대한 간단한 실행기(Executor)를 프로토타입으로 구현합니다.
