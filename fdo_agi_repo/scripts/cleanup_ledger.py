# cleanup_ledger.py
import os

# Define paths
repo_root = os.path.dirname(os.path.dirname(__file__))
ledger_path = os.path.join(repo_root, "memory", "resonance_ledger.jsonl")
backup_path = os.path.join(repo_root, "memory", "resonance_ledger.backup.jsonl")

# Define how many recent lines to keep
LINES_TO_KEEP = 500

def main():
    if not os.path.exists(ledger_path):
        print(f"Ledger file not found at {ledger_path}. Nothing to do.")
        return

    print(f"Reading ledger: {ledger_path}")
    with open(ledger_path, "r", encoding="utf-8") as f:
        all_lines = f.readlines()

    total_lines = len(all_lines)
    print(f"Total lines found: {total_lines}")

    if total_lines <= LINES_TO_KEEP:
        print(f"Ledger has fewer than {LINES_TO_KEEP} lines. No cleanup needed.")
        return

    # Create a backup
    print(f"Backing up original ledger to: {backup_path}")
    with open(backup_path, "w", encoding="utf-8") as f_backup:
        f_backup.writelines(all_lines)

    # Keep the last N lines
    lines_to_keep = all_lines[-LINES_TO_KEEP:]
    
    # Write the cleaned lines back
    print(f"Writing last {len(lines_to_keep)} lines back to the ledger.")
    with open(ledger_path, "w", encoding="utf-8") as f_main:
        f_main.writelines(lines_to_keep)

    print(f"Cleanup complete. {total_lines - len(lines_to_keep)} old lines removed.")

if __name__ == "__main__":
    main()
