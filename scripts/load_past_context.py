import json
import argparse
from pathlib import Path
from datetime import datetime

def load_past_context(target_date: str):
    """
    Reconstructs the context of a past date from memory artifacts.
    """
    journal_path = Path("fdo_agi_repo/memory/daily_journal.md")
    invariants_path = Path("fdo_agi_repo/memory/conversation_history_invariants.json")
    
    context = {
        "date": target_date,
        "narrative": "No narrative found.",
        "active_invariants": []
    }
    
    # 1. Load Narrative
    if journal_path.exists():
        with open(journal_path, "r", encoding="utf-8") as f:
            content = f.read()
            # Simple parsing: look for header matching date
            # Assuming format: # YYYY-MM-DD Narrative Consolidation
            if f"# {target_date}" in content:
                # Extract section (rough implementation)
                parts = content.split(f"# {target_date}")
                if len(parts) > 1:
                    section = parts[1].split("\n# ")[0] # Read until next header
                    context["narrative"] = section.strip()
    
    # 2. Load Invariants active at that time
    if invariants_path.exists():
        try:
            with open(invariants_path, "r", encoding="utf-8") as f:
                invariants = json.load(f)
                
            target_dt = datetime.strptime(target_date, "%Y-%m-%d")
            
            for inv in invariants:
                ts = inv.get("timestamp", "")
                if ts:
                    # Parse ISO format
                    try:
                        inv_dt = datetime.fromisoformat(ts).date()
                        # Include if created on or before target date
                        if inv_dt <= target_dt.date():
                            context["active_invariants"].append(inv)
                    except ValueError:
                        continue
        except json.JSONDecodeError:
            pass
            
    return context

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load past context for simulation.")
    parser.add_argument("--date", required=True, help="Target date (YYYY-MM-DD)")
    
    args = parser.parse_args()
    
    ctx = load_past_context(args.date)
    
    print(json.dumps(ctx, ensure_ascii=False, indent=2))
