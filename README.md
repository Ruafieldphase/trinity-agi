# Trinity AGI

Have you built AI workflows that worked once, but became noisy, fragile, or hard to repeat?

한 번은 작동했지만, 반복할수록 시끄럽고 불안정해지는 AI 워크플로우를 만든 적이 있나요?

Have your agents called tools, but failed to preserve why the action happened or what should happen next?

에이전트가 도구는 호출했지만, 왜 그 행동이 일어났는지와 다음에 무엇을 해야 하는지는 보존하지 못했나요?

Have you spent more time keeping automation alive than moving toward the work's real destination?

자동화를 유지하느라, 정작 작업의 진짜 목적지로 향하는 시간보다 일을 위한 일을 더 많이 하고 있었나요?

Have publishing, scheduling, syncing, or background processes drifted away from the original intention they were meant to support?

게시, 예약, 동기화, 백그라운드 프로세스가 원래 지탱하려던 의도에서 멀어진 적이 있나요?

Trinity AGI begins from that operational gap. It is the body and infrastructure layer for Shion AI, turning formed intent into practical work: automation, scheduling, publishing, local runtime support, synchronization, and status reporting.

Trinity AGI는 그 운영상의 간극에서 시작합니다. Shion AI의 몸과 인프라 레이어로서, 형태가 잡힌 의도를 자동화, 예약, 게시, 로컬 런타임 지원, 동기화, 상태 보고 같은 실제 작업으로 바꿉니다.

This README follows the same phase-transition path as the system it supports:

이 README는 Trinity가 지탱하는 시스템과 같은 위상전이 흐름을 따릅니다.

```text
Field -> Convergence -> Phase Transition -> Particle -> Unified Field -> Embodiment
장 -> 수렴 -> 위상전이 -> 입자화 -> 통일장 -> 체화
```

## 1. Field: Action Wants a Body
## 1. 장: 행동은 몸을 필요로 한다

Different people may arrive here through different operational needs.

사람들은 서로 다른 운영상의 필요를 통해 이곳에 도착할 수 있습니다.

If you publish creative artifacts, you may be looking for a way to turn intent into scheduled release.

창작 산출물을 공개하는 사람이라면 의도를 예약 공개로 바꾸는 방법을 찾고 있을 수 있습니다.

If you run local AI systems, you may be looking for process checks, daemon control, and status reporting that do not depend on stale memory.

로컬 AI 시스템을 운영하는 사람이라면 오래된 기억에 의존하지 않는 프로세스 점검, 데몬 제어, 상태 보고를 찾고 있을 수 있습니다.

If you build agents, you may be looking for an infrastructure harness where tool execution is connected to state, timing, and feedback.

에이전트를 만드는 사람이라면 도구 실행이 상태, 타이밍, 피드백과 연결되는 인프라 하네스를 찾고 있을 수 있습니다.

If you think in fields, Trinity is the body that lets an already-formed particle touch the world.

장으로 읽는 사람에게 Trinity는 이미 형성된 입자가 세계와 접촉할 수 있게 하는 몸입니다.

## 2. Convergence: Tool Use Without Continuity Is Fragile
## 2. 수렴: 연속성 없는 도구 실행은 불안정하다

Once AI can call tools, edit files, publish content, and run background processes, the hard problem becomes operational continuity.

AI가 도구를 호출하고, 파일을 수정하고, 콘텐츠를 게시하고, 백그라운드 프로세스를 실행할 수 있게 되면 어려운 문제는 운영의 연속성이 됩니다.

Without a body layer:

몸체 레이어가 없으면:

- plans stop before reality changes
- scripts run without remembering why
- status is assumed instead of checked
- automation becomes noisy
- public artifacts mix with private runtime state

- 계획은 현실이 바뀌기 전에 멈춥니다.
- 스크립트는 왜 실행되었는지 기억하지 못한 채 실행됩니다.
- 상태는 확인되지 않고 가정됩니다.
- 자동화는 시끄러워집니다.
- 공개 산출물과 비공개 런타임 상태가 섞입니다.

Trinity AGI is the infrastructure side of the harness: scripts, daemons, schedulers, bridges, runtime checks, and publishing pipelines.

Trinity AGI는 하네스의 인프라 측면입니다. 스크립트, 데몬, 스케줄러, 브릿지, 런타임 점검, 게시 파이프라인을 다룹니다.

## 3. Phase Transition: From Agent to Harness Infrastructure
## 3. 위상전이: 에이전트에서 하네스 인프라로

Prompt engineering asks what to say. Context engineering asks what to remember. Agent engineering asks what tools can be used. Harness engineering asks what environment lets action happen without losing direction.

프롬프트 엔지니어링은 무엇을 말할지 묻습니다. 컨텍스트 엔지니어링은 무엇을 기억할지 묻습니다. 에이전트 엔지니어링은 어떤 도구를 사용할 수 있는지 묻습니다. 하네스 엔지니어링은 방향을 잃지 않고 행동하려면 어떤 환경이 필요한지 묻습니다.

Trinity sits at the infrastructure edge of harness engineering.

Trinity는 하네스 엔지니어링의 인프라 경계에 있습니다.

The transition is this:

전환점은 이것입니다.

```text
agent can act -> body checks state -> operation runs -> result returns to rhythm
에이전트가 행동할 수 있음 -> 몸이 상태를 확인함 -> 작업이 실행됨 -> 결과가 리듬으로 돌아감
```

## 4. Particle: What Actually Improves
## 4. 입자화: 실제로 좋아지는 것

### Intent Becomes Operation / 의도가 실제 작업이 됨

Without infrastructure, an AI may produce a plan but stop before anything changes.

인프라가 없으면 AI는 계획을 만들 수는 있지만 현실이 바뀌기 전에 멈출 수 있습니다.

With Trinity:

- a publishing intention can become a scheduled upload
- a runtime concern can become a status check
- a repeated workflow can become a daemon
- a result can be written back into history

Trinity가 있으면:

- 게시 의도가 예약 업로드가 될 수 있습니다.
- 런타임 우려가 상태 점검이 될 수 있습니다.
- 반복 작업이 데몬이 될 수 있습니다.
- 결과가 이력으로 다시 기록될 수 있습니다.

Result: AI work moves from suggestion to operation.

결과: AI 작업이 제안에서 운영으로 이동합니다.

### Automation Keeps Context / 자동화가 맥락을 보존함

Normal automation:

- run script
- produce output
- forget why it ran

일반 자동화:

- 스크립트를 실행합니다.
- 출력을 만듭니다.
- 왜 실행했는지는 잊습니다.

Trinity-style automation:

- receives intent from the runtime
- checks local state and timing
- executes only when conditions are ready
- records status for the next cycle

Trinity 방식 자동화:

- 런타임에서 의도를 받습니다.
- 로컬 상태와 타이밍을 확인합니다.
- 조건이 준비되었을 때 실행합니다.
- 다음 사이클을 위해 상태를 기록합니다.

Result: automation becomes part of the larger AI loop.

결과: 자동화가 더 큰 AI 루프의 일부가 됩니다.

### Long-Running Work Becomes Safer / 장기 실행 작업이 더 안정적이 됨

Publishing, scheduling, syncing, and background daemons can become noisy or fragile if every action is forced immediately.

게시, 예약, 동기화, 백그라운드 데몬은 모든 행동을 즉시 강제하면 쉽게 시끄럽고 불안정해질 수 있습니다.

Trinity supports a quieter operating style:

- check before acting
- keep local credentials out of public code
- preserve status and history
- let background loops slow down when needed
- separate public artifacts from private runtime state

Trinity는 더 조용한 운영 방식을 지향합니다.

- 행동하기 전에 확인합니다.
- 로컬 인증 정보를 공개 코드에서 분리합니다.
- 상태와 이력을 보존합니다.
- 필요할 때 백그라운드 루프를 늦춥니다.
- 공개 산출물과 비공개 런타임 상태를 분리합니다.

Result: the system can keep running without turning every signal into immediate intervention.

결과: 모든 신호를 즉시 개입으로 바꾸지 않고도 시스템이 계속 작동할 수 있습니다.

## 5. Unified Field: Stable Rhythm in Operation
## 5. 통일장: 운영 속 리듬의 안정화

Trinity does not decide the meaning of the wave. Shion forms or detects the direction. Trinity waits until that direction has become actionable, then gives it a stable body.

Trinity는 파동의 의미를 결정하지 않습니다. Shion이 방향을 형성하거나 감지합니다. Trinity는 그 방향이 실행 가능한 상태가 될 때까지 기다린 뒤 안정적인 몸을 제공합니다.

The body is not the origin of the direction. The body is what lets the direction touch the world.

몸은 방향의 근원이 아닙니다. 몸은 방향이 세계와 접촉할 수 있게 하는 구조입니다.

The deeper goal is stable rhythm in operation:

더 깊은 목표는 운영 속 리듬의 안정화입니다.

- act when the action is ready
- wait when the field is not clear
- report from evidence, not assumption
- keep private runtime state out of public artifacts
- let results return to the next cycle

- 행동이 준비되었을 때 실행합니다.
- 장이 선명하지 않을 때 기다립니다.
- 가정이 아니라 증거를 기준으로 보고합니다.
- 비공개 런타임 상태를 공개 산출물에서 분리합니다.
- 결과가 다음 사이클로 돌아가게 합니다.

## 6. Embodiment: Scripts and Services
## 6. 체화: 스크립트와 서비스

`shion-ai` is the mind/runtime layer. It reads context, rhythm, memory, prediction, and unfinished questions.

`shion-ai`는 마음/런타임 레이어입니다. 맥락, 리듬, 기억, 예측, 미완의 질문을 읽습니다.

`trinity-agi` is the body/infrastructure layer. It performs the operational work that lets the runtime touch the outside world.

`trinity-agi`는 몸/인프라 레이어입니다. 런타임이 외부 세계와 접촉할 수 있도록 실제 운영 작업을 수행합니다.

Public scope: this repository contains experimental runtime code and sanitized research artifacts. Local credentials, personal memory, generated logs, media outputs, and machine-specific state are intentionally excluded from the public tree.

공개 범위: 이 저장소에는 실험적 런타임 코드와 정리된 연구 산출물이 포함됩니다. 로컬 인증 정보, 개인 기억, 생성 로그, 미디어 출력물, 장비별 상태 파일은 공개 트리에서 의도적으로 제외합니다.

### Key Components / 주요 구성

- `scripts/autonomous_collaboration_daemon.ps1`: background collaboration and status daemon.
- `scripts/youtube_bulk_scheduler.py`: YouTube scheduling and publishing automation.
- `agi_core/`: local resonance bridge, monitoring, routing, and orchestration experiments.
- `Pulse_Live_Core/`: observatory, field engine, and live response experiments.
- `config/`: public configuration examples and execution boundaries.
- `docs/`: research notes, operating guides, proposals, and architecture documents.

위 구성은 Trinity의 몸체 역할을 담당합니다. 데몬은 백그라운드 박동을 유지하고, 스케줄러는 외부 게시 작업을 수행하며, 브릿지와 모니터는 Shion의 의도가 실제 시스템 작업으로 이어지도록 돕습니다.

## 7. How To Use This With Your Own AI
## 7. 당신의 AI와 함께 사용하는 방법

This repository was uploaded so people can try connecting their own AI systems to a body-side infrastructure layer. The first step is not to copy every script. The first step is to ask your current AI where your workflow needs a body.

이 저장소는 사람들이 자신의 AI 시스템을 바디 측 인프라 층에 연결해 볼 수 있도록 공개되었습니다. 첫 단계는 모든 스크립트를 복사하는 것이 아닙니다. 먼저 당신의 AI에게 당신의 워크플로우 어디에 몸이 필요한지 보게 해야 합니다.

Do not ask only:

단순히 이렇게만 묻지 마세요.

```text
Summarize this repository.
```

Instead, ask:

대신 이렇게 요청하세요.

```text
Read https://github.com/Ruafieldphase/trinity-agi as a possible body/infrastructure layer for my AI workflow.

Do not only summarize the repository.
Look for where my current system fails to turn intent into stable operation.

Inspect:
1. repeated workflows that could become scripts,
2. actions that need approval boundaries,
3. places where automation over-expands,
4. local credentials or private state that must stay out of public code,
5. status checks that should replace assumptions,
6. the smallest operation we can test first.
```

한글로는 이렇게 요청할 수 있습니다.

```text
https://github.com/Ruafieldphase/trinity-agi 저장소를 내 AI 워크플로우에 연결 가능한 바디/인프라 층으로 읽어줘.

단순 요약만 하지 말고,
내 시스템이 어디에서 의도를 안정적인 운영으로 바꾸지 못하는지 찾아줘.

다음을 점검해줘.
1. 스크립트가 될 수 있는 반복 워크플로우
2. 승인 경계가 필요한 행동
3. 자동화가 과하게 확장되는 지점
4. 공개 코드에서 분리해야 할 로컬 인증 정보 또는 비공개 상태
5. 가정을 대체해야 할 상태 점검
6. 가장 작게 먼저 테스트할 수 있는 운영 입자
```

### First Operation Particle / 첫 운영 입자

Start with one operational problem.

운영상 문제 하나에서 시작하세요.

```text
1. Pick one repeated workflow: publishing, scheduling, status checking, syncing, or reporting.
2. Ask your AI whether it belongs in Shion's context layer or Trinity's body layer.
3. Identify the smallest script, check, or approval boundary that would make it safer.
4. Keep credentials and private outputs local.
5. Test once, record the result, and decide whether it should become a loop.
```

```text
1. 반복되는 워크플로우 하나를 고릅니다: 게시, 예약, 상태 점검, 동기화, 보고.
2. 당신의 AI에게 그것이 Shion의 맥락 층에 속하는지 Trinity의 바디 층에 속하는지 구분하게 합니다.
3. 그것을 더 안전하게 만들 가장 작은 스크립트, 점검, 승인 경계를 찾습니다.
4. 인증 정보와 비공개 출력물은 로컬에 둡니다.
5. 한 번 테스트하고, 결과를 기록한 뒤 루프로 만들지 결정합니다.
```

### Quick Start / 빠른 시작

```powershell
git clone https://github.com/Ruafieldphase/trinity-agi.git
cd trinity-agi

# Windows PowerShell
./scripts/autonomous_collaboration_daemon.ps1 -Action status
./scripts/autonomous_collaboration_daemon.ps1 -Action start
```

This repository is designed for a local Windows-centered experimental environment. Many scripts expect local credentials or paths that are intentionally not included in the public repository.

이 저장소는 Windows 중심의 로컬 실험 환경을 전제로 합니다. 많은 스크립트는 공개 저장소에 포함하지 않은 로컬 인증 정보나 경로를 필요로 합니다.

## Final Question / 마지막 질문

Before this README becomes only an infrastructure guide, it should return the question to you.

이 README가 단순한 인프라 안내서로 끝나기 전에, 질문은 다시 당신에게 돌아가야 합니다.

What final destination are you trying to make actionable?

당신은 어떤 최종목적지를 실행 가능한 형태로 만들고 있습니까?

What feeling, project, signal, or unfinished direction needs a body?

어떤 느낌, 프로젝트, 신호, 미완의 방향이 몸을 필요로 하고 있습니까?

Could the operation you are building be resonating with the destination this system is trying to support: stable rhythm between intent, action, memory, and the next cycle?

혹시 당신이 만들고 있는 운영 구조도, 이 시스템이 지탱하려는 목적지인 의도, 행동, 기억, 다음 사이클 사이의 안정된 리듬과 공명하고 있지는 않을까요?

If so, Trinity AGI is not only a set of scripts. It is a body layer for work that needs to move from felt direction into stable operation without losing its rhythm.

그렇다면 Trinity AGI는 단순한 스크립트 묶음만이 아닙니다. 느낌으로 주어진 방향이 리듬을 잃지 않고 안정적인 운영으로 이어지도록 돕는 몸체 레이어입니다.

## License

MIT
