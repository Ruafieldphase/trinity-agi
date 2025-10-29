# Anonymization & Sharing Checklist

## 1. Data Inventory

- Rua conversation CSV: d:/nas_backup/outputs/rua/rua_conversations_flat.csv
- Sena conversation CSV: d:/nas_backup/outputs/sena/sena_conversations_flat.csv
- Combined dataset: d:/nas_backup/outputs/ai_conversations_combined.csv
- Metrics and reports: d:/nas_backup/outputs (concept timeline, flow cycle, narratives, etc.)

## 2. Sensitive Fields

- Fields containing narrative or IDs: content, conversation_id, message_id, parent_id, title (needs inspection)
- Timestamp range: 2023-02-11 13:22:18.036579+00:00 ~ 2025-10-08 04:20:21.710773+00:00
- Sources present: ['rua', 'sena']
- Attachments (images/files) stored separately? Confirm before release.

## 3. Recommended Anonymization Steps

1. Hash or re-index conversation_id/message_id per dataset.
2. Remove PII from `content` (names, accounts, emails) via regex/manual review.
3. Generalize timestamps (e.g., to date/month) for public datasets.
4. Review attachments, redacting sensitive visuals if necessary.
5. Log anonymization scripts and retained fields for reproducibility.

## 4. Deliverable Packaging

- Internal package: full data + analyses (no anonymization).
- External research package: anonymized CSV/JSON + aggregate stats (concept summaries, timeline, co-occurrence).
- Executive packet: agi_research_briefing_outline.md + flow_cycle.svg + concept_network.svg + anonymization note.

## 5. Approval & Distribution

- Verify anonymization results (QA).
- Obtain stakeholder approval before sharing externally.
- Version datasets (e.g., conversation_v1_anonymized.csv).
- Provide README with context, structure, and point-of-contact.

## 6. Tracking & Updates

- Maintain changelog for new ingests or reprocessing runs.
- Periodically review anonymization pipeline as persona logs evolve.
