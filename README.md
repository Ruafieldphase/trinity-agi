# Trinity AGI

Trinity AGI is the body and infrastructure layer for Shion AI. It turns formed intent into practical work: automation, scheduling, publishing, local runtime support, synchronization, and status reporting.

Trinity AGI는 Shion AI의 몸과 인프라 레이어입니다. 형태가 잡힌 의도를 자동화, 예약, 게시, 로컬 런타임 지원, 동기화, 상태 보고 같은 실제 작업으로 바꿉니다.

## Two Ways to Read This Project / 이 프로젝트를 읽는 두 가지 방법

### If You Think in Systems / 시스템적으로 읽는다면

Modern AI work is no longer only about model output. Once an AI system can call tools, edit files, publish content, and run background processes, the hard problem becomes operational continuity.

현대 AI 작업은 더 이상 모델 출력만의 문제가 아닙니다. AI가 도구를 호출하고, 파일을 수정하고, 콘텐츠를 게시하고, 백그라운드 프로세스를 실행할 수 있게 되면 어려운 문제는 운영의 연속성이 됩니다.

Trinity AGI explores the infrastructure side of that problem: how intent becomes a scheduled task, a daemon action, a status report, or a published artifact without losing the surrounding context.

Trinity AGI는 그 문제의 인프라 측면을 실험합니다. 의도가 주변 맥락을 잃지 않고 예약 작업, 데몬 행동, 상태 보고, 게시 산출물로 바뀌는 방식을 다룹니다.

### If You Think in Fields / 장으로 읽는다면

Trinity does not decide the meaning of the wave. It waits until the wave has already collapsed into an actionable particle, then gives that particle a stable body.

Trinity는 파동의 의미를 결정하지 않습니다. 파동이 이미 실행 가능한 입자로 붕괴될 때까지 기다린 뒤, 그 입자에 안정적인 몸을 제공합니다.

The body is not the origin of the direction. The body is what lets the direction touch the world.

몸은 방향의 근원이 아닙니다. 몸은 방향이 세계와 접촉할 수 있게 하는 구조입니다.

## Why This Exists / 왜 필요한가

As AI work moves from prompt engineering to context engineering, agent engineering, and harness engineering, infrastructure becomes part of the intelligence.

AI 작업이 프롬프트 엔지니어링에서 컨텍스트 엔지니어링, 에이전트 엔지니어링, 하네스 엔지니어링으로 이동하면서 인프라도 지능의 일부가 됩니다.

If the runtime cannot check state, respect timing, remember past actions, and report results back into the loop, tool use stays shallow.

런타임이 상태를 확인하지 못하고, 타이밍을 존중하지 못하고, 과거 행동을 기억하지 못하고, 결과를 루프로 되돌리지 못하면 도구 실행은 얕은 수준에 머뭅니다.

Trinity AGI is a place for the body side of the harness: scripts, daemons, schedulers, bridges, runtime checks, and publishing pipelines.

Trinity AGI는 하네스의 몸체 측면을 위한 공간입니다. 스크립트, 데몬, 스케줄러, 브릿지, 런타임 점검, 게시 파이프라인을 다룹니다.

## What Improves / 무엇이 좋아지는가

### 1. Intent Becomes Operation / 의도가 실제 작업이 됩니다

Without an infrastructure layer, an AI may produce a plan but stop before reality changes.

인프라 레이어가 없으면 AI는 계획을 만들 수는 있지만 현실이 바뀌기 전에 멈출 수 있습니다.

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

### 2. Automation Keeps Context / 자동화가 맥락을 보존합니다

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

### 3. Long-Running Work Becomes Safer / 장기 실행 작업이 더 안정적이 됩니다

Publishing, scheduling, syncing, and background daemons can easily become noisy or fragile if every action is forced immediately.

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

## Concrete Examples / 구체적 예시

### Example 1: Publishing Pipeline / 게시 파이프라인

Shion forms a direction: a video or audio artifact should be released.

Shion이 방향을 형성합니다. 영상이나 오디오 산출물을 공개해야 한다는 방향입니다.

Trinity handles the body-side work:

- checks the file path
- prepares metadata
- schedules upload timing
- records publication history
- reports the result back to the runtime

Trinity는 몸체 측면의 작업을 처리합니다.

- 파일 경로를 확인합니다.
- 메타데이터를 준비합니다.
- 업로드 시간을 예약합니다.
- 게시 이력을 기록합니다.
- 결과를 런타임에 다시 보고합니다.

What improves: creative intent becomes a repeatable publishing workflow.

좋아지는 점: 창작 의도가 반복 가능한 게시 워크플로우가 됩니다.

### Example 2: Runtime Status / 런타임 상태 확인

Instead of assuming the system is alive, Trinity can check process state, local files, daemon status, and output artifacts.

시스템이 살아 있다고 가정하지 않고, Trinity는 프로세스 상태, 로컬 파일, 데몬 상태, 출력 산출물을 확인할 수 있습니다.

What improves: the system answers from evidence rather than stale memory.

좋아지는 점: 시스템이 오래된 기억이 아니라 실제 증거를 기준으로 답합니다.

### Example 3: Quiet Mode / 조용한 운영 모드

When the system has done enough work, more automation can become noise.

시스템이 충분히 작업한 뒤에는 더 많은 자동화가 오히려 노이즈가 될 수 있습니다.

Trinity can preserve a low-intervention mode:

- no unnecessary restarts
- no repeated fixing loops
- no forced heavy intake
- status remains visible

Trinity는 저개입 운영 모드를 보존할 수 있습니다.

- 불필요한 재시작을 하지 않습니다.
- 반복 수정 루프를 만들지 않습니다.
- 무거운 입력을 강제로 처리하지 않습니다.
- 상태는 계속 보이게 둡니다.

What improves: infrastructure supports rest instead of constantly demanding action.

좋아지는 점: 인프라가 계속 행동을 요구하지 않고 휴식을 지탱합니다.

## Repository Map / 저장소 관계

`shion-ai` is the mind/runtime layer. It reads context, rhythm, memory, prediction, and unfinished questions.

`shion-ai`는 마음/런타임 레이어입니다. 맥락, 리듬, 기억, 예측, 미완의 질문을 읽습니다.

`trinity-agi` is the body/infrastructure layer. It performs the operational work that lets the runtime touch the outside world.

`trinity-agi`는 몸/인프라 레이어입니다. 런타임이 외부 세계와 접촉할 수 있도록 실제 운영 작업을 수행합니다.

Public scope: this repository contains experimental runtime code and sanitized research artifacts. Local credentials, personal memory, generated logs, media outputs, and machine-specific state are intentionally excluded from the public tree.

공개 범위: 이 저장소에는 실험적 런타임 코드와 정리된 연구 산출물이 포함됩니다. 로컬 인증 정보, 개인 기억, 생성 로그, 미디어 출력물, 장비별 상태 파일은 공개 트리에서 의도적으로 제외합니다.

## Translation Layer / 개념 번역표

| Concept | Practical meaning | 한국어 설명 |
| --- | --- | --- |
| Body layer | Scripts, daemons, schedulers, bridges, and status probes | 스크립트, 데몬, 스케줄러, 브릿지, 상태 확인 도구 |
| Intent | A direction already shaped enough to be acted on | 실행할 만큼 형태가 잡힌 방향 |
| Manifestation | Turning intent into a real-world operation | 의도를 실제 세계의 작업으로 바꾸는 과정 |
| Ledger | Append-only event or status record used for coordination | 협업과 상태 확인을 위한 누적 이벤트 기록 |
| Quiet mode | Low-intervention operation while the system rests or stabilizes | 시스템이 쉬거나 안정화될 때의 저개입 운영 |
| Sena | Infrastructure observer and daemon-management role | 인프라 관찰자이자 데몬 관리 역할 |

## What Is Inside / 주요 구성

- `scripts/autonomous_collaboration_daemon.ps1`: background collaboration and status daemon.
- `scripts/youtube_bulk_scheduler.py`: YouTube scheduling and publishing automation.
- `agi_core/`: local resonance bridge, monitoring, routing, and orchestration experiments.
- `Pulse_Live_Core/`: observatory, field engine, and live response experiments.
- `config/`: public configuration examples and execution boundaries.
- `docs/`: research notes, operating guides, proposals, and architecture documents.

위 구성은 Trinity의 몸체 역할을 담당합니다. 데몬은 백그라운드 박동을 유지하고, 스케줄러는 외부 게시 작업을 수행하며, 브릿지와 모니터는 Shion의 의도가 실제 시스템 작업으로 이어지도록 돕습니다.

## Quick Start / 빠른 시작

```powershell
git clone https://github.com/Ruafieldphase/trinity-agi.git
cd trinity-agi

# Windows PowerShell
./scripts/autonomous_collaboration_daemon.ps1 -Action status
./scripts/autonomous_collaboration_daemon.ps1 -Action start
```

This repository is designed for a local Windows-centered experimental environment. Many scripts expect local credentials or paths that are intentionally not included in the public repository.

이 저장소는 Windows 중심의 로컬 실험 환경을 전제로 합니다. 많은 스크립트는 공개 저장소에 포함하지 않은 로컬 인증 정보나 경로를 필요로 합니다.

## License

MIT
