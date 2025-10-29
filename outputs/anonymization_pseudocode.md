# Anonymization Script Pseudo-code

```python
import pandas as pd
import hashlib
from pathlib import Path

source_path = Path('ai_conversations_combined.csv')
df = pd.read_csv(source_path)

# 1. Hash identifiers
for col in ['conversation_id', 'message_id', 'parent_id']:
    if col in df.columns:
        df[col] = df[col].fillna("").apply(lambda x: hashlib.sha256(str(x).encode()).hexdigest()[:12])

# 2. Remove or redact PII in content
pattern = r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'
df['content_clean'] = df['content'].fillna('').str.replace(pattern, '[EMAIL]', regex=True)
df['content_trimmed'] = df['content_clean'].str.slice(0, 500)

# 3. Generalize timestamps
df['date'] = pd.to_datetime(df['timestamp'], errors='coerce').dt.date
df = df.drop(columns=['timestamp'], errors='ignore')

# 4. Drop sensitive columns if required
df = df.drop(columns=['content', 'attachments', 'files'], errors='ignore')

# 5. Save anonymized outputs
df.to_csv('ai_conversations_anonymized.csv', index=False)
```
