"""
Clean Context Ledger by validating and fixing JSON lines
"""
import json
from pathlib import Path

# Actual location
ledger_path = Path("outputs/contexts/context_ledger.jsonl")
backup_path = ledger_path.with_suffix('.jsonl.backup')

if not ledger_path.exists():
    print(f"Ledger not found: {ledger_path}")
    exit(0)

print(f"Cleaning: {ledger_path}")

# Backup original
if backup_path.exists():
    backup_path.unlink()
ledger_path.rename(backup_path)
print(f"Backed up to: {backup_path}")

valid_lines = []
invalid_count = 0

# Read and validate each line
with open(backup_path, 'r', encoding='utf-8', errors='ignore') as f:
    for i, line in enumerate(f, 1):
        line = line.strip()
        if not line:
            continue
        try:
            # Try to parse as JSON
            obj = json.loads(line)
            # Re-serialize to clean format
            clean_line = json.dumps(obj, ensure_ascii=False)
            valid_lines.append(clean_line)
        except json.JSONDecodeError as e:
            print(f"Line {i} invalid: {e}")
            print(f"Content: {line[:100]}...")
            invalid_count += 1

# Write cleaned lines
with open(ledger_path, 'w', encoding='utf-8') as f:
    for line in valid_lines:
        f.write(line + '\n')

print(f"\nCleaning complete:")
print(f"  Valid lines: {len(valid_lines)}")
print(f"  Invalid lines removed: {invalid_count}")
print(f"  Cleaned file: {ledger_path}")
