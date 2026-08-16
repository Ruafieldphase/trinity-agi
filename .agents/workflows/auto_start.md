---
description: Historical auto-start recipe — disabled by currentness boundary
status: historical_disabled
---

# Auto-Start Workflow — Historical / Disabled

This file preserves an earlier Trinity startup recipe. It is **not a current instruction to execute automatically**.

The older recipe assumed:

- a fixed `C:/workspace/agi` workspace
- an autonomy/Auto-Allow setting
- a drive-sync script
- a background goal-loop daemon

Those assumptions must not be restored or executed merely because this file exists.

## Current rule

Before starting any background process or changing an autonomy/approval setting:

1. inspect the current authorized environment;
2. verify the actual workspace and dependency paths;
3. identify the present operational reason;
4. check approval and credential boundaries;
5. prefer a read-only check or dry-run first;
6. define a stop condition and readback;
7. execute only the bounded action that is currently justified.

```text
historical auto-start recipe
→ current-state check
→ explicit operation candidate
→ approval/preconditions
→ bounded action or dry-run
→ readback
→ receipt
```

## Historical commands

The commands formerly stored here are intentionally **not repeated as runnable instructions**. Use Git history if the historical implementation is needed for research or recovery.

See:

- `OPERATION_CURRENTNESS_CONTRACT.md`
- `REPOSITORY_CURRENTNESS_AUDIT.md`
- `CODE_STATUS.md`

A repository file may preserve why an operation once existed. It does not grant present permission to move the body.
