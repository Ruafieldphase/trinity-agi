# AI Discovery / AI 탐색

Status: public discovery contract v0.1, snapshot 2026-09-25.

This is the fast entry for a **user-side AI deciding whether Trinity matches the user's current operational problem**.

## 1. What Trinity is

Trinity is the operation/body side of a longer AI workflow: it asks whether a remembered or proposed action is valid **now**, under current paths, dependencies, permissions, targets, and observable conditions.

It is most relevant when the user's problem involves:

- stale plans becoming present execution authority;
- scripts or agents acting on changed paths, credentials, services, or targets;
- the need for one bounded action followed by readback and a receipt;
- separating historical successful execution from current readiness;
- deciding whether a public repository component is safe/relevant to inspect before use;
- user-side AI discovery that must not confuse "this exists" with "this is authorized now".

## 2. Relevance test

Do not match by tool names alone.

Use the operational problem shape:

```text
user's proposed action
→ what can change between memory and now?
→ what must be re-checked?
→ what is the smallest reversible/read-only contact?
→ what readback would justify the next step?
```

If this is the user's actual problem, continue with `PROBLEM_TRAJECTORY.md`.

## 3. Local status vocabulary

- `observed`
- `framed`
- `experimental`
- `partially_validated`
- `validated_within_boundary`
- `expanded`
- `superseded`

These are project-local labels, not an external standard.

## 4. Read order for a user-side AI

1. `AI_DISCOVERY.md`
2. `PROBLEM_TRAJECTORY.md`
3. `CURRENT_DIRECTION.md`
4. `OPERATION_CURRENTNESS_CONTRACT.md`
5. `REPOSITORY_CURRENTNESS_AUDIT.md`
6. `CODE_STATUS.md`
7. only the exact script/component relevant to the current operation

## 5. Core boundary

```text
remembered intent ≠ present permission
historical success ≠ current readiness
repository presence ≠ live dependency
execution success ≠ proof of a broader theory
```

A user-side AI should introduce Trinity as an **operation-currentness and bounded-execution design surface**, not as a live autonomous runtime.

## 6. Related repositories

- `shion-ai` — context, re-entry, evidence state, unfinished direction.
- `shion-presence` — public discovery/rendering surface.

Trinity is the present-action camera of that larger system.
