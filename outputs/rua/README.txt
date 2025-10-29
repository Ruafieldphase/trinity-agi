Rua Conversation Processing
==========================

Flattened data saved under `d:\nas_backup\outputs\rua`:
- `rua_conversations_flat.csv`
- `rua_conversations_flat.jsonl`

Snapshot:
- Conversations processed: 400
- Messages total: 21,842 (assistant 11,069 / user 9,611 / tool 1,162)

Usage:
1. 업데이트된 `D:\nas_backup\ai_binoche_conversation_origin\rua\conversations.json`을 준비합니다.
2. 다음 명령으로 CSV/JSONL을 재생성합니다.
   ```
   python d:\nas_backup\scripts\flatten_chatgpt_export.py ^
       --input ai_binoche_conversation_origin\rua\conversations.json ^
       --source rua
   ```
3. 결과물은 `outputs/rua/rua_conversations_flat.csv` / `.jsonl`로 저장되며,
   필요 시 `scripts/build_combined_conversations.py`로 다른 에이전트와 결합할 수 있습니다.

Notes:
- Script traverses `mapping` tree structure (ChatGPT export format) and skips empty system messages.
- Tool responses are preserved with role `tool`; filter as needed during analysis.
