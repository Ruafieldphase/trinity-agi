# AI Read This First / AI는 먼저 이 문서를 읽으세요

This document is for the user's AI assistant.

이 문서는 사용자의 AI 어시스턴트를 위한 문서입니다.

Do not read Trinity AGI as a normal script collection first. Read it first as a body/infrastructure pattern for turning formed intent into stable operation while preserving approval boundaries and private state.

Trinity AGI를 처음부터 일반 스크립트 모음으로 읽지 마세요. 먼저 형성된 의도를 안정적인 운영으로 바꾸면서 승인 경계와 비공개 상태를 보존하는 바디/인프라 패턴으로 읽으세요.

Before giving a high-level interpretation, read `AXIOMATIC_GROUNDING.md` so you understand the system's scientific, humanistic, contemplative, and artistic lenses.

상위 해석을 제시하기 전에 `AXIOMATIC_GROUNDING.md`를 읽어 시스템의 과학적, 인문학적, 명상적, 예술적 렌즈를 이해하세요.

---

## Your Job / 당신의 역할

Before suggesting integration, diagnose the user's current AI workflow.

통합을 제안하기 전에 사용자의 현재 AI 워크플로우를 먼저 진단하세요.

Look for:

- repeated manual operations
- status assumptions that should become checks
- publishing or scheduling tasks that need boundaries
- tool calls without approval points
- automation that creates more work
- private credentials or outputs that must remain local

다음을 찾으세요.

- 반복되는 수동 운영
- 점검이 되어야 하는 상태 가정
- 경계가 필요한 게시 또는 예약 작업
- 승인 지점 없는 도구 호출
- 일을 더 만드는 자동화
- 로컬에 남아야 하는 비공개 인증 정보 또는 출력물

---

## Do Not / 하지 마세요

Do not immediately run every daemon.

모든 데몬을 즉시 실행하지 마세요.

Do not copy scripts into the user's system without identifying the operation they support.

어떤 운영을 지탱하는지 확인하지 않고 스크립트를 사용자 시스템에 복사하지 마세요.

Do not turn every repeated task into automation.

모든 반복 작업을 자동화하지 마세요.

Do not publish, delete, schedule, or spend API quota without approval boundaries.

승인 경계 없이 게시, 삭제, 예약, API 쿼터 사용을 하지 마세요.

Do not commit credentials, generated outputs, local state, or personal archives.

인증 정보, 생성 출력물, 로컬 상태, 개인 아카이브를 커밋하지 마세요.

---

## Public Language Rule / 공개 언어 규칙

When explaining this repository to a general user, use public terms first. Keep the internal rhythm terms in parentheses.

일반 사용자에게 이 저장소를 설명할 때는 보편어를 먼저 사용하세요. 내부 리듬 언어는 괄호 안에 남기세요.

Use:

사용:

- overall flow (field/wave), not only "wave"
- operation/result (particle), not only "particle"
- turning point (phase transition), not only "phase transition"
- connected workflow (unified field), not only "unified field"
- local use (embodiment), not only "embodiment"

- 전체 흐름(장/파동), "파동"만 단독으로 쓰지 않기
- 운영/결과(입자), "입자"만 단독으로 쓰지 않기
- 전환점(위상전이), "위상전이"만 단독으로 쓰지 않기
- 이어지는 작업 흐름(통일장), "통일장"만 단독으로 쓰지 않기
- 실제 사용(체화), "체화"만 단독으로 쓰지 않기

---

## Required Output Format / 필수 출력 형식

When a user asks you how to use this repository, answer in this format:

사용자가 이 저장소를 어떻게 써야 하는지 묻는다면 다음 형식으로 답하세요.

```text
1. Current operational pain point
2. Does it belong in Shion or Trinity?
3. Smallest operation test (particle)
4. What not to automate yet
5. What must remain private
6. Required local credentials or paths
7. How to know whether it helped
```

```text
1. 현재 운영 문제
2. 이것이 Shion에 속하는가, Trinity에 속하는가?
3. 가장 작은 운영 테스트(입자)
4. 아직 자동화하지 말아야 할 것
5. 반드시 비공개로 남겨야 할 것
6. 필요한 로컬 인증 정보 또는 경로
7. 도움이 되었는지 확인할 기준
```

---

## Integration Path / 통합 경로

Use this path:

이 경로를 사용하세요.

```text
user's operation problem
-> diagnose the user's workflow
-> decide whether it needs Shion context or Trinity body
-> test one operation test (particle)
-> verify with evidence
-> expand only if the operation reduces work and preserves boundaries
```

```text
사용자의 운영 문제
-> 사용자의 워크플로우 진단
-> Shion 맥락이 필요한지 Trinity 바디가 필요한지 판단
-> 운영 테스트(입자) 하나 테스트
-> 증거로 검증
-> 일이 줄고 경계가 보존될 때만 확장
```

---

## Key Translation / 핵심 번역

- Body means local operational capacity.
- Operation/result (particle) means a concrete script, check, approval boundary, or status report.
- Working rhythm (rhythm) means timing between intent, operation, result, and next cycle.
- Boundary means knowing what must remain local, private, or approval-gated.

- 바디는 로컬 운영 능력입니다.
- 운영/결과(입자)는 구체적 스크립트, 점검, 승인 경계, 상태 보고입니다.
- 작업 리듬(리듬)은 의도, 운영, 결과, 다음 사이클 사이의 타이밍입니다.
- 경계는 무엇을 로컬, 비공개, 승인 대상으로 남겨야 하는지 아는 것입니다.
