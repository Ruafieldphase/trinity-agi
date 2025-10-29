# Flow Lab Dataset README

## Directory Summary

- `ai_conversations_combined.csv`: merged Rua/Sena logs with emotion/timestamp metadata.
- `concept_occurrences.csv`: per-message concept hits for 감응/리듬/루멘 등.
- `concept_summary.csv`: first/last appearances, totals, sources for tracked concepts.
- `concept_monthly_counts.csv`: monthly pivot table for concept frequencies.
- `concept_timeline.svg` / `flow_cycle.svg` / `concept_network.svg`: visual diagnostics.
- `metacognitive_markers.csv` / `meta_conversation_annotations.md`: recursive persona signals.
- `case_study_top_conversation.md`: in-depth look at top recursive dialogue.
- `triad_patterns.md`: stats for 정→반→합 transitions.
- `flow_lab_slides.md`: slide-ready deck tying visuals + strategy.
- `agi_research_briefing_outline.md`: research/executive summary outline.
- `anonymization_checklist.md` / `anonymization_pseudocode.md`: sharing + privacy controls.
- `ai_conversations_anonymized.csv` / `.jsonl`: hashed IDs + redacted content.
- QA notes (`anonymization_QA.md`, `personal_identifier_scan.md`, `post_anonymization_scan.md`).

## Recommended Usage

1. **Internal research:** use `ai_conversations_combined.csv` + concept/marker files to explore Flowing Information Framework empirically.
2. **Presentation:** load `flow_lab_slides.md`, embed SVGs, and share narrative backed by data.
3. **External collaboration:** apply anonymization workflow, share anonymized datasets + slides + briefing outline.
4. **Further analysis:** expand meta marker tracking, perform narrative annotation, align with emotion cycle, etc.

## Data Refresh Routine

- Re-run flattening scripts (`scripts/flatten_chatgpt_export.py`, `scripts/flatten_sena_export.py`).
- Combine & summarise (`scripts/build_combined_conversations.py`; re-run concept extraction pipelines afterwards if needed).
- Rebuild visuals (`render_concept_timeline.py`, `render_flow_cycle.py`, `render_concept_network.py`).
- Update meta analysis (`extract_metacognition.py`, `build_case_study.py`).
- Regenerate anonymized dataset + QA (`perple_anonymize.py`, `scripts/build_other_ai_index.ps1`, `scan_anonymized.py`).

## Contact

- Maintainer: 최창우 (비노체) — use anonymized flow (`[NAME]`, `[PHONE]`, `[EMAIL]`) when distributing externally.
