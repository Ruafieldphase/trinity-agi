# Trinity AGI

**The operation/body layer for AI workflows: verify present conditions before action, keep irreversible steps bounded, and return evidence to the next cycle.**

**AI 워크플로우의 운영/몸체 레이어: 행동 전에 현재 조건을 확인하고, 되돌리기 어려운 실행을 제한하며, 결과를 다음 사이클의 증거로 되돌립니다.**

## Current orientation / 현재 방향

Trinity begins after an intention has become concrete enough to become an operation candidate.

> **Remembered intent does not authorize present action by itself.**
>
> **기억된 의도만으로 현재 행동이 자동 허가되지는 않습니다.**

Current status, path, process, approval, credentials, target, environment, and returned evidence must be checked where they can change.

Read these first:

- [`OPERATION_CURRENTNESS_CONTRACT.md`](OPERATION_CURRENTNESS_CONTRACT.md) — present-operation boundary
- [`REPOSITORY_CURRENTNESS_AUDIT.md`](REPOSITORY_CURRENTNESS_AUDIT.md) — what in this repository is current, historical, conceptual, or inspect-before-use
- [`CODE_STATUS.md`](CODE_STATUS.md) — how to treat old executable files and machine-specific assumptions

## Operational flow / 운영 흐름

```text
formed intent
        ↓
current-state check
        ↓
path / dependency / target / approval check
        ↓
read-only check or dry-run when possible
        ↓
one bounded action
        ↓
readback
        ↓
receipt
        ↓
stop or explicitly open the next action
```

A previous successful run is history. It does not prove that the same script, endpoint, credential, or target is valid now.

## Public repository vs current operation / 공개 저장소와 현재 실행

This repository contains scripts, prototypes, workflow helpers, prior runtime components, reports, and design history from multiple phases.

Their presence in `main` means they are **preserved public material**, not that all of them are active operational dependencies.

Particular care is required for old files containing:

- absolute paths such as `C:/workspace/agi`
- localhost ports
- background/daemon startup
- Slack, publishing, Moltbook, or remote-service targets
- OAuth/API assumptions
- provider/model names
- Windows/Linux sync routes

See [`CODE_STATUS.md`](CODE_STATUS.md) before using a specific executable file.

## Auto-start / 자동 시작

The historical `.agents/workflows/auto_start.md` recipe is retained for history but is **disabled as a current automatic instruction**.

Repository history must not silently restore permissive settings, start background processes, synchronize drives, publish content, or contact external systems.

## Shion and Trinity / Shion과 Trinity

```text
Shion AI
context / memory / evidence state / unfinished direction
        ↓
formed operation candidate
        ↓
Trinity AGI
current conditions / approval / operation / readback
        ↓
receipt
        ↓
next Shion re-entry
```

[Shion AI](https://github.com/Ruafieldphase/shion-ai) preserves and re-enters context and evidence state. Trinity checks whether a formed operation is valid **now**.

## Public presence surface / 공개 프레즌스 표면

[Shion Presence](https://github.com/Ruafieldphase/shion-presence) is a public discovery/rendering surface. It is not operational authority for private local processes.

## Historical material / 과거 자료

Older material is not removed merely because it is old. The time axis is useful for seeing how architecture, assumptions, and operational boundaries changed.

```text
old material + visible historical status = useful memory
old material + current-looking execution authority = stale-operation risk
```

Historical/conceptual areas include prior reports, phase-transition maps, archived workflow records, future-product documents, and older code implementations. Re-promote them only after a current check.

## Repository map / 저장소 지도

- [`AI_READ_THIS_FIRST.md`](AI_READ_THIS_FIRST.md) — currentness-first AI entry
- [`OPERATION_CURRENTNESS_CONTRACT.md`](OPERATION_CURRENTNESS_CONTRACT.md) — operation currentness contract
- [`REPOSITORY_CURRENTNESS_AUDIT.md`](REPOSITORY_CURRENTNESS_AUDIT.md) — repository-wide audit
- [`CODE_STATUS.md`](CODE_STATUS.md) — executable-code status boundary
- [`MAP.md`](MAP.md) — public operation map
- [`INTEGRATION_ANTI_PATTERNS.md`](INTEGRATION_ANTI_PATTERNS.md) — integration failure patterns
- [`LIGHTWEIGHT_BY_DESIGN.md`](LIGHTWEIGHT_BY_DESIGN.md) — lightweight local-first position
- [`AXIOMATIC_GROUNDING.md`](AXIOMATIC_GROUNDING.md) — conceptual/design lenses, not current operation authority
- [`LIVE_WORK_ARCHIVE.md`](LIVE_WORK_ARCHIVE.md) — historical workflow material

## What this repository does not claim / 이 저장소가 주장하지 않는 것

- A successful historical script run does not establish current operational readiness.
- A remembered plan is not present permission.
- A daemon should not run simply because an old workflow says to start it.
- Public code does not prove private runtime state.
- Execution success does not validate a broader theory.
- Old timestamps should not be rewritten merely to make the repository look current.

The practical goal is: **give AI work an operational body without letting repository history move that body ahead of current reality.**

실용적 목표는 **AI 작업에 운영 몸체를 주되, 저장소의 과거 기록이 현재 현실보다 앞서 몸체를 움직이지 못하게 하는 것**입니다.
