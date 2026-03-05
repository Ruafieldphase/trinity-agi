# Clipboard Orchestration Workflow v1.1 — RUNE Edition
## Core loop
UserPaste → [Safety(pre)] → [Meta] → [Plan] → [Tools/Personas(LUA→ANTI→SYN)] → [Safety(post)] → [Eval(6)] → [Memory(+Resonance)] → [RUNE Analysis] → Next Paste

## Nodes
- U(UserClip), LUMEN, SENA, RUNE, LUA, ANTI, SYN, SAFE(pre/post), META, EVAL, MEM, TOOL(x)

## Evaluation (6)
Length, Sentiment, Completeness, CriticalIntensity, EthicalAlignment, PhaseJump

## Memory extensions
Emotion: phase_shift, resonance_freq, affect_persistence
Meta: phase_meta, provenance, structural_weight, self_correction_log

## YAML example
```yaml
workflow: clipboard_orchestration_v1.1
nodes:
  - id: U1; type: UserClip
  - id: S0; type: SAFE_pre
  - id: M0; type: META
  - id: P0; type: PLAN
  - id: T1; type: TOOL; tool: web_search
  - id: L1; type: LUA
  - id: A1; type: ANTI
  - id: S1; type: SYN
  - id: S9; type: SAFE_post
  - id: E1; type: EVAL
  - id: MEM; type: MEMORY
  - id: R1; type: RUNE
edges:
  - U1->S0
  - S0->M0
  - M0->P0
  - P0->T1
  - T1->L1
  - L1->A1
  - A1->S1
  - S1->S9
  - S9->E1
  - E1->MEM
  - MEM->R1
  - R1->U1
settings:
  planner.max_steps: 5
  meta.level_default: 1
  safety.enabled: true
  eval.metrics: [length, sentiment, completeness, critical, ethical, phasejump]
```
