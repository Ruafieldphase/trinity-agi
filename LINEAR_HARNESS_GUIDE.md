# Linear Harness Guide / 선형 하네스 가이드

This guide is for readers who prefer a clear step-by-step path.

이 문서는 명확한 단계별 경로를 선호하는 독자를 위한 가이드입니다.

The linear harness is only an entry rail. It should not replace the deeper rhythm between intent, operation, memory, and the next cycle.

선형 하네스는 진입 레일일 뿐입니다. 의도, 운영, 기억, 다음 사이클 사이의 더 깊은 리듬을 대체하면 안 됩니다.

---

## Step 1. Choose One Operation / 운영 하나 고르기

Pick one:

하나를 고르세요.

- publishing
- scheduling
- status checking
- syncing
- reporting
- approval before action
- local credential boundary

- 게시
- 예약
- 상태 점검
- 동기화
- 보고
- 행동 전 승인
- 로컬 인증 정보 경계

---

## Step 2. Ask Your AI To Diagnose / AI에게 진단시키기

Use:

사용:

```text
Before suggesting scripts, diagnose this operational problem:
[write one operation here]

Tell me whether it needs Shion context or Trinity body, and what the smallest safe operation test (particle) is.
```

```text
스크립트를 제안하기 전에 이 운영 문제를 진단해줘.
[여기에 운영 하나 작성]

이것이 Shion 맥락이 필요한지 Trinity 바디가 필요한지, 가장 작고 안전한 운영 테스트(입자)가 무엇인지 알려줘.
```

---

## Step 3. Select One Trinity Layer / Trinity 층 하나 고르기

Choose one:

하나를 고르세요.

- script wrapper
- status check
- approval boundary
- publishing helper
- scheduling helper
- public/private separation
- result reporting

- 스크립트 래퍼
- 상태 점검
- 승인 경계
- 게시 보조
- 예약 보조
- 공개/비공개 분리
- 결과 보고

---

## Step 4. Write One Operation Test (Particle) / 운영 테스트(입자) 하나 쓰기

Use `FIRST_PARTICLE_TEMPLATE.md`.

`FIRST_PARTICLE_TEMPLATE.md`를 사용하세요.

The first operation test (particle) should be small enough to test once.

첫 운영 테스트(입자)는 한 번 테스트할 수 있을 만큼 작아야 합니다.

---

## Step 5. Verify With Evidence / 증거로 검증하기

Good evidence:

좋은 증거:

- current status output
- explicit approval record
- one generated report
- one dry-run result
- one local-only credential check
- one note returned to the next AI cycle

- 현재 상태 출력
- 명시적 승인 기록
- 생성된 보고서 하나
- 드라이런 결과 하나
- 로컬 전용 인증 정보 점검 하나
- 다음 AI 사이클로 돌아가는 노트 하나

---

## Step 6. Decide Whether To Expand / 확장 여부 결정

Expand only if:

다음이 확인될 때만 확장하세요.

- the operation became easier to repeat
- status is based on evidence
- private state stayed private
- approval boundaries stayed visible
- automation reduced work instead of adding work

- 운영이 반복하기 쉬워졌다
- 상태가 증거를 기반으로 한다
- 비공개 상태가 비공개로 남았다
- 승인 경계가 보인다
- 자동화가 일을 늘리지 않고 줄였다
