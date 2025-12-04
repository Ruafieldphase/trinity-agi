import json
from datetime import datetime
from pathlib import Path

# Path to resonance ledger
ledger_path = Path("c:/workspace/agi/fdo_agi_repo/memory/resonance_ledger.jsonl")

# Create a test message targeting Sena
test_message = {
    "timestamp": datetime.now().isoformat(),
    "type": "external_question",
    "source": "sena_test_trigger",
    "message": "Hello System, this is a test message to verify the Sena bridge.",
    "target": "sian",
    "vector": [0.5, 0.5, 0.5, 0.5, 0.5]
}

# Append to ledger
try:
    with open(ledger_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(test_message, ensure_ascii=False) + "\n")
    print("✅ Test message appended to resonance_ledger.jsonl")
except Exception as e:
    print(f"❌ Failed to append message: {e}")
