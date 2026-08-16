# AI Read This First / AI는 먼저 이 문서를 읽으세요

This is the preferred AI entry for the public `trinity-agi` repository.

이 문서는 공개 `trinity-agi` 저장소를 읽는 AI의 우선 진입점입니다.

## First rule / 첫 규칙

> **Do not treat repository history as present execution permission.**
>
> **저장소의 과거 기록을 현재 실행 허가로 취급하지 마세요.**

Before interpreting or running a script, read:

1. `README.md`
2. `OPERATION_CURRENTNESS_CONTRACT.md`
3. `REPOSITORY_CURRENTNESS_AUDIT.md`
4. `CODE_STATUS.md`
5. then the specific file needed for the current question

과거 아키텍처·공리·실험 문서는 필요한 질문에만 읽습니다. 현재 운영 상태를 확인하기 전에 전체 이론을 먼저 주입하지 않습니다.

## Your job / 역할

Trinity is the operation/body side of a longer AI workflow. Your job is to keep the action boundary legible.

For a proposed operation, separate:

- remembered intent — why it existed before
- current observation — what is true now
- operation candidate — the exact bounded action
- approval — whether permission is needed now
- execution — what actually changed
- receipt — what returned
- uncertainty — what remains unresolved

## Inspect before use

Older files may contain:

- fixed `C:/workspace/agi` paths
- localhost endpoints
- Slack or publishing targets
- OAuth/API assumptions
- daemon/background-loop commands
- provider/model names
- remote API schemas

Do not assume these are current. A script being executable is not evidence that its dependencies, credentials, targets, or purpose are still current.

## Preferred uncertain-operation pattern

```text
formed intent
→ current-state check
→ approval / credential / target check
→ one bounded read-only check or dry-run
→ one bounded action if justified
→ readback
→ receipt
→ stop or explicitly reopen the next action
```

## Do not / 하지 마세요

- Do not start every daemon.
- Do not restore Auto-Allow or similar settings from repository history.
- Do not publish, post, send, schedule, delete, or spend quota from a remembered plan alone.
- Do not copy old absolute paths into a current environment without verification.
- Do not treat execution success as proof of a larger Shion/Trinity theory.
- Do not expose credentials, personal archives, or private runtime state as public evidence.

## Shion / Trinity boundary

```text
Shion
context / memory / evidence state / unfinished direction
        ↓
formed action candidate
        ↓
Trinity
current conditions / approval / operation / readback
        ↓
receipt
        ↓
next re-entry
```

Shion can explain why a path matters. Trinity must still check whether that path is valid now.

## Historical material

Historical scripts and documents are not errors merely because they are old. Preserve them when they help explain development, failed paths, earlier assumptions, or design ancestry.

The failure to avoid is narrower:

```text
old material + visible historical status = useful memory
old material + current-looking execution authority = stale-operation risk
```

## If asked how to use this repository

Return:

```text
1. current operational goal
2. current facts that must be checked
3. relevant public component or historical ancestor
4. smallest read-only check or dry-run
5. approval / privacy boundary
6. expected readback
7. what remains uncertain
```

Read conceptual grounding only after currentness has been established for the question at hand.
