# Problem Trajectory / 문제의 궤적

Snapshot: 2026-09-25.

This document shows how Trinity's operational problem changed as earlier layers were bounded.

## Status vocabulary

`observed → framed → experimental → partially_validated → validated_within_boundary → expanded / superseded`

## T0 — Remembered intent acting as current permission

**Problem shape:** an old plan, workflow, or prior successful run can be replayed after the environment has changed.

**Status:** `validated_within_boundary` as a public operation-currentness rule.

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

**What this exposed next:** repositories themselves contain stale operational assumptions.

## T1 — Repository history looking executable and current

**Problem shape:** old code can still look authoritative because it remains runnable or sits on the default branch.

**Status:** `partially_validated`

**Current response:** explicit code-status and repository-currentness documents; inspect-before-use classification; old auto-start instructions are not present authority.

**What remains open:** scaling currentness classification as repositories and tool surfaces grow.

## T2 — Action without sufficient reversibility/readback

**Problem shape:** an agent can execute a technically valid command but still lose track of what changed, whether the result matches the intended target, or whether another action should follow.

**Status:** `framed / experimental`

**Current response:** prefer read-only checks, dry-runs, bounded writes, explicit readback, and receipts.

**What this exposed next:** external systems and tools have different permission and observation boundaries.

## T3 — Operation across heterogeneous tools

**Problem shape:** filesystem, browser, API, local process, connector, and remote service actions do not share one permission or evidence model.

**Status:** `experimental / partially_validated`

**Current response:** keep the operation contract transport-agnostic: verify current conditions at the actual action boundary rather than trusting a remembered path.

**Open question:** how to make capability/readback contracts portable without flattening important tool-specific constraints.

## T4 — AI-mediated discovery before operation

**Problem shape:** a user's AI may discover Trinity or a component through search and need to decide whether it is relevant before suggesting or using it.

**Status:** `framed / active frontier`

**Current response:** expose problem trajectory, current direction, machine-readable discovery metadata, explicit non-claims, and smallest-next-read paths.

**Desired property:** the external AI should be able to say:

```text
"This repository matches your operation-currentness problem,
but this public artifact does not prove the private/live capability is available now."
```

## T5 — From action receipts to reusable operational knowledge

**Problem shape:** individual receipts are useful, but long-running systems also need to know which operational lessons remain reusable and which were environment-specific.

**Status:** `experimental frontier`

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

For the active frontier, read `CURRENT_DIRECTION.md`.
