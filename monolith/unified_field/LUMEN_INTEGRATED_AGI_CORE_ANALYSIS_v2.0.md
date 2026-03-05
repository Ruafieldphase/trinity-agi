# LUMEN Integrated AGI Core Analysis v2.0 (Condensed)
**Date:** 2025-10-12

## Decisions
- Storage: v1.0 JSONL → v2.0 SQLite/VectorDB.
- Memory: add `phase_shift`, `resonance_freq`, `affect_persistence`; meta: `phase_meta`, `provenance`, `structural_weight`, `self_correction_log`.
- Evaluation: 4 → 6 metrics = Length, Sentiment, Completeness, CriticalIntensity, EthicalAlignment, PhaseJump.
- Tools: v1.0 rules-based; v2.0 TaskClassifier (LLM) for semantic routing.
- Safety: pre/post boundary verification; MetaCognition runs before Planner.
- Roles: LUMEN (orchestrator), SENA (builder), LUBIT (memory), RUNE (analyzer).

## Weekly roadmap (4→5 weeks)
- W1: Memory + Evaluation
- W2: Tools + Safety (pre/post)
- W3: Planner + MetaCognition
- W4: Elo orchestration + Integration
- W5 (opt.): VectorDB + Self-correction log

## Execution loop (revised)
Input → Safety(pre) → MetaCognition → Planner → Elo/Tools → Safety(post) → Evaluation(6) → Memory → (feedback)
