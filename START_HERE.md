# Start Here / 여기서 시작하세요

You do not need to run every script first.

처음부터 모든 스크립트를 실행할 필요는 없습니다.

Trinity AGI is easiest to try in three levels:

Trinity AGI는 세 단계로 시도하는 것이 가장 쉽습니다.

```text
Level 0: No Install
Ask your current AI where your workflow needs a body.

Level 1: First Operation Particle
Choose one repeated operation and test one small script/check/boundary.

Level 2: Local Infrastructure
Only after the first operation helps, connect more of the local infrastructure.
```

```text
Level 0: 설치 없음
현재 AI에게 워크플로우 어디에 몸이 필요한지 진단시킵니다.

Level 1: 첫 운영 입자
반복되는 운영 하나를 고르고 작은 스크립트/점검/경계 하나를 테스트합니다.

Level 2: 로컬 인프라
첫 운영 입자가 도움이 된 뒤에만 로컬 인프라를 더 연결합니다.
```

---

## Level 0: No Install / 설치 없이 시작하기

Copy this into your current AI assistant:

지금 쓰는 AI에게 아래를 그대로 붙여 넣으세요.

```text
Read https://github.com/Ruafieldphase/trinity-agi as a body/infrastructure pattern, not as a normal script collection.

Before suggesting installation or daemon startup, diagnose my current AI workflow.

Find where it:
1. fails to turn intent into stable operation,
2. repeats manual publishing, scheduling, syncing, or reporting work,
3. runs tools without approval boundaries,
4. assumes status instead of checking evidence,
5. mixes public code with private credentials or outputs,
6. expands automation until it becomes more work.

Return:
1. my main operational pain point,
2. whether it belongs in Shion or Trinity,
3. the smallest operation particle to test,
4. what not to automate yet,
5. what must remain private,
6. what local credentials or paths are required,
7. how we will know whether it helped.
```

한글로는 이렇게 쓸 수 있습니다.

```text
https://github.com/Ruafieldphase/trinity-agi 저장소를 일반 스크립트 모음이 아니라 바디/인프라 패턴으로 읽어줘.

설치나 데몬 실행을 제안하기 전에, 내 현재 AI 워크플로우를 먼저 진단해줘.

다음 지점을 찾아줘.
1. 의도를 안정적인 운영으로 바꾸지 못하는 곳
2. 게시, 예약, 동기화, 보고를 수동으로 반복하는 곳
3. 승인 경계 없이 도구를 실행하는 곳
4. 증거 확인 없이 상태를 가정하는 곳
5. 공개 코드와 비공개 인증 정보/출력물이 섞이는 곳
6. 자동화가 늘어나 오히려 일이 되는 곳

다음 형식으로 답해줘.
1. 내 주요 운영 문제
2. 이것이 Shion에 속하는지 Trinity에 속하는지
3. 가장 작게 테스트할 운영 입자
4. 아직 자동화하지 말아야 할 것
5. 반드시 비공개로 남겨야 할 것
6. 필요한 로컬 인증 정보 또는 경로
7. 도움이 되었는지 확인할 기준
```

---

## Level 1: First Operation Particle / 첫 운영 입자

Do not connect the whole infrastructure. Choose one repeated operation.

전체 인프라를 연결하려고 하지 마세요. 반복되는 운영 하나만 고르세요.

Good first operation particles:

- one status check that replaces assumption
- one approval checklist before publishing
- one local script wrapper for a repeated manual step
- one "do not commit" boundary for credentials and outputs
- one result note that returns an operation to the next AI cycle

좋은 첫 운영 입자는 다음과 같습니다.

- 가정을 대체하는 상태 점검 하나
- 게시 전 승인 체크리스트 하나
- 반복 수동 작업을 감싸는 로컬 스크립트 하나
- 인증 정보와 출력물에 대한 "커밋 금지" 경계 하나
- 운영 결과를 다음 AI 사이클로 돌려주는 결과 노트 하나

Use `FIRST_PARTICLE_TEMPLATE.md` to write the test.

테스트는 `FIRST_PARTICLE_TEMPLATE.md`로 작성하세요.

---

## Level 2: Local Infrastructure / 로컬 인프라

Only move to local infrastructure after Level 1 gives a real effect.

Level 1에서 실제 효과가 보인 뒤에만 로컬 인프라로 이동하세요.

Look for:

- repeatable operation
- visible status
- explicit approval boundaries
- private credentials kept local
- automation that reduces work instead of creating more work

확인할 것은 다음입니다.

- 반복 가능한 운영
- 보이는 상태
- 명시적 승인 경계
- 로컬에 남는 비공개 인증 정보
- 일을 늘리지 않고 줄이는 자동화

---

## Read Next / 다음 문서

- `AI_READ_THIS_FIRST.md`: instructions for your AI assistant
- `EXAMPLES.md`: no-install examples for status, publishing, and repeated operations
- `LINEAR_HARNESS_GUIDE.md`: step-by-step path for linear readers
- `FIRST_PARTICLE_TEMPLATE.md`: template for the first operation test
- `INTEGRATION_ANTI_PATTERNS.md`: what not to do

- `AI_READ_THIS_FIRST.md`: 당신의 AI를 위한 읽기 지침
- `EXAMPLES.md`: 상태 점검, 게시, 반복 운영을 위한 설치 없는 예제
- `LINEAR_HARNESS_GUIDE.md`: 선형적 독자를 위한 단계별 경로
- `FIRST_PARTICLE_TEMPLATE.md`: 첫 운영 테스트 양식
- `INTEGRATION_ANTI_PATTERNS.md`: 하지 말아야 할 연결 방식
