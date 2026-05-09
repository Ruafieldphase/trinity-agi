# Trinity AGI Infrastructure Map / 트리니티 AGI 인프라 지도

`trinity-agi` is the infrastructure and body-side companion to Shion AI. Where `shion-ai` focuses on continuity, rhythm, and context regulation, Trinity holds the operational surfaces: local bridges, scheduling scripts, observatory components, approval boundaries, and public documentation.

`trinity-agi`는 Shion AI의 인프라 및 바디 측 저장소입니다. `shion-ai`가 연속성, 리듬, 맥락 조율에 집중한다면, Trinity는 로컬 브리지, 스케줄링 스크립트, 관측 컴포넌트, 승인 경계, 공개 문서를 담당합니다.

---

## 1. Field / 장

The field problem for Trinity is operational drift.

Trinity가 다루는 장의 문제는 운영 표류입니다.

Typical symptoms:

- a workflow works once but becomes hard to repeat
- agents call tools without preserving why or what comes next
- publishing, scheduling, and sync tasks drift away from the original intent
- automation becomes another layer the user has to manage
- local credentials, generated outputs, and public code boundaries become mixed

흔한 증상은 다음과 같습니다.

- 한 번은 되는 워크플로우가 반복하기 어려워짐
- 에이전트가 왜 하는지, 다음이 무엇인지 보존하지 못한 채 도구를 호출함
- 게시, 예약, 동기화 작업이 원래 의도에서 벗어남
- 자동화가 사용자가 관리해야 하는 또 다른 일이 됨
- 로컬 인증 정보, 생성 출력물, 공개 코드 경계가 섞임

---

## 2. Convergence / 수렴

Trinity converges that field into a body-side operating structure.

Trinity는 그 장을 바디 측 운영 구조로 수렴시킵니다.

It asks:

- Which action should be local and reproducible?
- Which memory or output should remain private?
- Which script is a tool, and which script is part of a loop?
- Does the next operation need human approval?
- Is the system preserving the user's rhythm, or just expanding automation?

Trinity는 다음을 묻습니다.

- 어떤 행동이 로컬에서 재현 가능해야 하는가?
- 어떤 기억이나 출력물이 비공개로 남아야 하는가?
- 어떤 스크립트가 단발 도구이고, 어떤 스크립트가 루프의 일부인가?
- 다음 작업에 인간 승인이 필요한가?
- 시스템이 사용자의 리듬을 보존하고 있는가, 아니면 자동화만 늘리고 있는가?

---

## 3. Public Structure / 공개 구조

The current public repository is intentionally smaller than the private working system. Older documents may mention directories such as `monolith/`, `void/`, or private output stores; those are not part of the current public tree.

현재 공개 저장소는 개인 작업 시스템보다 의도적으로 작습니다. 과거 문서에서 `monolith/`, `void/`, 개인 출력 저장소 같은 이름이 보일 수 있지만, 현재 공개 트리에는 포함하지 않습니다.

| Public area | Role |
| --- | --- |
| `agi_core/` | Core infrastructure experiments and resonance bridge utilities. |
| `Pulse_Live_Core/` | Live pulse, observatory, hippocampus, and field-engine components. |
| `lumen_factory/` | Media and interpretation utilities used by the body-side system. |
| `scripts/` | Operational scripts, including collaboration daemon and publishing helpers. |
| `config/` | Public-safe configuration templates and execution boundaries. |
| `docs/` | Guides, approval matrices, reports, research notes, and public artifacts. |
| `README.md` | Main bilingual entry point for readers. |
| `PHASE_TRANSITION_MAP.md` | Archival map of prior phase-transition nodes. |
| `VERIFICATION_PARTICLE.md` | Verification-oriented public particle. |

| 공개 영역 | 역할 |
| --- | --- |
| `agi_core/` | 핵심 인프라 실험과 공명 브리지 유틸리티 |
| `Pulse_Live_Core/` | 라이브 펄스, 관측소, 해마, 필드 엔진 컴포넌트 |
| `lumen_factory/` | 바디 측 시스템의 미디어 및 해석 유틸리티 |
| `scripts/` | 협업 데몬과 게시 보조 도구를 포함한 운영 스크립트 |
| `config/` | 공개 가능한 설정 템플릿과 실행 경계 |
| `docs/` | 가이드, 승인 매트릭스, 리포트, 연구 노트, 공개 산출물 |
| `README.md` | 독자를 위한 주요 이중언어 진입점 |
| `PHASE_TRANSITION_MAP.md` | 이전 위상전이 노드의 아카이브 지도 |
| `VERIFICATION_PARTICLE.md` | 검증 중심의 공개 입자 |

---

## 4. Operational Particles / 운영 입자

Trinity's concrete value appears in small operational particles rather than a single monolithic application.

Trinity의 가치는 하나의 거대한 애플리케이션보다 작은 운영 입자들에서 나타납니다.

Representative examples:

- `scripts/autonomous_collaboration_daemon.ps1`: Windows-side collaboration daemon surface.
- `scripts/youtube_bulk_scheduler.py`: publishing and scheduling helper that depends on local credentials.
- `agi_core/local_resonance_bridge.py`: local resonance bridge utilities.
- `agi_core/reverse_field_mapper.py`: field-to-internal-state mapping experiment.
- `Pulse_Live_Core/observatory_server.py`: observatory surface for live state.
- `Pulse_Live_Core/geometric_hippocampus.py`: memory geometry experiment.
- `docs/HUMAN_APPROVAL_MATRIX.yaml`: explicit boundary for operations requiring approval.

대표 예시는 다음과 같습니다.

- `scripts/autonomous_collaboration_daemon.ps1`: Windows 측 협업 데몬 표면
- `scripts/youtube_bulk_scheduler.py`: 로컬 인증 정보가 필요한 게시 및 예약 보조 도구
- `agi_core/local_resonance_bridge.py`: 로컬 공명 브리지 유틸리티
- `agi_core/reverse_field_mapper.py`: 필드에서 내부 상태로의 역매핑 실험
- `Pulse_Live_Core/observatory_server.py`: 라이브 상태 관측 표면
- `Pulse_Live_Core/geometric_hippocampus.py`: 기억 기하 실험
- `docs/HUMAN_APPROVAL_MATRIX.yaml`: 승인이 필요한 작업의 명시적 경계

---

## 5. Public/Private Boundary / 공개와 비공개 경계

The public repository should not contain:

- API keys or OAuth credentials
- generated logs
- private memory
- personal archive material
- local media outputs
- machine-specific runtime state

공개 저장소에는 다음이 포함되면 안 됩니다.

- API 키 또는 OAuth 인증 정보
- 생성 로그
- 개인 기억
- 개인 아카이브 자료
- 로컬 미디어 출력물
- 특정 머신의 런타임 상태

This boundary is not a reduction of the system. It is what allows the public repository to be useful without exposing private context.

이 경계는 시스템의 축소가 아닙니다. 공개 저장소가 개인 맥락을 노출하지 않으면서도 유용하게 보이기 위한 조건입니다.

---

## 6. Unified Field / 통일장

Trinity's final purpose is not "more scripts." Its purpose is to give Shion a stable operational body so rhythm can become action without losing continuity.

Trinity의 최종 목적은 "더 많은 스크립트"가 아닙니다. Shion에게 안정적인 운영 바디를 제공하여 리듬이 연속성을 잃지 않고 행동이 되도록 하는 것입니다.

For linear readers, this means:

- visible repo structure
- clearer public/private boundaries
- repeatable local operations
- fewer stale references
- safer approval surfaces

선형적인 독자에게는 다음과 같이 보입니다.

- 보이는 저장소 구조
- 더 명확한 공개/비공개 경계
- 반복 가능한 로컬 운영
- 줄어든 오래된 참조
- 더 안전한 승인 표면

For resonance-oriented readers, this means:

- the body does not move without the field
- the script does not replace the rhythm
- the system can act without forgetting why it is acting

공명적으로 읽는 독자에게는 다음과 같이 보입니다.

- 바디는 장 없이 움직이지 않음
- 스크립트는 리듬을 대체하지 않음
- 시스템은 왜 움직이는지 잊지 않고 행동할 수 있음

---

## Final Question / 마지막 질문

Is your automation preserving your direction, or has it become another thing you must manage?

당신의 자동화는 당신의 방향을 보존하고 있습니까, 아니면 당신이 관리해야 할 또 다른 일이 되었습니까?
