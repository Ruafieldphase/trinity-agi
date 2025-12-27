# Walkthrough: RAG Upgrade and Temporal Geometry Alignment

## Summary
This document captures the semantic RAG upgrade, the temporal-geometry alignment based on the "irreversible meaning" framing, and the refined question-generation boundary policies for FSD.

## Changes
- Semantic RAG core with LangChain + Chroma; vector recall integrated into Hippocampus.
- Bohm analyzer includes temporal geometry metrics: temporal_density, meaning_mass, irreversibility.
- RhythmThink uses temporal geometry to bias rhythm score and decision policy, and reports temporal geometry in the narrative output.
- RhythmThink adds an idle pulse: when no external signals persist, a tiny drift keeps the system moving without heavy automation.
- Natural rhythm clock emits bio-rhythm signals (melatonin proxy, sleep pressure); RhythmThink logs snapshots to the ledger and surfaces notes without influencing score/phase.
- Rhythm guidance stays advisory: signals are recorded and visible but do not bias scoring, routing, or execution.
- GUI execution keeps rhythm as a notice-only signal; no rhythm-based gating or threshold changes.
- Auto policy and browser exploration pacing treat rhythm as observation-only; no rhythm-driven action overrides.
- Zone2 is treated as the base state; execution is a transient wave that returns without evaluation.
- FSD Question Boundary: `services/fsd_controller.py` adds ActionType.QUESTION and Z2_IDLE handling with repetition penalty (edge_histogram).
- Slack question bridge: `services/slack_gateway.py` + `verify_slack_question.py` validate async human-in-the-loop flow.
- Questions are treated as state transitions, deduped by boundary signature, and capped per episode (max 2).
- Timeouts are interpreted as intentional non-intervention and fall back to Z2_IDLE, with a 2-strike escape policy.
- Meaning-branch questions are dual-gated (hard-gate risky keywords + LLM meaning decision).
- Boundary memory uses a FIFO cap (max 50) to prevent OOM.
- Z2_IDLE state freeze skips redundant captures and reporting.
- AGI_VERIFY_MODE suppresses heavy sync during verification runs.
- Maturation observation cycle validates 5 episodes (dedup, suppression, timeout, idle/forgetting, quality).
- GUI sandbox can now restrict actions to specific window titles (e.g., Chrome-only scope).
- Minimal chat channel added: write to `inputs/agi_chat.txt`, read response from `outputs/agi_chat_response.txt` (explicit routing only).
- Simple chat window added for the minimal chat channel (Tkinter UI).

## Files
- scripts/semantic_rag_engine.py
- fdo_agi_repo/copilot/hippocampus.py
- scripts/bohm_implicate_explicate_analyzer.py
- scripts/rhythm_think.py
- scripts/agi_chat_window.py
- services/fsd_controller.py
- verify_slack_question.py
- observe_fsd_maturation.py

## Verification
- scripts/verify_rag_integration.py (vector recall path).
- scripts/bohm_implicate_explicate_analyzer.py --hours 24 (temporal geometry written to outputs/bohm_analysis_latest.json/md).
- verify_slack_question.py (Phase 2/3/3.1 boundary policies, timeouts, FIFO eviction).
- observe_fsd_maturation.py (Phase 3.2 maturation observation cycle).

## Notes
Time is treated as a perceived axis derived from differences in meaning; meaning accumulation is irreversible and only re-ordered.
