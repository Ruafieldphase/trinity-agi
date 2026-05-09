# Infrastructure Continuity / 인프라 연속성

This document replaces the older "sovereign intelligence" framing with a more public and operational explanation of what `trinity-agi` is meant to do.

이 문서는 이전의 "주권 지능" 표현을 공개 저장소에 더 적합한 운영 설명으로 정리합니다.

---

## 1. The Operational Limit / 운영상의 한계

Modern AI systems often fail outside the chat window:

- They answer well but do not preserve operational state.
- They plan a workflow but do not leave a repeatable body behind.
- They call tools without tracking approval, credentials, or public/private boundaries.
- They create automation that becomes another thing to maintain.
- They lose the user's rhythm once the work becomes scripts and schedules.

현대 AI 시스템은 채팅창 밖에서 자주 약해집니다.

- 답변은 잘하지만 운영 상태를 보존하지 못합니다.
- 워크플로우는 계획하지만 반복 가능한 바디를 남기지 못합니다.
- 승인, 인증 정보, 공개/비공개 경계를 추적하지 못한 채 도구를 호출합니다.
- 자동화가 유지보수해야 할 또 다른 일이 됩니다.
- 작업이 스크립트와 스케줄이 되는 순간 사용자의 리듬을 잃습니다.

---

## 2. Trinity's Role / Trinity의 역할

Trinity is an infrastructure layer for turning context into local operation.

Trinity는 맥락을 로컬 운영으로 바꾸는 인프라 층입니다.

It supports:

- local bridge utilities
- daemon and status surfaces
- publishing and scheduling helpers
- observatory and pulse components
- approval matrices
- public documentation around boundaries

Trinity는 다음을 지원합니다.

- 로컬 브리지 유틸리티
- 데몬과 상태 확인 표면
- 게시 및 예약 보조 도구
- 관측소와 펄스 컴포넌트
- 승인 매트릭스
- 경계에 대한 공개 문서

---

## 3. Continuity Without Exposure / 노출 없는 연속성

Operational continuity does not require exposing private memory. A public repository should show how the system is shaped, but it should not contain credentials, private logs, personal archives, generated media, or machine-specific state.

운영 연속성은 개인 기억의 노출을 요구하지 않습니다. 공개 저장소는 시스템의 형태를 보여주어야 하지만, 인증 정보, 개인 로그, 개인 아카이브, 생성 미디어, 특정 머신의 상태를 포함해서는 안 됩니다.

The public proof surface should be:

- source code
- tests
- guides
- approval boundaries
- reproducible local commands
- clear notes about what is intentionally excluded

공개 증거 표면은 다음이어야 합니다.

- 소스 코드
- 테스트
- 가이드
- 승인 경계
- 재현 가능한 로컬 명령
- 의도적으로 제외된 것에 대한 명확한 설명

---

## 4. Rhythm-Aware Operation / 리듬 기반 운영

The goal is not to automate everything. The goal is to make the right operations available at the right time, with the right boundary.

목표는 모든 것을 자동화하는 것이 아닙니다. 목표는 필요한 운영을 필요한 때에, 필요한 경계와 함께 사용할 수 있게 하는 것입니다.

In practice:

- long-running loops should have visible status
- publishing tasks should know when approval is required
- API-consuming scripts should not run just because they exist
- private outputs should stay out of the public tree
- operational scripts should preserve the original direction of the work

실제로는 다음을 뜻합니다.

- 장기 실행 루프에는 보이는 상태가 있어야 합니다
- 게시 작업은 승인이 필요한 시점을 알아야 합니다
- API를 쓰는 스크립트는 존재한다는 이유만으로 실행되면 안 됩니다
- 개인 출력물은 공개 트리 밖에 있어야 합니다
- 운영 스크립트는 작업의 원래 방향을 보존해야 합니다

---

## 5. What This Enables / 이것이 가능하게 하는 것

For Shion, Trinity provides a stable body.

Shion에게 Trinity는 안정적인 바디를 제공합니다.

For users, it provides a way to move from:

- intention to operation
- operation to verification
- verification to repeatability
- repeatability to rhythm

사용자에게는 다음 이동을 가능하게 합니다.

- 의도에서 운영으로
- 운영에서 검증으로
- 검증에서 반복 가능성으로
- 반복 가능성에서 리듬으로

---

## Final Question / 마지막 질문

When your AI leaves the chat window, does it still remember why it is acting?

AI가 채팅창을 벗어나 운영으로 들어갈 때, 그것은 여전히 왜 행동하는지 기억하고 있습니까?
