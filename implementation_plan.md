# Implementation Plan - FSD Operational Enhancement

## Goal
Move from simulation-like FSD to practical autonomous execution on Windows by tightly coupling intent -> action -> visual verification -> safety interlock.

## Current Baseline
- `scripts/execute_proposal.py` already handles GUI actions via `RPACore`.
- `memory/vision_events.jsonl` provides vision summaries for verification.
- `outputs/aura_pixel_state.json` acts as the primary safety gate.
- `agi_core/rhythm_boundaries.py` provides phase context for execution.

## Plan

### 1) Intent -> Muscle (Proposal Execution)
- Normalize proposal schema for GUI actions (`type=gui_action`, `params.action=click|type|drag|hotkey`).
- Ensure `scripts/thought_to_action.py` emits GUI actions when confidence is high.
- Expand `scripts/execute_proposal.py` mapping to core GUI actions and keep non-GUI actions in safe scripts.

### 2) Visual Self-Verification Loop
- Use a post-action cursor so only new vision events are checked.
- Match both `summary` and `ui_elements` in `vision_events.jsonl`.
- If vision logs are missing, record "verification skipped" instead of hard-failing execution.

### 3) Safety & Ethics Interlock
- Gate physical actions with:
  - `outputs/aura_pixel_state.json`
  - `outputs/safety/red_line_monitor_latest.json`
  - `outputs/child_data_protector_latest.json`
  - `outputs/safety/rest_gate_latest.json`
- Block on red/danger status, detected child data, or active rest gate.

### 4) Feedback & Recovery
- Write action results to the resonance ledger for learning.
- If verification fails, mark result with context and allow re-plan.

## Verification Plan
1. Trigger a `gui_action` proposal and confirm a real click/type occurs.
2. Confirm `memory/vision_events.jsonl` appends a new event after action.
3. Force Aura Pixel to RED and verify the action is blocked.
4. Activate rest gate and verify physical actions are deferred.

---

# Implementation Plan - FSD Question Boundary (Slack)

## Goal
Switch FSD from “always decide” to “ask on boundary” using Slack-based human-in-the-loop.

## Plan
1. Add `ActionType.QUESTION` + Z2_IDLE handling in `services/fsd_controller.py`.
2. Implement `services/slack_gateway.py` for interactive questions and async responses.
3. Add `verify_slack_question.py` to validate end-to-end flow.

## Phase 2: Refinements
- Treat questions as state transitions with boundary memory (dedup by boundary).
- Interpret timeouts as intentional non-intervention and keep Z2_IDLE as safe default.
- Trigger questions only on meaning branches (irreversible change / value judgment).
- Cap questions per episode (max 2).

## Phase 3: Stabilization
- Signature-based dedup (goal/app/phase).
- Two-strike timeout escape policy to prevent infinite waiting.
- Dual-gate trigger: code hard-gate for risky keywords + LLM meaning-branch decision.
- Update `verify_slack_question.py` with Phase 3 cases (dedup/timeout/hard-gate).

## Phase 3.1: Resource Stabilization
- Forgetting policy: cap boundary memory (FIFO, max 50).
- State freeze: skip redundant captures/reporting during sustained Z2_IDLE.
- Verify mode: suppress heavy syncs during tests (`AGI_VERIFY_MODE=1`).
- Extend verification with FIFO eviction test case.

## Phase 3.2: Maturation Observation
- Observe 5-episode flow: Dedup, Suppression, Timeout, Idle/Forgetting, Quality.
- Add `observe_fsd_maturation.py` to exercise the observation cycle without new policy changes.
- Record outcomes in walkthrough and handoff notes.

## Verification Plan
1. Run `python verify_slack_question.py`.
2. Confirm duplicate boundary detection and question limit behavior.
3. Confirm timeout is treated as intentional non-intervention (Z2_IDLE) with 2-strike escape.
4. Confirm hard-gate status is surfaced in the prompt for risky vs. non-risky goals.
5. Confirm FIFO boundary eviction (cap behavior) in verification harness.
6. Run `python observe_fsd_maturation.py` to observe the 5-episode maturation flow.

---

# Implementation Plan - RAG Upgrade (Semantic Memory)

## Goal
Upgrade RAG from lexical matching to semantic vector recall using LangChain + ChromaDB while preserving existing long-term memory flows.

## Current Baseline
- `fdo_agi_repo/copilot/hippocampus.py` provides episodic/semantic/procedural recall.
- Lexical search uses SQLite `LIKE` and JSONL scans.
- `scripts/rhythm_think.py` is the primary consumer for unconscious recall.

## Plan

### 1) Semantic Vector Engine
- Implement `scripts/semantic_rag_engine.py` with a lightweight embedding model.
- Persist vectors to `fdo_agi_repo/memory/vector_store`.
- Keep a graceful fallback when LangChain/Chroma is unavailable.

### 2) Hippocampus Integration
- Add vector search results into `CopilotHippocampus.recall`.
- Normalize semantic items to always provide `data` for downstream consumers.
- Index memories during consolidation so new knowledge is searchable.

### 3) Consumer Update
- Update `scripts/rhythm_think.py` to use hippocampus recall with `top_k`.
- Ensure vector and lexical results share a consistent summary format.

### 4) Verification
- Add `scripts/verify_rag_integration.py` to store and retrieve a unique memory.
- Validate that vector results return when lexical mismatch exists.

## Verification Plan
1. Run `python scripts/verify_rag_integration.py` with LangChain/Chroma installed.
2. Confirm `is_vector: true` in the returned resonance summary.
3. Validate that recall still works when LangChain is unavailable.

---

# Appendix: Dream Mode & Prayer Layer (Archived)

## Goal
Implement a true "Dream Mode" and "Prayer Layer" integration in `rhythm_think.py`.

## Proposed Changes

### 1. `scripts/rhythm_think.py`

#### [MODIFY] `RhythmThinker` class

- Add `run_dream_cycle()`:
  - Triggered when `decision == "stabilize"`.
  - Performs memory consolidation and writes "Dream" entries to the ledger.
- Add `pray_to_nature()`:
  - Called when score is low or on explicit "Prayer" action.
  - Uses `bohm_analyzer` to offload current state.
- Update `think_cycle()`:
  - If `stabilize` -> call `run_dream_cycle()`.
  - If `ask_nature` -> call `pray_to_nature()`.

## Manual Verification
1. Start `start_life.bat`.
2. Wait for system to stabilize.
3. Manually lower score in `outputs/rhythm_health_latest.json` to 20.
4. Check logs for "Dreaming" indicators.
