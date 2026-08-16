# Trinity Repository Currentness Audit

Status: public repository audit, 2026-08-16.

This document classifies `trinity-agi` by operational status. It does **not** make the public GitHub tree an authority for a private live runtime.

## Core rule

> **A remembered operation is not a present permission. An executable file is not proof that its runtime still exists.**

For any operation that can change files, processes, remote services, schedules, published content, credentials, or external state, current authorized readback must outrank old repository instructions.

## Status classes

### A. Current public operation-boundary documents

Preferred current entry documents:

- `README.md`
- `OPERATION_CURRENTNESS_CONTRACT.md`
- `REPOSITORY_CURRENTNESS_AUDIT.md`
- `CODE_STATUS.md`
- `AI_READ_THIS_FIRST.md`
- `MAP.md`
- `.agents/workflows/auto_start.md`

These define how to read and approach the repository. They do not certify that any private process or endpoint is currently running.

### B. Public code snapshot — verify before use

The following path families contain scripts, prototypes, helpers, experiments, or prior operational implementations:

- `scripts/`
- `agi_core/`
- `Pulse_Live_Core/`
- `lumen_factory/`
- configuration and workflow helpers

Status: **public code snapshot, not live-operation authority**.

Machine-specific paths, localhost endpoints, daemon names, credentials, channel IDs, remote APIs, model names, and scheduler assumptions may be historical.

### C. Historical or conceptual material

Examples include:

- `PHASE_TRANSITION_MAP.md`
- `LIVE_WORK_ARCHIVE.md`
- `Manifest_Future_Products/`
- older reports, applications, product concepts, and architecture narratives
- dated or experiment-specific documents

These are useful as design history, prior proposals, or retrospective evidence. They do not inherit present operational status merely by remaining in `main`.

### D. Private/current operational environment

The live operational environment, if available to an authorized agent, is outside the authority of this public repository.

Before acting, verify the relevant current facts such as:

- working directory and actual file path
- process/service status
- remote endpoint availability
- credentials and permissions
- approval state
- dry-run behavior
- current target/account/channel
- returned result and receipt

If current authorized evidence conflicts with an old GitHub instruction, the current evidence wins for the changed claim.

## Drift found in this audit

The 2026-08 audit found concrete stale-operation risks:

1. `.agents/workflows/auto_start.md` instructed an agent to restore `Auto-Allow`, initialize sync, and start a background daemon from a fixed `C:/workspace/agi` path.
2. Multiple scripts still contain machine-specific `C:/workspace/agi` assumptions.
3. `MAP.md` described several older components as representative operating surfaces without making their currentness status prominent enough.
4. `AI_READ_THIS_FIRST.md` prioritized conceptual grounding before a repository/currentness check.
5. Some publishing, sync, Slack, Moltbook, media, and daemon scripts can look runnable even though current credentials, endpoints, targets, or operational need have not been established.

These are repository-history facts, not proof that the corresponding components are wrong or dead.

## Promotion rule

A public script becomes a current operational dependency only after a current authorized check supports the specific dependency claim.

A minimal promotion receipt should include:

```yaml
source: current file | process readback | tool return | remote status
observed_at: timestamp
observer: human | AI | tool | system
operation_candidate: exact bounded operation
current_preconditions: what was verified
approval: required | granted | not_required
result: dry_run | executed | blocked | no_op
uncertainty: unresolved conditions
changed_claim: only the claim updated by this receipt
```

## Safety of historical material

Old files should usually remain when they preserve useful development history. Do not rewrite timestamps merely to make the repository look current.

Instead:

```text
old code + status visible = useful history
old code + current-looking execution instruction = stale-authority risk
```

## Result of this pass

Read the repository in this order:

```text
README
→ OPERATION_CURRENTNESS_CONTRACT
→ REPOSITORY_CURRENTNESS_AUDIT
→ CODE_STATUS
→ AI_READ_THIS_FIRST / MAP as needed
→ specific script only after its current preconditions are checked
```

Trinity remains a public operational-history and code surface. Present execution authority stays with the current authorized environment and explicit action boundary.
