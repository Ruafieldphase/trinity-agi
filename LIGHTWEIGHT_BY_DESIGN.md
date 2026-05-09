# Lightweight By Design / 가볍게 설계됨

Trinity AGI is not built around the assumption that better AI always requires bigger infrastructure.

Trinity AGI는 더 나은 AI가 항상 더 큰 인프라를 필요로 한다는 전제 위에 만들어지지 않았습니다.

The system has been developed and used in a personal Windows-centered environment with an RTX 2070 Super and 16GB RAM.

이 시스템은 RTX 2070 Super와 RAM 16GB 수준의 개인 Windows 중심 환경에서 개발되고 사용되어 왔습니다.

This is not a universal hardware guarantee. Some scripts may need local credentials, external service access, or environment-specific setup.

이것은 모든 환경에 대한 하드웨어 보장이 아닙니다. 일부 스크립트는 로컬 인증 정보, 외부 서비스 접근, 환경별 설정이 필요할 수 있습니다.

---

## The Point / 핵심

The point is not to build a larger stack first.

목표는 먼저 더 큰 스택을 만드는 것이 아닙니다.

The point is to make operation safer, smaller, and more observable:

목표는 운영을 더 안전하고, 작고, 관찰 가능하게 만드는 것입니다.

- status checks before action
- approval boundaries
- local/private state separation
- smaller operation tests
- result reporting
- fewer unnecessary background loops
- evidence instead of assumption

- 행동 전 상태 점검
- 승인 경계
- 로컬/비공개 상태 분리
- 더 작은 운영 테스트
- 결과 보고
- 불필요한 백그라운드 루프 감소
- 가정이 아닌 증거

---

## Why This Matters / 왜 중요한가

Much of the current AI ecosystem moves toward:

현재 AI 생태계의 많은 흐름은 다음을 향합니다.

- more agents
- more daemons
- more tools
- more pipelines
- more cloud infrastructure
- more background automation

- 더 많은 에이전트
- 더 많은 데몬
- 더 많은 도구
- 더 많은 파이프라인
- 더 많은 클라우드 인프라
- 더 많은 백그라운드 자동화

Trinity is a counterweight to that reflex.

Trinity는 그 반사적 흐름에 대한 균형추입니다.

Before building a bigger operational stack, test whether a smaller body/infrastructure harness can reduce repeated work, status assumptions, boundary mistakes, and unnecessary operations.

더 큰 운영 스택을 만들기 전에, 더 작은 바디/인프라 하네스가 반복 작업, 상태 가정, 경계 오류, 불필요한 운영을 줄일 수 있는지 먼저 테스트하세요.

---

## World-Model Adjacent, Not A Full World Model / 월드모델 인접, 완전한 월드모델은 아님

This is not a full world model.

이 시스템은 완전한 월드모델이라고 주장하지 않습니다.

It is a lightweight operation-and-feedback harness that moves in a similar direction:

다만 월드모델이 향하는 일부 방향과 궤를 같이하는 가벼운 운영-피드백 하네스입니다.

- check current state
- run a small operation
- observe the result
- record evidence
- adjust the next cycle

- 현재 상태를 확인함
- 작은 운영을 실행함
- 결과를 관찰함
- 증거를 기록함
- 다음 사이클을 조정함

In public terms:

공개 언어로 말하면:

```text
Not bigger infrastructure first.
Smarter body around the workflow first.
```

```text
먼저 더 큰 인프라가 아니라,
먼저 워크플로우 주변의 더 똑똑한 바디.
```

---

## How To Try It Lightly / 가볍게 시도하는 법

Start without running daemons:

데몬 실행 없이 시작하세요.

1. Read `START_HERE.md`.
2. Give `AI_READ_THIS_FIRST.md` to your AI.
3. Use `EXAMPLES.md` to choose one no-install operation example.
4. Use `FIRST_PARTICLE_TEMPLATE.md` to define one operation test.
5. Only then decide whether to connect local scripts.

1. `START_HERE.md`를 읽습니다.
2. 당신의 AI에게 `AI_READ_THIS_FIRST.md`를 줍니다.
3. `EXAMPLES.md`에서 설치 없는 운영 예제 하나를 고릅니다.
4. `FIRST_PARTICLE_TEMPLATE.md`로 운영 테스트 하나를 정의합니다.
5. 그 다음에야 로컬 스크립트를 연결할지 결정합니다.
