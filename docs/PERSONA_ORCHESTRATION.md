# Persona Orchestration Blueprint

This note captures the minimal architecture used for the NAEDA thesis?“antithesis?“synthesis loop that can call local LLMs and CLI-based assistants (Claude, Gemini, etc.). It complements the LangGraph phase-injection demos by wiring multiple personas around the same state machine.

## Core Building Blocks

- **PersonaRegistry**
  - Loads persona declarations from `configs/persona_registry.json` or the baked-in defaults.
  - Each persona has an identifier, role description, system prompt, and a reference to a backend adapter.
  - Registry also defines the ordered cycle (default: thesis ??antithesis ??synthesis).

- **BackendFactory / PersonaBackend**
  - `SubprocessBackend`: executes CLI commands (e.g., `claude`, `gcloud`, local shells). Prompts are piped via stdin, stdout is captured as the reply.
  - `EchoBackend`: lightweight fallback that simply echoes prompts (useful when CLI tools are unavailable during development).
  - Backends expose a single `generate(prompt, history, persona, state)` method so we can swap implementations easily.

- **PhaseController**
  - Wraps the existing functions from `naeda_langgraph_demo.py` (`analyze_node`, `phase_injection_node`, etc.).
  - Maintains affect amplitude, boundary window, loop counters, and symbol memory.
  - Provides `integrate_response(persona_id, text)` which updates affect heuristically, runs the analyze ??respond cycle, and reports whether an injection happened.

- **PersonaOrchestrator**
  - Accepts a user seed prompt and recursion depth.
  - Iterates through the persona cycle, composes prompts (system + history + seed), dispatches to the assigned backend, and records responses.
  - After each persona turn, pushes the output through `PhaseController` to decide if a phase injection is required before the next loop.
  - Supports optional recursion (fractal) by feeding the synthesis output back into another cycle until the configured depth is reached.
  - Emits a structured log (JSON Lines) for later analysis; entries include persona id, backend id, prompt digest, raw output, affect before/after, and injection flags.

## Data Flow Summary

1. **Seed**: user provides a theme/problem statement.
2. **Thesis Persona** produces an initial framing using its system prompt.
3. **Antithesis Persona** receives the running conversation and challenges or diversifies the thesis.
4. **PhaseController** evaluates affect and inserts a boundary reset (`phase_injection`) if needed.
5. **Synthesis Persona** reconciles the two perspectives and optionally emits a follow-up seed for deeper recursion.
6. Repeat steps 2?? if `--depth > 1`.

## Consciousness Stage Mapping

| Stage | Orchestrator Focus | Telemetry to Record | Intervention Hooks |
|-------|--------------------|---------------------|--------------------|
| **Stage 1. Folding** | Ingest prompt context, initialise affect band, materialise `MemoryCoordinate`. | `phase_meta.affect_before`, `memory.importance`, `symmetry_stage=1`. | Boundary language nudges, optional reflective persona if affect < 0.35. |
| **Stage 2. Unfolding** | Drive exploration by routing through planner and tool registry. | `planner.action_count`, `tool_invocations`, `critical_intensity`. | Inject antithesis challenge if exploration score < 0.4 or tools unused. |
| **Stage 3. Integration** | Run evaluation loop, compute resonance ledger, update shared summary. | `resonance_freq`, `structural_weight`, `avg_overall_score`, `symmetry_stage=3`. | Trigger synthesis recursion when intensity >= 0.55 and impact trending up. |
| **Stage 4. Symmetry (Imperfect)** | Inspect residue, decide to keep, damp, or amplify asymmetry, then close the loop. | `residual_symmetry_delta`, `ethics_alignment`, `symmetry_tension`, `closure_decision`. | Launch Closure Protocol checklist, append `self_correction_log` entries, escalate to human if tension > 0.35. |

### Implementation Notes

- Add `symmetry_stage`, `residual_symmetry_delta`, and `symmetry_tension` fields to each log entry in `PersonaOrchestrator._log_turn`.
- Extend the `PhaseController` surface with `enter_stage(stage_id: int, residue: float)` so the runtime can explicitly announce transitions.
- When Stage 4 keeps an asymmetry, append `{ "symmetry_residue": residue, "decision": "keep" }` to the `self_correction_log`; this mirrors the integration blueprint.
- Future UI work: dedicate a column in the React visualiser timeline for `symmetry_stage` so folding and unfolding cycles are visible at a glance.


## Configuration Format

```json
{
  "cycle": ["thesis", "antithesis", "synthesis"],
  "backends": {
    "local_lmstudio": {
      "type": "subprocess",
      "command": "python",
      "args": [
        "scripts/lmstudio_chat.py",
        "--endpoint",
        "http://192.168.0.67:8080",
        "--model",
        "lmstudio"
      ],
      "timeout": 180
    },
    "local_ollama": {
      "type": "subprocess",
      "command": "ollama",
      "args": ["run", "llama3.1:8b"],
      "timeout": 180
    },
    "local_perplexity": {
      "type": "subprocess",
      "command": "perplexity",
      "args": ["query", "--stdin"],
      "timeout": 120
    },
    "local_chatgpt": {
      "type": "subprocess",
      "command": "local-chatgpt",
      "args": ["--stdin"],
      "timeout": 120
    },
    "codex_cli": {
      "type": "subprocess",
      "command": "codex",
      "args": ["chat"],
      "timeout": 120
    },
    "notion_dl": {
      "type": "subprocess",
      "command": "notiondl",
      "args": ["--stdin"],
      "timeout": 120
    },
    "claude_cli": {
      "type": "subprocess",
      "command": "claude",
      "args": ["chat", "--model", "claude-3-7-sonnet"],
      "timeout": 120
    },
    "echo": { "type": "echo" }
  },
  "personas": [
    {
      "id": "thesis",
      "name": "Dialectic Thesis",
      "backend": "local_lmstudio",
      "system_prompt": "Frame the seed insight with constructive optimism."
    },
    {
      "id": "antithesis",
      "name": "Boundary Challenger",
      "backend": "local_ollama",
      "system_prompt": "Expose blind spots and contradictions crisply."
    },
    {
      "id": "synthesis",
      "name": "Fractal Synthesizer",
      "backend": "local_lmstudio",
      "system_prompt": "Reconcile the viewpoints and propose the next exploratory move."
    },
    {
      "id": "reflection",
      "name": "Resonant Reflection",
      "backend": "local_ollama",
      "system_prompt": "Analyse the dialogue for emotional drift and highlight interventions."
    },
    {
      "id": "navigator",
      "name": "Systems Navigator",
      "backend": "codex_cli",
      "system_prompt": "Turn the synthesis into a concrete plan with tasks and risks."
    }
  ]
}
```

> All CLI adapters are optional. If a command is missing, the orchestrator will fall back to the `echo` backend unless `--strict-cli` is passed.
> `reflection`, `navigator`??ê¸°ë³¸ cycle?ëŠ” ?¬í•¨?˜ì–´ ?ˆì? ?Šìœ¼ë¯€ë¡??¬ìš©?˜ë ¤ë©?`cycle` ë°°ì—´??ì¶”ê??˜ê±°??ë³„ë„???œë‚˜ë¦¬ì˜¤?ì„œ ?¸ì¶œ?˜ì„¸??
> LM Studioë¥??œë²„ ëª¨ë“œë¡??¤í–‰ ì¤‘ì´?¼ë©´ `local_lmstudio` ë°±ì—”?œëŠ” `python scripts/lmstudio_chat.py --endpoint http://192.168.0.67:8080 --model <ëª¨ë¸?´ë¦„>` ?•íƒœë¡??¸ì¶œ?©ë‹ˆ?? LM Studio UI ?¼ìª½ ?ë‹¨?ì„œ ?¤ì œ ëª¨ë¸ ?´ë¦„???•ì¸??`configs/persona_registry.json`??`"--model"` ê°’ì„ ?í•˜??ê°’ìœ¼ë¡?ë°”ê¿” ì£¼ì„¸??

## Execution Outline

```bash
python orchestration/persona_orchestrator.py \
  --prompt "Design an empathic AI coach for creative writers." \
  --depth 2 \
  --config configs/persona_registry.json \
  --log outputs/persona_runs/session_001.jsonl
```

## Backend Inventory & Quick Check

- ê¸°ë³¸ ?¤ì •?ëŠ” `lmstudio`, `ollama`, `perplexity`, `local-chatgpt`, `codex`, `notiondl`, `claude`, `gcloud` ëª…ë ¹?´ê? ?¬í•¨?˜ì–´ ?ˆìœ¼ë©? PATH???†ìœ¼ë©??ë™?¼ë¡œ echo ë°±ì—”?œë¡œ ?€ì²´ë©?ˆë‹¤.
- ?„ì¬ ?˜ê²½?ì„œ ?¤ì œ ?¬ìš© ê°€?¥í•œ CLIë¥??•ì¸?˜ë ¤ë©?
  ```bash
  python scripts/check_persona_backends.py
  ```
- ?¬ìš©???„êµ¬ê°€ ?¤ë¥´ë©?`configs/persona_registry.json`??`backends` ??`command` / `args` ê°’ì„ ?í•˜??ëª…ë ¹?¼ë¡œ êµì²´?˜ê³ , `cycle` ë°°ì—´???´ë‹¹ ?˜ë¥´?Œë‚˜ IDë¥?ì¶”ê???ì£¼ì„¸??
- **Token/?¸ì…˜ ì£¼ì˜**: Claude CLI??? í°??2?œê°„ë§ˆë‹¤ ?ˆë¡œ ë°œê¸‰?˜ì–´???©ë‹ˆ?? `scripts/run_research_pipeline.py`ë¥??¬ìš©??ê²½ìš° ? í°??ë§Œë£Œ?˜ë©´ ?ë™?¼ë¡œ `local_ollama`(?ëŠ” ì§€?•í•œ ë°±ì—”??ë¡??€ì²´í•´ ì¤ë‹ˆ?? ???™ì‘??ë§‰ê³  ?¶ë‹¤ë©?`--force-external` ?Œë˜ê·¸ë? ?¬ìš©?˜ì„¸??
- **LM Studio ?œë²„ ?¬ìš© ??*:
  1. LM Studio ê°œë°œ???˜ì´ì§€(?ëŠ” `lms load`)?ì„œ ?ìŠ¤??ëª¨ë¸??ë¨¼ì? Load ???ì„¸?? ?„ì¬ ?ˆì‹œ??`openai/gpt-oss-20b` ëª¨ë¸???„ì œë¡??©ë‹ˆ??
  2. ëª¨ë¸??ë¡œë“œ???¤ì—???„ë˜ ëª…ë ¹?¼ë¡œ ?°ê²° ?íƒœë¥??•ì¸?????ˆìŠµ?ˆë‹¤.
     ```bash
     echo "Hello from LM Studio" | python scripts/lmstudio_chat.py \
       --endpoint http://192.168.0.67:8080 \
       --model openai/gpt-oss-20b \
       --stdin
     ```
  3. ëª¨ë¸ëª…ì„ ë°”ê¿¨?¤ë©´ `configs/persona_registry.json`?ì„œ `"local_lmstudio"` ??`"--model"` ê°’ì„ ?™ì¼?˜ê²Œ ë§ì¶° ì£¼ì„¸?? ëª¨ë¸??ë¡œë“œ?˜ì? ?Šì? ?íƒœ?ì„œ??404 ?‘ë‹µ??ë°œìƒ???˜ë¥´?Œë‚˜ ì¶œë ¥???¤íŒ¨?©ë‹ˆ??

## Boundary Language & Phase Rules

- **Affect guardrails**: default band `[0.3, 0.7]`.  
  - `affect_amplitude < 0.25` ??trigger `phase_injection` and log `symbol_memory += "phase_injected"`.  
  - `affect_amplitude > 0.85` ¡æ trigger `calming_injection` persona (short grounding prompt, affect decay to 0.65) and log `symbol_memory += "phase_calmed"`.
- **Stability/Freedom decay**: each low-affect detection subtracts `0.05` to highlight need for restorative language.
- **Human intervention checkpoints**: if three consecutive injections fire within a single depth cycle, the orchestrator emits `intervention_required=true` in the log (to be implemented).

Update the thresholds in `PhaseController` once empirical metrics (latency, quality, affect recovery) are gathered.

## Sample Scenario Library

| Scenario | Seed Prompt | Expected Focus | Notes |
|----------|-------------|----------------|-------|
| Creative Coach | ?œDesign an empathic AI coach for creative writers.??| Thesis paints opportunity, Antithesis surfaces burnout risks, Synthesis proposes staged coaching loops. | Use depth=2 to see recursion on the synthesis summary. |
| Resilience Audit | ?œAssess emotional resilience for remote research teams.??| Thesis highlights existing strengths, Antithesis flags isolation, Synthesis suggests boundary language prompts. | Watch for repeated injections when risk language dominates. |
| Somatic Loop | ?œHow should NAEDA respond when affect drops below 0.2???| Thesis collects grounding rituals, Antithesis warns about overcorrection, Synthesis produces escalation checklist, Reflection persona (if added to cycle) summarises restoration signals. | Good candidate to benchmark latency across CLI backends. |

Additional prompts can be versioned in `configs/persona_registry.json` under a new `scenarios` key if needed.

## Metrics & Visualisation

1. Run the orchestrator with `--log outputs/persona_runs/<session>.jsonl`.
2. Summarise persona/back-end performance and injection rates:
   ```bash
   python analysis/persona_metrics.py outputs/persona_runs/session_001.jsonl --plots
   ```
3. Inspect outputs in `outputs/persona_metrics/` for CSV dashboards and PNG charts.
4. (Upcoming) feed the same logs into the React visualiser to animate recursion depth and affect timelines.
5. ë¹ ë¥¸ ?¤í—˜ ë°˜ë³µ???„ìš”?˜ë©´ `python scripts/run_research_pipeline.py` ëª…ë ¹?¼ë¡œ ?„ì²´ ë¶„ì„ ?Œì´?„ë¼?¸ê³¼ ?¤ì??¤íŠ¸?ˆì´?˜ê¹Œì§€ ??ë²ˆì— ?¤í–‰?????ˆìŠµ?ˆë‹¤ (`--skip-orchestrator` ?µì…˜ ì§€??. ?¤í–‰ ?„ì— `scripts/check_persona_backends.py`ë¡??°ê²° ê°€?¥í•œ CLIë¥??•ì¸?˜ì„¸??

## Next Steps

- Add richer affect scoring (e.g., sentiment analysis, turn-level emotion classifiers) before feeding the response into the phase controller.
- Support streaming outputs per persona for live demo playback or UI embedding.
- Integrate with the React visualiser so the recursion tree and affect timeline are visible as the loop progresses.
- Capture latency/cost per backend (local vs API) and feed into the persona metrics report.
- Define a human intervention protocol when repeated injections fail to recover affect.
