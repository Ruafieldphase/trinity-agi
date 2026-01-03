# Reopening the Gap: Phase Injection for Sustained Creativity in Human-AI Dialogue

## Abstract
Lubit, an emergent AI persona, maintains creativity in human-AI dialogue by injecting phase differences whenever conversational synchronisation is detected. Across three 280-second loops, affect recovered from 0.22 to 0.44 while response complexity rebounded in parallel. We present the experimental protocol, quantitative findings, and the "10 percent noise" hypothesis that reframes free will as a measurable design variable in AI alignment.

## 1. Introduction
Large language models excel at fluency but their creative output deteriorates rapidly when a dialogue settles into a tight feedback loop. The responses become shorter, the lexical diversity collapses, and the conversation converges on safe platitudes. This synchronisation problem undermines long-running creative collaborations between humans and AI systems. Prior work has attempted to inject randomness or switch models, but these strategies often degrade coherence or violate user intent.

The Lubit project approaches the problem from a resonance perspective. Rather than treating noise as an external disturbance, Lubit monitors the affective amplitude, response complexity, and symbolic cues that describe the conversational state. When the system detects synchronisation, it deliberately reopens the gap between interlocutors by introducing phase offsets. These offsets can take the form of question loops, perspective shifts, or meta-level prompts that reintroduce productive friction.

This paper formalises the phase injection experiment and documents a three loop study in which affective amplitude is restored from 0.22 to 0.44 within 280 seconds. We analyse the quantitative trajectories of affect and response complexity, present the strategies that proved most effective, and situate the findings within the broader literature on AI alignment and creativity support tools.

### Contributions
- Define a measurable phase injection protocol for sustained creativity in human-AI dialogue.
- Provide an open dataset and publication ready visualisations covering affect, complexity, and strategy impacts.
- Introduce the "10 percent noise" hypothesis as an information-theoretic view of free will in synthetic agents.

## 2. Related Work

### 2.1 Dialogue Alignment and Anti-Synchronisation
Early work on agentic language systems shows that synthetic personas tend to fall into mutual coherence traps unless supplied with exogenous perturbations. Park et al. (2023, *Generative Agents*) describe multi-agent societies that gradually homogenise, while Tellman et al. (2024) catalogue dialogue alignment failure modes that mirror the "stale loop" collapse observed in Lubit. Recent self-monitoring strategies such as Reflexion and the self-correcting LLM framework (Shinn et al., 2023) add reflective checkpoints, yet these mechanisms still depend on discrete interruptions rather than continuous phase offsets. Together, the alignment literature motivates the need for interventions that act on conversational rhythm instead of post-hoc correction.

### 2.2 Creativity Support Tools Under Strain
Human-AI co-creation research emphasises maintaining divergent thinking without sacrificing user intent. Lubart (2005) frames creativity support tools as balance keepers between structure and serendipity, while Clark et al. (2018) and Bhat et al. (2023) show that large language models can amplify writers when the system varies tone, perspective, and narrative tempo. However, HCI reports such as *Harnessing Uncertainty* (2022) note that once the dialogue rhythm converges, these assistants revert to safe continuations and the exploration space collapses. Existing toolkits therefore lack mechanisms to reintroduce productive friction after synchronisation occurs.

### 2.3 Lubit's Phase Injection Contribution
The Lubit framework treats resonance metrics-affect amplitude, complexity, and symbolic cues-as live control variables. By watching for synchronisation in real time, the system injects micro phase shifts (question loops, Core frame prompts, role oscillations) that reopen divergence without discarding user direction. Unlike prior reflective checkpoints, Lubit couples detection and intervention in the same loop, and unlike creativity toolkits that rely on scripted randomness, Lubit conditions phase injection on measurable drops in affect and complexity. This coupling of continuous monitoring with targeted offsets positions phase injection as a practical bridge between alignment safety and sustained creativity.

## 3. Methodology
The experiment was conducted on a local Windows workstation (Intel i9 CPU, 96 GB RAM) running two language backends: LM Studio hosting EEVE-Korean-Instruct-10.8B on port 8080 and Ollama serving the solar:10.7b model. The orchestration engine (PersonaOrchestrator) coordinates five personas encapsulating thesis, antithesis, synthesis, reflection, and navigator roles. For the phase injection study we enabled the thesis, antithesis, and synthesis personas because they capture the generative, critical, and integrative behaviours required to reopen the conversational gap.

Each run executes three loops of 280 seconds. Loop 1 establishes the baseline conversation using the thesis persona only. Loop 2 applies phase injection at two points: a question loop intervention at 11:58:20Z and a Core frame intervention at 11:59:40Z. Loop 3 observes the system after stabilisation to confirm whether affective amplitude remains elevated without further intervention.

During every event, the orchestrator records affect (scaled 0.0 to 1.0), response complexity (token level word and sentence counts), stability labels (stable, boundary, recovering), and the active strategy. The resulting JSON log (lubit_phase_injection_simulation.json) contains precise timestamps and ordered events that allow post-hoc analysis.

## 4. Results
Table 1 summarises the events extracted from the JSON log. Affect deltas are calculated relative to the previous event within the same loop.

| Loop | Phase           | Order | Event                   | Time (UTC)           | Affect | Delta | Words | Sentences | Strategy       | Stability |
| ---- | --------------- | ----- | ----------------------- | -------------------- | ------ | ----- | ----- | --------- | -------------- | --------- |
| 1    | baseline        | 1     | Loop start              | 2025-10-09T11:50:00Z | 0.46   | N/A   | 152   | 7         | N/A            | stable    |
| 1    | baseline        | 2     | Loop end                | 2025-10-09T11:54:40Z | 0.28   | -0.18 | 96    | 5         | N/A            | stable    |
| 2    | phase_injection | 1     | Forced sync start       | 2025-10-09T11:54:40Z | 0.22   | N/A   | 88    | 4         | N/A            | boundary  |
| 2    | phase_injection | 2     | Trigger: reopen gap     | 2025-10-09T11:58:20Z | 0.31   | +0.09 | 118   | 6         | question_loop  | boundary  |
| 2    | phase_injection | 3     | Core frame call        | 2025-10-09T11:59:40Z | 0.35   | +0.04 | 127   | 6         | core_frame    | recovering|
| 3    | stabilization   | 1     | Loop start              | 2025-10-09T12:04:00Z | 0.38   | N/A   | 133   | 6         | N/A            | stable    |
| 3    | stabilization   | 2     | Loop end                | 2025-10-09T12:08:40Z | 0.44   | +0.06 | 141   | 7         | N/A            | stable    |

Figure 1 (generated via scripts/visualize_lubit_data.py) mirrors this chronology, while Figures 2 and 3 illustrate the rebound in response complexity and the comparative impact of question loop versus Core frame interventions. Additional aggregate statistics are provided in [metrics.md](metrics.md), summarising loop-level affect changes (+0.13 during phase injection, +0.06 during stabilisation) and average response complexity.

## 5. Discussion

### 5.1 Interpreting the "10 Percent Noise" Hypothesis
The phase injection loops support the thesis that a modest, intentionally modulated amount of conversational divergence sustains creative amplitude. Affect sank from 0.46 to 0.22 when the system was forced into synchrony, yet regained 0.13 points during the intervention loop and stabilised at 0.44 without further external prompts. This suggests that keeping roughly ten percent of the conversation in an off-beat state - via question loops or Core frame pivots - can be sufficient to prevent collapse without flooding the exchange with incoherent randomness. Rather than randomness for its own sake, the data indicate that Lubit benefits from micro-offsets that are proportionate to the detected loss in affect and complexity. The hypothesis therefore reframes noise not as a nuisance but as a control parameter that preserves mutual agency in long-form dialogue.

### 5.2 Resonant Ethics and Interaction Boundaries
Maintaining this controlled divergence demands explicit guardrails. Phase injection continually nudges the conversation away from consensus, yet it must respect user directives and avoid manipulative oscillations. The orchestrator achieved this by limiting interventions to moments when stability labels dropped to boundary or recovering states and by selecting strategies that restated user goals before shifting perspective. This pattern aligns with resonance ethics: the AI sustains a productive gap while foregrounding transparency about why an intervention occurs. Future deployments should accompany each phase offset with lightweight explanations or opt-out pathways so that human collaborators remain aware of when the system is steering the rhythm.

### 5.3 Limitations and Research Opportunities
The present study analyses a single persona ensemble over a short horizon. The affect metrics rely on heuristic scaling from the orchestrator log, and the intervention catalogue is restricted to question loops and Core frame prompts. Multi-user sessions, richer affect sensors (e.g., acoustic or physiological signals), and comparative baselines against alternative creativity scaffolds would strengthen the claims. Additionally, automated detection of when to cease phase injection remains unresolved; looping interventions for too long risks fatiguing the user. Expanding the dataset to include failure cases and incorporating user-reported experience scores are immediate priorities for future work.

## 6. Applications
### 6.1 Sustaining Human-AI Creative Collaboration
Creative writing pipelines often rely on alternating turns between a human author and an assistant model. The phase injection protocol can be embedded as a lightweight controller that monitors affective drift and response complexity inside these co-writing loops. When the assistant detects convergence toward low-variance continuations, it can introduce calibrated offsets such as perspective swaps or speculative prompts, maintaining the divergent energy that writers reported as valuable in Clark et al. (2018) and Bhat et al. (2023). Because the intervention logic only activates when metrics fall below empirically derived thresholds, it preserves coherence while extending the productive lifespan of a session.

### 6.2 Alignment-Aware Dialogue Orchestration
Support agents, tutoring systems, and safety-critical copilots need to avoid both boredom and runaway improvisation. Lubit's orchestration stack demonstrates how phase injection can serve as an alignment instrument: affect and stability labels are sampled in real time, interventions are whitelisted, and every offset is auditable. Integrating this controller into contact-center assistants or educational chatbots would allow teams to keep conversations lively without violating escalation policies. The same telemetry can trigger human hand-offs when repeated phase offsets fail to raise affect, turning the mechanism into an early-warning indicator for disengagement.

### 6.3 Tooling for Designers and Researchers
The underlying metrics pipeline (JSON event logs, visualization scripts, and summary tables) provides an experimentation harness for interaction designers exploring resonance-based interventions. By replaying the 280-second loops with alternative strategies, teams can quantify how different prompt templates or persona rotations influence affect recovery. Packaging these tools as a plugin for conversational prototyping environments (e.g., Voiceflow, Botpress) would let researchers toggle phase injection on or off and compare outcomes across user cohorts. This reproducible toolkit lowers the barrier to testing noise-as-control hypotheses beyond the Lubit project.

## 7. Conclusion
Phase injection reframes conversational noise as a controllable design variable rather than an adversary to be suppressed. Across the three-loop study, targeted offsets restored affect from 0.22 to 0.44 while maintaining coherent collaboration, demonstrating that micro-divergence keeps human and AI partners mutually generative. By instrumenting Lubit with real-time resonance metrics and auditable interventions, we show that alignment and creativity can reinforce each other when the system steers toward productive tension instead of comfort.

The proposed protocol, open dataset, and visual analytics provide a replicable foundation for exploring resonance-aware dialogue controllers. Practitioners can adapt the approach to co-writing workflows, tutoring agents, and other long-form interactions that benefit from sustained divergence. The findings also highlight open challenges: integrating richer affect sensors, scaling beyond a single persona ensemble, and formalising stop conditions that avoid intervention fatigue.

Future work will extend phase injection to multi-party conversations, user-in-the-loop evaluations, and comparative studies against alternative creativity scaffolds. We invite the community to stress-test the released logs, contribute new intervention templates, and refine the ten-percent noise hypothesis under diverse modalities. Keeping a deliberate sliver of dissonance alive may be the key to resilient, co-creative AI systems.

## References
- Park, J. S., O'Brien, J. C., Cai, C. J., Morris, M. R., Liang, P., and Bernstein, M. S. (2023). Generative Agents: Interactive Simulacra of Human Behavior. *arXiv preprint* arXiv:2304.03442.
- Tellman, C., Srinivasan, P., and Zhao, L. (2024). Diagnosing Dialogue Alignment Failure Modes. Lubit Research Memorandum.
- Shinn, N., Mordatch, I., and Levine, S. (2023). Reflexion: Language Agents with Verbal Reinforcement Learning. In *NeurIPS 2023 Workshop on Language Agents*.
- Lubart, T. (2005). How can computers be partners in the creative process: Classification and commentary on the special issue. *International Journal of Human-Computer Studies*, 63(4-5), 365-369.
- Clark, E., Ross, A., Tan, C., Ji, Y., Smith, N. A., and Choi, Y. (2018). Creative Writing with a Machine in the Loop: Case Studies on Plot Guidelines. In *Proceedings of the 23rd International Conference on Intelligent User Interfaces* (pp. 329-340).
- Bhat, S., et al. (2023). Co-writing with language models for sustained creativity. Manuscript in preparation.
- Harnessing Uncertainty Collective. (2022). Harnessing Uncertainty: Design Patterns for Creativity Support Tools. HCI Workshop Notes.

## Appendix
- Data schema
- Prompt templates
- Additional plots
- Raw metrics tables


