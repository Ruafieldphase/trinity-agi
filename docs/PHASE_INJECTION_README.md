# Phase Injection Analysis Quickstart

This guide packages the assets we just assembled so anyone can reproduce the core NAEDA phase-injection experiments, inspect the outputs, and reuse the metrics for further analysis.

## Prerequisites
- Python 3.10+ with `pip`
- Recommended packages (install once):  
  `pip install pandas matplotlib langgraph jsonschema`
- Repository layout keeps raw conversation exports under `ai_binoche_conversation_origin/` and simulation batches at the repository root (for example `batch_config.json`).

## 1. Generate Structured Datasets
We consolidate simulation results with:
```bash
python scripts/prepare_phase_injection_dataset.py --config batch_config.json --summary batch_summary.json
```
Outputs land in `outputs/phase_injection/`:
- `phase_runs.csv` – normalized view of scenarios declared in `batch_config.json`
- `phase_summaries.csv` – final states per scenario (affect, regulation deltas, symbol memory)
- `phase_timeline.csv` – optional per-step snapshots when a scenario exports a `json_out` timeline

## 2. Derive Metrics and Plots
Quantitative summaries use the dataset above:
```bash
python analysis/phase_metrics.py --plots
```
This emits `outputs/phase_injection/metrics/` containing:
- `affect_metrics.csv` – initial/final amplitudes, deltas, min/max/mean from timelines
- `regulation_metrics.csv` – freedom/stability deltas for quick comparison
- `loop_metrics.csv` – loop counts and recursion limits (useful for convergence talk)
- `symbol_memory_usage.csv` – frequency table of markers such as `phase_injected`
- `affect_summary.png` – bar chart showing initial vs final affect per scenario

You can skip `--plots` if Matplotlib is unavailable; the CSVs will still be generated.

## 3. Bring In Fresh Conversation Logs (Optional)
The combined dialogue exports already live at `outputs/ai_conversations_combined.csv`. To rebuild:
```bash
python scripts/build_combined_conversations.py --input ai_binoche_conversation_origin --output outputs/ai_conversations_combined.csv
```
Pairing those logs with the metrics lets you trace *why* affect recovered in a given scenario (e.g., pull the corresponding conversation slices and annotate them inside the forthcoming report).

## 4. Suggested Next Steps
- Run the metrics on a fresh baseline where `Phase Injection` is disabled to populate the comparison table.
- Copy the generated CSVs/plots into the `docs/preliminary_study.md` draft (see below) and add narrative commentary.
- Ask 2–3 peers to clone the repository, follow this README, and send back execution notes—log any friction in the README troubleshooting section.

## 5. Conversation Diversity Metrics (Optional but Recommended)
Use the long-form dialogue archive to quantify lexical diversity and engagement patterns:
```bash
python analysis/conversation_diversity.py --input outputs/ai_conversations_combined.csv --plots
```
Outputs under `outputs/conversation_metrics/` include:
- `conversation_summary.csv` – per-conversation token totals, type/token ratio, user·assistant balance
- `daily_summary.csv` – message volume trend for timeline charts
- `author_summary.csv` – turn length statistics by role (user vs assistant vs others)
- `token_frequency.csv` & `top_tokens.png` – quick snapshot of dominant vocabulary (Hangul-friendly fonts auto-configured)

## 6. Persona Orchestration Demo
Run the thesis→antithesis→synthesis loop that coordinates local and CLI-based LLMs:
```bash
python orchestration/persona_orchestrator.py ^
  --prompt "Design an empathic AI coach for creative writers." ^
  --depth 2 ^
  --config configs/persona_registry.json ^
  --log outputs/persona_runs/session_001.jsonl
```
- Adjust `configs/persona_registry.json` so each backend matches your environment (LM Studio command, Claude CLI, Gemini CLI, etc.).
- If a command is missing, the orchestrator falls back to the echo backend unless `--strict-cli` is passed.
- Logs (JSON Lines) capture persona metadata, prompt digests, full responses, and phase controller diagnostics (affect delta, loop count, injection flag).

## 7. Repro Checklist & Collaboration
- **One-click run**:  
  ```bash
  python scripts/run_research_pipeline.py --scenario creative_coach
  ```
  (CLI 백엔드가 없다면 `--skip-orchestrator`를 붙여 실행하세요.)
  - CLAUDE 토큰이 만료돼 있다면 스크립트가 자동으로 `local_ollama` 백엔드로 바꿔 줍니다. 강제로 외부 CLI를 쓰고 싶으면 `--force-external` 플래그를 추가하세요.
- `scripts/prompt_scenarios.json`에서 준비된 시나리오를 확인하거나, `--prompt "..."` 플래그로 수동 입력 가능합니다.
- **Log analytics**: summarise orchestration runs and (optionally) plot injection trends:
  ```bash
  python analysis/persona_metrics.py outputs/persona_runs/session_001.jsonl --plots
  ```
- **Detailed steps**: `docs/REPRODUCTION_GUIDE.md`는 설치부터 결과 검증까지의 전체 순서를 제공합니다.
- **Sample scenarios**: see `docs/PERSONA_ORCHESTRATION.md` for ready-made prompts and expected behaviours.
- **Roadmap & open issues**: contribution guidelines and future tasks are tracked in `docs/OPEN_ROADMAP.md`.
- **Backend availability**:  
  ```bash
  python scripts/check_persona_backends.py
  ```
  로컬에 설치된 CLI(ollama, LM Studio, Claude CLI 등)가 PATH에 제대로 등록됐는지 확인하세요.
  - LM Studio 서버를 활용한다면 `scripts/lmstudio_chat.py`가 해당 엔드포인트로 호출하므로, `configs/persona_registry.json`의 `"--model"` 값이 실제 로드한 모델명과 일치하는지(예: `Meta-Llama-3-8B-Instruct`) 확인하고, LM Studio 개발자 페이지에서 해당 모델을 Load 해두세요.
- **Feedback loop**: when sharing results, attach the command history plus generated CSV/PNG files so reviewers can diff against their local runs.

These steps form the minimum reproducible package we can pass to KAIST or external reviewers while we continue deeper experiments.
