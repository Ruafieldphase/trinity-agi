# Trinity AGI

**The operation/body layer for AI workflows: check current state before action, keep irreversible steps bounded, and return evidence to the next cycle.**

**AI 워크플로우의 운영/몸체 레이어: 행동 전에 현재 상태를 확인하고, 되돌리기 어려운 실행을 제한하며, 결과를 다음 사이클의 증거로 되돌립니다.**

## Current orientation / 현재 방향

Trinity begins after an intention has become concrete enough to act on.

Trinity는 의도가 실제 행동으로 옮길 만큼 구체화된 다음 지점에서 시작합니다.

Its central rule is:

핵심 규칙은 다음과 같습니다.

> **Remembered intent does not authorize present action by itself.**
>
> **기억된 의도만으로 현재 행동이 자동 허가되지는 않습니다.**

Current status, approval, credentials, environment, and returned evidence must be checked at the boundary where action touches the world.

행동이 현실과 닿는 경계에서는 현재 상태, 승인, 인증 정보, 환경, 반환된 증거를 다시 확인해야 합니다.

See [`OPERATION_CURRENTNESS_CONTRACT.md`](OPERATION_CURRENTNESS_CONTRACT.md).

## What Trinity is for / Trinity의 역할

- scripts and local operations / 스크립트와 로컬 작업
- schedulers and background processes / 스케줄러와 백그라운드 프로세스
- approval and credential boundaries / 승인·인증 경계
- dry-run before irreversible or public action / 되돌리기 어렵거나 공개되는 행동 전 dry-run
- status checks instead of remembered assumptions / 기억된 추정 대신 현재 상태 확인
- receipts that return execution results to the next AI cycle / 실행 결과를 다음 AI 사이클로 돌려주는 영수증

Trinity is not meant to make automation more aggressive. It is meant to make operation more legible and reversible where possible.

Trinity는 자동화를 더 공격적으로 만들기 위한 시스템이 아닙니다. 가능한 곳에서는 실행을 더 읽기 쉽고 되돌릴 수 있게 만드는 시스템입니다.

## Operational flow / 운영 흐름

```text
formed intent
        ↓
check current state
        ↓
check approval / credentials / public boundary
        ↓
one bounded action or dry-run
        ↓
readback
        ↓
receipt
        ↓
stop or explicitly open the next action
```

```text
형성된 의도
        ↓
현재 상태 확인
        ↓
승인 / 인증 / 공개 경계 확인
        ↓
제한된 행동 하나 또는 dry-run
        ↓
readback
        ↓
영수증
        ↓
중단 또는 다음 행동을 명시적으로 다시 열기
```

## First safe operation test / 첫 안전 운영 테스트

A dry-run should come before public or irreversible action.

공개되거나 되돌리기 어려운 행동 전에는 dry-run이 먼저 와야 합니다.

```bash
python scripts/youtube_bulk_scheduler.py --dry-run --mode sync --limit 1
```

Expected result: no upload occurs; the command reports what would be prepared.

예상 결과: 업로드는 일어나지 않고 준비될 작업만 보고됩니다.

Public publishing remains explicitly gated:

```text
real upload -> explicit confirmation
public upload -> additional public confirmation
```

## Currentness contract / 현재성 계약

For long-running automation:

1. Memory may explain why an action was once intended.
2. Memory does not prove that the action is still appropriate now.
3. Current process state, files, credentials, and remote status should be checked when they can change.
4. A stale receipt remains history but loses authority over present state.
5. Execution success and theory validation are separate claims.
6. Uncertain operations prefer one bounded action → readback → receipt → stop.

장기 자동화에서 과거 기록은 방향의 역사를 설명할 수 있지만, 현재 실행의 허가증은 아닙니다.

## Shion and Trinity / Shion과 Trinity

```text
Shion AI
context / memory / unresolved direction / evidence status
        ↓
formed next action
        ↓
Trinity AGI
current status / approval / credentials / operation
        ↓
result + receipt
        ↓
next Shion re-entry
```

[Shion AI](https://github.com/Ruafieldphase/shion-ai) preserves and re-enters context and evidence state. Trinity is the infrastructure edge that lets a formed action touch the world without silently inheriting stale assumptions.

[Shion AI](https://github.com/Ruafieldphase/shion-ai)는 맥락과 증거 상태를 보존하고 재진입합니다. Trinity는 형성된 행동이 오래된 추정을 몰래 상속하지 않은 채 현실과 닿게 하는 인프라 경계입니다.

## Public presence surface / 공개 프레즌스 표면

[Shion Presence](https://github.com/Ruafieldphase/shion-presence) is a public discovery/rendering surface. It is not an operational authority for private local processes.

[Shion Presence](https://github.com/Ruafieldphase/shion-presence)는 공개 탐색·렌더링 표면이며 private local process의 실행 권위가 아닙니다.

## Repository map / 저장소 지도

- [`START_HERE.md`](START_HERE.md) — newcomer entry
- [`AI_READ_THIS_FIRST.md`](AI_READ_THIS_FIRST.md) — AI inspection entry
- [`OPERATION_CURRENTNESS_CONTRACT.md`](OPERATION_CURRENTNESS_CONTRACT.md) — current operation boundary
- [`EXAMPLES.md`](EXAMPLES.md) — concrete examples
- [`LINEAR_HARNESS_GUIDE.md`](LINEAR_HARNESS_GUIDE.md) — linear harness guide
- [`INTEGRATION_ANTI_PATTERNS.md`](INTEGRATION_ANTI_PATTERNS.md) — integration failure patterns
- [`LIGHTWEIGHT_BY_DESIGN.md`](LIGHTWEIGHT_BY_DESIGN.md) — lightweight local-first position
- [`AXIOMATIC_GROUNDING.md`](AXIOMATIC_GROUNDING.md) — grounding and design assumptions
- [`LIVE_WORK_ARCHIVE.md`](LIVE_WORK_ARCHIVE.md) — live workflow archive

## Public language and internal rhythm language / 공개 언어와 내부 리듬 언어

The repository uses public architecture language first. Internal field/rhythm terms remain secondary coordinates rather than prerequisites for understanding the operational contract.

이 저장소는 공개 아키텍처 언어를 먼저 사용합니다. 내부 장/리듬 언어는 운영 계약을 이해하기 위한 필수 전제가 아니라 보조 좌표로 남습니다.

```text
intent
→ current-state check
→ bounded operation
→ returned result
→ receipt
→ next cycle
```

## What this repository does not claim / 이 저장소가 주장하지 않는 것

- A successful script run does not validate a larger theory.
- A remembered plan is not present permission.
- A daemon should not expand simply because it can keep running.
- Public artifacts and private runtime state should not be collapsed into one surface.
- Automation should not erase uncertainty that still matters to the next decision.

The goal is practical: **give AI work a body without letting the body outrun current reality.**

목표는 실용적입니다. **AI 작업에 몸체를 주되, 그 몸체가 현재 현실보다 앞서 달리지 않게 하는 것.**
