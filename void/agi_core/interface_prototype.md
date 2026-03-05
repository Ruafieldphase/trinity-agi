# Empathetic Exploration Engine — Interface Sketch

Scenario based on persona run (2025-10-11 12:55 UTC).

## Design Goals
- Convey emotional hypotheses as *suggestions*, not diagnoses.
- Collect user corrections without interrupting writing flow.
- Respect privacy/data minimisation.
- Maintain accessibility-first layout.

## Layout Concept
```
┌───────────────────────────────────────────────────────────────┐
│ Writing Canvas (primary focus)                                │
│ ───────────────────────────────────────────────────────────── │
│ [User text editor]                                            │
│ ⤷ optional subtle highlights (e.g., pale underline)           │
│                                                               │
│ Sidebar Tabs:  [Insights] [Context] [History] [Settings]      │
│                                                               │
│ ┌── Insights Tab (default collapsed to summary pill) ───────┐ │
│ │  Emotional Snapshot: “Tentative optimism?” (confidence ●○○)│ │
│ │  Hypothesis Rationale:                                     │ │
│ │   • increase in positive adjectives vs baseline            │ │
│ │   • shorter sentences than typical draft                   │ │
│ │  Actions: [Sounds right] [Not accurate] [Tune ↴]            │ │
│ └───────────────────────────────────────────────────────────┘ │
│                                                               │
│ Correction Modal (when user clicks “Not accurate”)            │
│  • Prompt: “How would you describe your current tone?”        │
│  • Quick buttons (customisable): [Relaxed] [Frustrated] [...] │
│  • Optional text area                                         │
│  • Checkbox: “Update baseline”                                │
│  • Submit → log correction, adjust weights                    │
│                                                               │
│ Context Tab                                                   │
│  • Genre / audience / personal goal chips (user editable)     │
│  • “Share reason for upcoming deadline?” toggle               │
│  • Data collection summary (“Only style metrics stored”)      │
│                                                               │
│ History Tab                                                   │
│  • Timeline of past hypotheses & user responses               │
│  • “Revert to older baseline”                                │
│                                                               │
│ Settings Tab                                                  │
│  • Master toggle “Emotional assistance ON/OFF”                │
│  • Feedback intensity slider (Subtle ←→ Detailed)             │
│  • Notification mode (visual, audio, none)                    │
│  • Data retention period                                     │
└───────────────────────────────────────────────────────────────┘
```

## Interaction Flow
1. **Opt-in**: user toggles “Emotional assistance” in Settings.
2. During writing, coach surfaces a *pill* with hypothesis summary.
3. User accepts or corrects; corrections feed calibration store.
4. Coach updates baseline and explains next hypothesis accordingly.

## Privacy & Data Minimisation
- Default collects: tokenised word frequency, sentence length, break timestamps.
- Optional user context (genre, goals) stored locally; can be cleared.
- Explicit statement in Context tab about what is analysed/stored.

## Accessibility Considerations
- WCAG AA contrast; keyboard navigable.
- Supports screen readers (ARIA labels for hypotheses, controls).
- Provide equivalent textual description for visual cues (colour shifts).
*** End Patch
