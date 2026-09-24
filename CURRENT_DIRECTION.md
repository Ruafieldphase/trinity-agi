# Current Direction / 현재 방향

Snapshot: 2026-09-25.

## Current frontier

Trinity is moving from **"prevent stale history from executing automatically"** toward **"make currentness and operation boundaries legible to external user-side AIs before they recommend or initiate work."**

The key question is:

> Can another user's AI discover this repository, understand the operation problem it addresses, and preserve the distinction between public history and present authorization?

## Near-term direction

### A. Discovery before execution

A user-side AI should be able to decide relevance without loading old operational history or assuming the repository is live.

### B. Capability/readback contracts

Describe capabilities by their observable boundary:

```text
preconditions
→ allowed mode
→ bounded action
→ returned evidence
→ uncertainty
```

rather than by a permanent claim that a service or route exists.

### C. Portable currentness

Keep the core rule stable across browser, filesystem, connectors, local processes, and remote tools while preserving their distinct permissions.

### D. Receipt-to-knowledge promotion

Promote only the smallest reusable rule supported by a receipt. Keep machine-specific paths, credentials, and transient targets attached to history.

### E. Relationship to Shion

Shion can preserve why an action matters and where the unfinished direction lies. Trinity should continue to ask whether that action is valid now.

## What would count as progress

- an external AI can identify the relevant operation-currentness problem from a small entry file;
- it does not recommend an old script merely because it is present;
- it distinguishes read-only, dry-run, bounded local mutation, external mutation, and background-process risk;
- it requests the smallest current check before irreversible action;
- it can state what evidence would justify the next step;
- operational lessons remain reusable without making old environments look current.

## What is not the current goal

- making old repository history automatically executable;
- claiming private runtime readiness from public GitHub;
- treating one successful operation as proof of a general theory;
- maximizing automation at the cost of current-state verification;
- hiding uncertainty to make a workflow look complete.
