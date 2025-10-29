Sena Conversation Processing
============================

Flattened data saved under `d:\nas_backup\outputs\sena`:
- `sena_conversations_flat.csv`
- `sena_conversations_flat.jsonl`

Snapshot:
- Conversations processed: 119
- Messages total: 2,296 (human 1,155 / assistant 1,141)

Usage:
1. Drop new conversation export JSON into `D:\nas_backup\ai_binoche_conversation_origin\sena\conversations.json` (overwrite or new path).
2. Run `python d:\nas_backup\flatten_sena_conversations.py` (script stored in commands history below) to regenerate CSV/JSONL.
3. Resulting files can be ingested with `lumen_realdata_template.py` or other flow-analysis utilities.

Note: current script expects Claude-export format with `chat_messages`[]. Adjust if schema changes.
