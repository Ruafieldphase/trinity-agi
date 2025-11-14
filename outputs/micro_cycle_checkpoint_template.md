# ⏱️ Micro-Cycle Checkpoint (T+45m)

> Use this template at ~45 minutes into a 2h micro-cycle to assess trajectory, intervene early, and amplify flow.

## 1. Snapshot
- Start Time (T0): <!-- HH:MM -->
- Current Time (T+45m): <!-- HH:MM -->
- Phase / Mode: <!-- e.g., Deep Build, Diagnostic, Refactor, Exploration -->
- Energy / Arousal (1-10): <!-- -->
- Cognitive Focus (1-10): <!-- subjective sustained attention -->
- Frustration / Load (1-10): <!-- higher => intervention needed -->
- Flow Index (derived): <!-- (Focus + (10 - Frustration)) / 2 -->

## 2. Key Artifacts Touched
| Domain | Artifact | Status | Risk |
|--------|----------|--------|------|
| Code | <!-- file/module --> | <!-- progressing / blocked --> | <!-- low/med/high --> |
| System | <!-- script / daemon --> | <!-- healthy / degraded --> | <!-- --> |
| Goals | <!-- goal id(s) --> | <!-- on-track / drifting --> | <!-- --> |
| Rhythm | groove_profile_latest.json | <!-- stable / shifting --> | <!-- --> |

## 3. Metrics Delta (Since Start)
| Metric | T0 Baseline | Current | Delta | Interpretation |
|--------|-------------|---------|-------|----------------|
| Task Queue Throughput | <!-- --> | <!-- --> | <!-- --> | <!-- --> |
| Error Rate (%) | <!-- --> | <!-- --> | <!-- --> | <!-- stable / rising --> |
| Mean Latency (ms) | <!-- --> | <!-- --> | <!-- --> | <!-- --> |
| Cognitive Interrupts (count) | <!-- --> | <!-- --> | <!-- --> | <!-- minimal / frequent --> |
| Context Switches | <!-- --> | <!-- --> | <!-- --> | <!-- healthy / excessive --> |

## 4. Rhythm & Groove Quick Read
- Rest Phase File: <!-- RHYTHM_REST_PHASE_* status -->
- Groove: swing_ratio=<!-- --> microtiming_variance=<!-- -->
- Trend: <!-- improving / regressing / neutral -->
- Adjustment Needed?: <!-- yes/no (if Flow Index < 6 or Frustration > 6) -->

## 5. Risk Scan
| Risk Vector | Signal | Severity | Mitigation Action |
|-------------|--------|----------|-------------------|
| Copilot 400 Errors | <!-- count / last seen --> | <!-- low/med/high --> | <!-- fallback bridge / retry logic --> |
| Degraded Task Queue | <!-- symptom --> | <!-- --> | <!-- ensure server / worker restart --> |
| Context Drift | <!-- indicator --> | <!-- --> | <!-- trigger context snapshot --> |
| Latency Spikes | <!-- metric --> | <!-- --> | <!-- warmup / cache priming --> |

## 6. Decision Gate
- Continue Unmodified? <!-- yes/no -->
- Minor Course Correction? <!-- e.g., tighten scope, drop 1 low priority task -->
- Major Reset? <!-- only if Flow Index < 5 for >15m -->
- Selected Path: <!-- -->

## 7. Immediate Interventions (if any)
- [ ] Regenerate autonomous goal subset
- [ ] Run quick health probe
- [ ] Activate fallback AI bridge
- [ ] Perform cache warm horizon scan
- [ ] Trigger rhythm modulation (audio / binaural)

## 8. Updated Next 45m Focus
| Priority | Objective | Expected Artifact | Success Criteria |
|----------|-----------|-------------------|------------------|
| 1 | <!-- --> | <!-- file/output --> | <!-- measurable outcome --> |
| 2 | <!-- --> | <!-- --> | <!-- --> |
| 3 | <!-- --> | <!-- --> | <!-- --> |

## 9. Logging Hooks
Append summary to: `outputs/micro_cycle_summary.md`
Add structured entry to: `fdo_agi_repo/memory/goal_tracker.json` (if goals re-scoped)

## 10. Quick Reflection
- Biggest Win (so far): <!-- -->
- Emerging Blocker: <!-- -->
- Hidden Complexity Surfaced?: <!-- -->
- One Adjustment to Try: <!-- -->

---
Template version: 1.1
Fill objectively; prefer brevity over narrative. Intervene early, not late.
