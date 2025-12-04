# Phase Injection: A Preliminary Study on Maintaining Dialogue Affect Diversity

> Working draft – last updated YYYY-MM-DD.

## 1. Motivation
- Summarise the 6-month NAEDA build: fusion of Phase Injection, Boundary Language, and LangGraph control loops.
- Highlight captured artefacts: `outputs/ai_conversations_combined.csv` (11 months의 에이전트 로그), `outputs/phase_injection/` (시뮬레이션 메트릭), `outputs/conversation_metrics/` (대화 다양성 지표).
- State research question: *Does periodic Phase Injection stabilise affect amplitude and conversational diversity in autonomous dialogue loops?*

## 2. Experimental Set-up
1. **Simulation graph** – describe the nodes implemented in `naeda_langgraph_demo.py` (Analyze → Phase Injection → Respond).
2. **Scenarios** – tabulate `phase_runs.csv` (baseline vs boosted affect, boundary windows, loop counts).
3. **Data pipeline** – 실행 명령:  
   `python scripts/prepare_phase_injection_dataset.py …`,  
   `python analysis/phase_metrics.py --plots`,  
   `python analysis/conversation_diversity.py --plots`.
4. **Conversation grounding** – `conversation_summary.csv`에서 type/token ratio 상위·하위 대화를 선택하고, 원본 로그와 함께 정성 해석을 정리.
5. **Persona orchestration** – `orchestration/persona_orchestrator.py` 실행 결과를 기록해 실시간 정반합 루프와 phase injection의 상호작용을 캡처.

## 3. Metrics
- Affect amplitude (`phase_injection/metrics/affect_metrics.csv`): initial vs final, min/max/mean.
- Regulation deltas (`phase_injection/metrics/regulation_metrics.csv`): freedom/stability trade-offs.
- Loop behaviour (`phase_injection/metrics/loop_metrics.csv`): convergence speed, recursion cap usage.
- Symbol memory usage (`phase_injection/metrics/symbol_memory_usage.csv`): semantic markers invoked during recovery (예: `phase_injected`, `low_affect`).
- Lexical diversity (`conversation_metrics/conversation_summary.csv`): type/token ratio, 사용자·에이전트 발언 비율, 평균 발화 길이.
- Engagement trend (`conversation_metrics/daily_summary.csv`, `messages_per_day.png`): 장기 실험 기간 동안 메시지 양상.
- Persona loop diagnostics (`persona_metrics/persona_summary.csv` 등): 정반합 페르소나별 injection rate, 평균 affect 변화, 백엔드 안정성.

## 4. Results Snapshot
- Insert `affect_summary.png` with caption: *Phase Injection keeps boosted scenario stable while baseline recovers from 0.22 → 0.30 affect.*
- Draft bullet takeaway (fill in with actual numbers after running metrics):
  - Baseline affect delta: **+0.08** with symbol memory markers `low_affect → phase_injected`.
  - Boosted affect delta: **0.00** (already high affect; verify no overshoot).
  - Loop counts: baseline exits after 1 injection; boosted maintains loop count 2 (pre-loaded memory).
- Conversation diversity: `conversation_summary.csv` 기준 type/token ratio 상위·하위 5개 대화의 평균 값을 인용 (실제 수치 업데이트).
- Reference at least one qualitative example from the conversation logs (link message IDs once selected). Pair with `top_tokens.png` to comment on 주제 반복 여부.

## 5. Limitations
- Simulations currently deterministic; need stochastic runs (e.g., noise in affect decay) to measure variance.
- Phase-off baseline pending to isolate injection contribution explicitly.
- External validation deferred to KAIST/partner lab (state plan for handing over datasets + scripts).
- Data privacy: confirm anonymisation when sharing conversation snippets.

## 6. Roadmap (Next 4–6 Weeks)
1. Expand metrics: include sentiment diversity, response latency, symbol-memory entropy.
2. Run 20× repeated trials per scenario with random seeds.
3. Incorporate “no injection” control and alternative boundary windows.
4. Connect the persona orchestrator 로그(`outputs/persona_runs/*.jsonl`)와 정량 메트릭을 연동해 실험 섹션 보강.
5. 공개 로드맵(`docs/OPEN_ROADMAP.md`)을 최신 상태로 유지하며 외부 피드백 수집.
6. Prepare arXiv-style PDF export (LaTeX or Typst) once tables/figures are final.

## Appendix A. Reproduction Checklist
- [ ] Clone repository & install Python dependencies.
- [ ] Run dataset + metrics scripts without manual edits.
- [ ] Verify `outputs/phase_injection/metrics/*.csv` match table values.
- [ ] Rebuild `ai_conversations_combined.csv` and validate hashes (optional).
- [ ] Document any issues in `docs/PHASE_INJECTION_README.md` troubleshooting section (to be added).
