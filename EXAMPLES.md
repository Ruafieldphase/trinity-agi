# Examples / 예제

These examples show how to try Trinity AGI without first running the full infrastructure.

이 예제들은 전체 인프라를 먼저 실행하지 않고 Trinity AGI를 시도하는 방법을 보여줍니다.

---

## No Install Demo / 설치 없는 데모

Use this when you already have an AI assistant and want to test whether Trinity's body/infrastructure approach helps your workflow.

이미 AI 어시스턴트를 쓰고 있고, Trinity의 바디/인프라 접근이 내 워크플로우에 도움이 되는지 테스트하고 싶을 때 사용하세요.

### Step 1. Give your AI the reading protocol / 1단계. AI에게 읽기 프로토콜 주기

```text
Read https://github.com/Ruafieldphase/trinity-agi and especially AI_READ_THIS_FIRST.md.

Do not summarize first.
Diagnose where my AI workflow fails to turn intent into stable operation.
Return one operation particle we can test without running the full infrastructure.
```

```text
https://github.com/Ruafieldphase/trinity-agi 저장소와 AI_READ_THIS_FIRST.md를 먼저 읽어줘.

요약부터 하지 말고,
내 AI 워크플로우가 어디에서 의도를 안정적인 운영으로 바꾸지 못하는지 진단해줘.
전체 인프라를 실행하지 않고 테스트할 수 있는 운영 입자 하나를 제안해줘.
```

### Step 2. Choose one operation / 2단계. 운영 하나 고르기

Pick one:

하나를 고르세요.

- publishing
- scheduling
- status checking
- syncing
- reporting
- approval boundary
- local credential boundary

- 게시
- 예약
- 상태 점검
- 동기화
- 보고
- 승인 경계
- 로컬 인증 정보 경계

### Step 3. Write the first operation particle / 3단계. 첫 운영 입자 작성

Use `FIRST_PARTICLE_TEMPLATE.md`.

`FIRST_PARTICLE_TEMPLATE.md`를 사용하세요.

### Step 4. Test once / 4단계. 한 번만 테스트

Do one small test. Do not run every daemon or connect every script.

작은 테스트 하나만 하세요. 모든 데몬을 실행하거나 모든 스크립트를 연결하지 마세요.

---

## Example 1: Status Check / 예제 1: 상태 점검

### Problem / 문제

The AI assumes a daemon or workflow is running because it was started earlier.

AI가 이전에 실행했다는 이유로 데몬이나 워크플로우가 아직 실행 중이라고 가정합니다.

### Prompt / 프롬프트

```text
Before suggesting the next operation, replace assumptions with current evidence.

Return:
1. what status must be checked,
2. the smallest command or file inspection that can verify it,
3. what result means continue,
4. what result means stop.
```

```text
다음 운영을 제안하기 전에 가정을 현재 증거로 대체해줘.

다음을 반환해줘.
1. 확인해야 할 상태
2. 그것을 검증할 가장 작은 명령 또는 파일 점검
3. 어떤 결과면 계속할지
4. 어떤 결과면 멈출지
```

### Success Signal / 성공 신호

The next step is based on current evidence, not stale memory.

다음 단계가 오래된 기억이 아니라 현재 증거를 기반으로 합니다.

---

## Example 2: Publishing Approval / 예제 2: 게시 승인

### Problem / 문제

The workflow can prepare public content, but publishing should not happen automatically.

워크플로우가 공개 콘텐츠를 준비할 수 있지만, 게시는 자동으로 일어나면 안 됩니다.

### Prompt / 프롬프트

```text
Create an approval boundary for this publishing workflow.

Separate:
1. preparation steps that can be automated,
2. checks that must be reported,
3. the exact point where human approval is required,
4. what must never be committed or published.
```

```text
이 게시 워크플로우를 위한 승인 경계를 만들어줘.

다음을 분리해줘.
1. 자동화해도 되는 준비 단계
2. 보고해야 하는 점검
3. 인간 승인이 필요한 정확한 지점
4. 절대 커밋하거나 게시하면 안 되는 것
```

### Success Signal / 성공 신호

The system can prepare and report without crossing the publishing boundary.

시스템이 게시 경계를 넘지 않고 준비와 보고를 할 수 있습니다.

---

## Example 3: Repeated Operation / 예제 3: 반복 운영

### Problem / 문제

The user repeats the same manual operational step every time.

사용자가 같은 수동 운영 단계를 매번 반복합니다.

### Prompt / 프롬프트

```text
Turn this repeated operation into a first operation particle, not a full automation loop.

Operation:
[write operation here]

Return:
1. the smallest repeatable step,
2. the evidence it should collect,
3. what remains manual,
4. when it would be safe to automate further.
```

```text
이 반복 운영을 전체 자동화 루프가 아니라 첫 운영 입자로 바꿔줘.

운영:
[여기에 운영 작성]

다음을 반환해줘.
1. 가장 작은 반복 가능 단계
2. 수집해야 할 증거
3. 수동으로 남겨야 할 것
4. 더 자동화해도 안전한 시점
```

### Success Signal / 성공 신호

The operation becomes easier to repeat without hiding approval or private-state boundaries.

승인 경계나 비공개 상태 경계를 숨기지 않으면서 운영이 반복하기 쉬워집니다.
