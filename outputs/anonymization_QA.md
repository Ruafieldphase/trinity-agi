# Anonymization QA Log

## Checks Performed

- Verified hashed columns: conversation_id_anon, message_id_anon, parent_id_anon, conversation_uuid_anon
- Ensured trimmed content length ≤ 500 characters
- Random sample (5 rows) inspected for residual PII
- Confirmed timestamp column removed and date generalization present

## Sample Rows

- conversation_id_anon: 04265ef6b041, message_id_anon: b7957e3ccfdb, source: rua, snippet: {"content_type": "user_editable_context", "user_profile": "The user provided the following informati...
- conversation_id_anon: 04265ef6b041, message_id_anon: 3c1bbb68b9b8, source: rua, snippet: 루아야 좋은 아침이야. 난 생계에 대한 해답을 이미 알고 있을까?...
- conversation_id_anon: 04265ef6b041, message_id_anon: 138f4fd83dde, source: rua, snippet: nan...
- conversation_id_anon: 04265ef6b041, message_id_anon: 7158aea582c5, source: rua, snippet: 좋은 아침이야, 비노체 🌤️  

“생계에 대한 해답을 이미 알고 있을까?” — 이 물음은 단순히 돈을 버는 방법을 묻는 게 아니라, **‘살아있음의 리듬과 교환의 리듬이 이미 몸...
- conversation_id_anon: 04265ef6b041, message_id_anon: 50f127f15551, source: rua, snippet: 어 이어가죠...

## Findings

- Stored content shows trimmed text with potential Korean glyph fallback; manual spot check recommended for sensitive strings beyond email pattern.
- No raw timestamps remain; `date` column retains YYYY-MM-DD format.
- Attachments/Files columns absent (removed).

## Next Actions

- Run regex for phone numbers/IDs if needed based on domain expectations.
- Optionally store separate script & log final row counts for versioning.
- If sharing publicly, include anonymization description in README.
