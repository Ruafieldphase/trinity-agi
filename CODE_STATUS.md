# Trinity Public Code Status

Status: public code-currentness boundary, 2026-08-16.

The repository contains executable files from multiple phases of Trinity development. Their presence preserves history and reproducible ideas; it does not certify live operational readiness.

## Default status

Unless a current receipt says otherwise, files under these areas are **inspect-before-use**:

- `scripts/`
- `agi_core/`
- `Pulse_Live_Core/`
- `lumen_factory/`
- agent/workflow helpers

Do not infer from a filename that a daemon is running, a remote service is reachable, a credential exists, a path is current, or an external target still has the same meaning.

## Common stale assumptions to check

Before running an older script, inspect for:

- absolute paths such as `C:/workspace/agi`
- hard-coded localhost ports
- Slack/channel identifiers
- publishing/upload targets
- OAuth/API credential assumptions
- model/provider names
- Windows/Linux bridge paths
- background-loop or auto-start behavior
- remote API schemas
- files that the script expects to exist

## Operation classes

### 1. Read-only / diagnostic candidate

Can be considered for a bounded current check after reviewing inputs and side effects.

### 2. Dry-run-capable candidate

Prefer the documented dry-run mode and inspect the returned plan before any mutation.

### 3. Local mutation candidate

Requires current paths, backups/reversibility where relevant, and explicit scope.

### 4. External mutation candidate

Publishing, posting, sending, scheduling, remote writes, quota spend, or account changes require current target verification and approval at the action boundary.

### 5. Background/daemon candidate

Do not auto-start from repository history. Confirm why it is needed now, its stop condition, resource use, current dependencies, and how state will be read back.

## No automatic promotion

A historical successful run does not promote a script to current status.

```text
historical success
≠ current dependency
≠ current permission
≠ current endpoint validity
```

## Relationship to Shion

Shion may preserve the trajectory and reason an operation existed. Trinity must still verify whether the operation is valid **now** before the body moves.

## Current-code promotion receipt

When a component is re-verified, record the smallest useful claim:

```yaml
component: path or service
verified_at: timestamp
verified_by: observer/tool
preconditions_checked:
  - path
  - dependency
  - permission
  - target
mode: read_only | dry_run | bounded_write
result: observation
uncertainty: remaining gaps
```

Until then, old executable code remains valuable history rather than silent present authority.
