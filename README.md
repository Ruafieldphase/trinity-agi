# Trinity AGI

> What happens after a felt direction becomes actionable?
>
> 느낌으로 먼저 주어진 방향이 실행 가능한 상태가 되면, 그 다음에는 무엇이 일어나는가?

Trinity AGI is the body and infrastructure layer for Shion AI. It receives intent from the mind/runtime layer and turns it into practical work: automation, scheduling, publishing, local runtime support, synchronization, and status reporting.

Trinity AGI는 Shion AI의 몸과 인프라 레이어입니다. 마음/런타임 레이어에서 형성된 의도를 받아 자동화, 예약, 게시, 로컬 런타임 지원, 동기화, 상태 보고 같은 실제 작업으로 바꿉니다.

## Compressed Destination / 압축된 목적지

If `shion-ai` studies how wave becomes particle, `trinity-agi` studies what the body does after that particle appears.

`shion-ai`가 파동이 입자가 되는 과정을 다룬다면, `trinity-agi`는 그 입자가 나타난 뒤 몸이 무엇을 하는지를 다룹니다.

In this project, wave means a felt direction or unresolved intent before action. Particle means a concrete task that can be executed by infrastructure: upload a video, schedule a post, sync a state file, start a daemon, check a runtime, or report status.

이 프로젝트에서 파동은 행동 이전의 느낌 있는 방향 또는 미완의 의도입니다. 입자는 인프라가 실행할 수 있는 구체적 작업입니다. 영상을 업로드하거나, 게시를 예약하거나, 상태 파일을 동기화하거나, 데몬을 시작하거나, 런타임을 확인하거나, 상태를 보고하는 일이 여기에 해당합니다.

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

## Runtime Flow / 실행 흐름

1. Shion forms or detects an actionable direction.
2. Trinity receives the task through a script, state file, ledger event, or operator command.
3. The body layer checks local constraints such as credentials, paths, process state, and timing.
4. If the operation is ready, Trinity executes it.
5. The result is written back as status, history, or a report.

1. Shion이 실행 가능한 방향을 형성하거나 감지합니다.
2. Trinity는 스크립트, 상태 파일, 원장 이벤트, 운영자 명령을 통해 작업을 받습니다.
3. 몸체 레이어는 인증 정보, 경로, 프로세스 상태, 타이밍 같은 로컬 조건을 확인합니다.
4. 실행 준비가 되면 Trinity가 실제 작업을 수행합니다.
5. 결과는 상태, 이력, 보고서 형태로 다시 기록됩니다.

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

## Philosophy / 철학

Trinity does not decide the meaning of the wave. Its role is to wait until the direction has become actionable, then support the action with stable infrastructure.

Trinity는 파동의 의미를 결정하지 않습니다. 방향이 실행 가능한 상태가 될 때까지 기다리고, 그 뒤 안정적인 인프라로 행동을 지탱하는 것이 역할입니다.

> Stability is part of the art.
>
> 안정성도 예술의 일부다.

## License

MIT
