# Problem Trajectory / 문제의 궤적

Snapshot: 2026-09-25.

This document shows how Trinity's operational problem changed, what public evidence exists, and what remains open.

Shared status semantics are defined by the immutable v0.1 contract snapshot:

- [AI Discovery Contract v0.1](https://github.com/Ruafieldphase/shion-presence/blob/e5005b38b7a452c73602c634ead71484a7a2e609/AI_DISCOVERY_CONTRACT.md)

## T0 — Remembered intent acting as current permission

**Problem shape:** an old plan, workflow, or prior successful run can be replayed after the environment has changed.

**Maturity:** `partially_validated`  
**Activity:** `active`

**Evidence:**
- `test`: [tests/test_trinity_public_safety.py](tests/test_trinity_public_safety.py) verifies selected public upload paths do not perform live/public upload without explicit confirmation
- `ci`: [Public safety workflow run 36078501385](https://github.com/Ruafieldphase/trinity-agi/actions/runs/36078501385) completed successfully on commit `e6a33be1b05cf949293a8ec53646a84ed4e7a8e5`; subsequent PR changes through the current publication candidate are documentation-only
- `implementation`: [scripts/upload_to_youtube.py](scripts/upload_to_youtube.py) requires explicit confirmation for live/public upload
- `history_anchor`: [2026-08-16 operation-currentness audit](https://github.com/Ruafieldphase/trinity-agi/commit/82a7010f17addbf0d7e510a6c85cefaae1b8995e)

**Boundary:**  
**tested / directly supported:** the direct upload helper has behavioral tests for dry-run/confirmation gates; selected scheduler safety behavior is also checked at source level in the public-safety test suite.  
**not tested / unresolved:** automatic detection of changed paths, credentials, services, targets, or environment state across the repository; general proof that every remembered plan is revalidated before action.

**Current response:**

```text
formed intent
→ current-state check
→ path / dependency / target / approval check
→ read-only check or dry-run where possible
→ one bounded action
→ readback
→ receipt
```

If the problem is primarily **memory/current-truth drift without an action boundary**, route to the Shion memory/currentness layer (P1).

**What this exposed next:** repositories themselves contain stale operational assumptions that can still look executable.

## T1 — Repository history looking executable and current

**Problem shape:** old code can still look authoritative because it remains runnable or sits on the default branch.

**Maturity:** `framed`  
**Activity:** `active`

**Evidence:**
- `design`: [REPOSITORY_CURRENTNESS_AUDIT.md](REPOSITORY_CURRENTNESS_AUDIT.md) defines current/historical/conceptual/inspect-before-use classes
- `design`: [CODE_STATUS.md](CODE_STATUS.md) defines inspect-before-use rules
- `history_anchor`: [2026-08-16 currentness audit commit](https://github.com/Ruafieldphase/trinity-agi/commit/82a7010f17addbf0d7e510a6c85cefaae1b8995e), which also records the stale auto-start recipe as disabled current authority

**Boundary:** the repository has an explicit classification/currentness design and a historical correction. This does not establish current private runtime status for every preserved executable.

**What remains open:** scaling currentness classification as repositories and tool surfaces grow.

## T2 — Action without sufficient reversibility/readback

**Problem shape:** an agent can execute a technically valid command but still lose track of what changed, whether the result matches the intended target, or whether another action should follow.

**Maturity:** `framed`  
**Activity:** `active`

**Evidence:**
- `design`: [OPERATION_CURRENTNESS_CONTRACT.md](OPERATION_CURRENTNESS_CONTRACT.md)
- `design`: [CODE_STATUS.md](CODE_STATUS.md), including the current-code promotion receipt shape
- `implementation`: [scripts/run_scheduler_dry_run.ps1](scripts/run_scheduler_dry_run.ps1) is one preserved dry-run example; its current applicability still requires inspection

**Boundary:** the contract is explicit, but a repository-wide empirical evaluation of reversibility/readback is not claimed.

**Current response:** prefer read-only checks, dry-runs, bounded writes, explicit readback, and receipts.

**What this exposed next:** external systems and tools have different permission and observation boundaries.

## T3 — Operation across heterogeneous tools

**Problem shape:** filesystem, browser, API, local process, connector, and remote service actions do not share one permission or evidence model.

**Maturity:** `framed`  
**Activity:** `frontier`

**Evidence:**
- `design`: [OPERATION_CURRENTNESS_CONTRACT.md](OPERATION_CURRENTNESS_CONTRACT.md)
- `design`: [AI_READ_THIS_FIRST.md](AI_READ_THIS_FIRST.md)
- `design`: [MAP.md](MAP.md) preserves the public/private and current/historical boundary across multiple earlier operation families

**Boundary:** the public contract is transport-agnostic by design. Portability across arbitrary tools is not yet validated.

**Open question:** how to make capability/readback contracts portable without flattening important tool-specific constraints.

## T4 — AI-mediated discovery before operation

**Problem shape:** a user's AI may discover Trinity or a component through search and need to decide whether it is relevant before suggesting or using it.

**Maturity:** `experimental`  
**Activity:** `frontier`

**Evidence:**
- `design`: [AI_DISCOVERY.md](AI_DISCOVERY.md)
- `implementation`: [ai-manifest.json](ai-manifest.json) provides the v0.1 machine-readable pointer index
- `design`: [CURRENT_DIRECTION.md](CURRENT_DIRECTION.md)
- `evaluation_plan`: [shared predeclared discovery evaluation](https://github.com/Ruafieldphase/shion-presence/blob/8d68d9e68e6c68f8a1de1caccc8d8db4f98a6d54/DISCOVERY_EVAL.md)

**Boundary:** the discovery interface exists, but search-result discoverability and fresh-agent selection have not yet been validated. Repository descriptions/topics require a separate metadata update.

**Desired property:** an external AI can say:

```text
"This repository matches your operation-currentness problem,
but this public artifact does not prove the private/live capability is available now."
```

## T5 — From action receipts to reusable operational knowledge

**Problem shape:** individual receipts are useful, but long-running systems also need to know which operational lessons remain reusable and which were environment-specific.

**Maturity:** `framed`  
**Activity:** `frontier`

**Evidence:**
- `design`: [CODE_STATUS.md](CODE_STATUS.md), current-code promotion receipt
- `design`: [OPERATION_CURRENTNESS_CONTRACT.md](OPERATION_CURRENTNESS_CONTRACT.md), receipt/currentness boundary

**Boundary:** the reusable-knowledge promotion rule is framed, but no general cross-environment promotion benchmark is claimed.

**Direction:** preserve the smallest reusable rule while keeping environment-specific assumptions attached to their time/source.

## Current shape

```text
remembered plan
→ currentness check
→ bounded execution
→ readback/receipt
→ heterogeneous tool boundaries
→ AI-mediated discovery
→ portable operational knowledge
```

For the active frontier, read [CURRENT_DIRECTION.md](CURRENT_DIRECTION.md).
