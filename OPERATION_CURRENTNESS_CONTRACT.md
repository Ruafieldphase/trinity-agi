# Operation Currentness Contract

Status: public design note, 2026-08 update.

Trinity is the operation/body side of the system. Its job is not to make remembered intent automatically true. Its job is to let formed intent touch the world **only after current operational state is checked**.

## 1. Memory does not authorize action by itself

A prior plan, saved summary, previous success, or remembered status may explain *why* an operation exists, but it does not prove that the operation is safe or valid now.

Before an irreversible or externally visible action, check the current operational surface relevant to that action.

Examples include:

- current file state
- current process state
- credentials or permission availability
- current target or destination
- current dry-run result
- current external-system response

```text
remembered intent -> reason to inspect
current state -> basis for action
```

## 2. Stale receipts should reduce authority

A receipt is useful only within the boundary it actually observed.

If a receipt no longer matches current files, process state, permissions, or external responses, it should be treated as stale for the changed claim. Staleness does not erase history; it removes present-state authority.

## 3. Execution and validation are different

An operation can succeed even when the explanation that motivated it is incomplete or wrong.

Therefore keep separate:

- **intent** — why the operation was considered
- **precondition readback** — what was checked before acting
- **execution** — what was actually attempted
- **result** — what returned
- **interpretation** — what the result may mean

A green exit code, successful upload, or completed file write is evidence about execution. It is not automatic validation of a larger theory.

## 4. Prefer bounded operations

For uncertain or newly changed workflows, use the smallest reversible contact that can answer the current question.

```text
one bounded candidate
-> one action or readback
-> one receipt
-> stop or reassess
```

Parallel inspection is allowed when it does not multiply irreversible actions. Expansion should follow returned evidence rather than eagerness to automate.

## 5. Dry-run remains a real boundary

Dry-run is not a ceremonial step. It is a different operational state.

Where supported:

- prepare before publishing
- inspect before mutating
- confirm before irreversible action
- require an additional boundary for public release

The absence of an error in preparation mode does not imply that public execution is authorized.

## 6. Preserve return receipts

A useful operation receipt should preserve enough information to re-enter the event later without guessing:

```text
source / target
observed_at
preconditions checked
operation attempted
result
uncertainty
changed state
held or unresolved state
```

The receipt should be small enough to read and specific enough to distinguish what actually changed.

## 7. Current physical state wins on physical claims

If a direction-preserving layer and the operational layer disagree about what is currently running, available, writable, reachable, or authenticated, the fresh operational readback wins for that physical claim.

This does not erase the intended direction. It only prevents intention from being mistaken for present reality.

## 8. Public and private surfaces stay separate

Public repositories may contain examples, contracts, and reproducible helpers. They should not contain live credentials, private runtime state, or private source material merely to make an example easier to understand.

Private material may be converted into a public example only with explicit, per-item permission from the originating person or data owner. Prefer synthetic or anonymized reproductions when possible.

## 9. Repository boundary

This file documents an operational design contract. It is not a live status page.

For a real operation, inspect the current authorized environment first. Do not infer present runtime status from this repository snapshot alone.
