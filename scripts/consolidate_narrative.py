import json
import os
import sys
import google.generativeai as genai
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini
API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    # Try to find it in .env manually if load_dotenv fails or file is in parent
    try:
        with open(".env", "r") as f:
            for line in f:
                if line.startswith("GEMINI_API_KEY="):
                    API_KEY = line.strip().split("=")[1]
                    break
                elif line.startswith("GOOGLE_API_KEY="):
                    API_KEY = line.strip().split("=")[1]
                    break
    except:
        pass

if not API_KEY:
    print("❌ GEMINI_API_KEY or GOOGLE_API_KEY not found in environment or .env file.")
    sys.exit(1)

genai.configure(api_key=API_KEY)

def consolidate_narrative():
    """
    Reads today's resonance ledger and consolidates it into a narrative in daily_journal.md
    """
    ledger_path = Path("fdo_agi_repo/memory/resonance_ledger.jsonl")
    journal_path = Path("fdo_agi_repo/memory/daily_journal.md")
    
    if not ledger_path.exists():
        print("⚠️ No ledger found.")
        return

    # Filter for today's entries (Conversation only)
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_entries = []
    
    with open(ledger_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line)
                # Handle various timestamp formats
                ts = entry.get("timestamp")
                if ts is None:
                    ts = ""
                ts = str(ts)
                
                if ts.startswith(today_str):
                    # Filter for relevant types only
                    msg_type = entry.get("type", "")
                    if msg_type in ["user_message", "autonomous_response", "agent_response", "external_question", "gemini_conversation"]:
                        today_entries.append(entry)
            except json.JSONDecodeError:
                continue
    
    if not today_entries:
        print(f"⚠️ No relevant entries found for today ({today_str}).")
        return

    # Limit to last 100 entries to avoid rate limits
    if len(today_entries) > 100:
        today_entries = today_entries[-100:]

    print(f"📚 Found {len(today_entries)} relevant entries for today. Consolidating...")

    # Generate Narrative using Gemini
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    prompt = f"""
    Analyze the following log of AI-User interactions for today ({today_str}).
    
    Logs:
    {json.dumps(today_entries, ensure_ascii=False, indent=2)}
    
    Task: Write a "Daily Narrative" summary.
    Format: Markdown.
    
    Structure:
    1. **Theme**: One sentence summary of the day's core theme.
    2. **Key Events**: Bullet points of major actions or decisions.
    3. **Learnings**: What did the system learn? (e.g., corrected definitions, new concepts).
    4. **Narrative**: A short paragraph telling the story of the session from the AI's perspective (First person "I").
    
    Language: Korean (Natural, reflective tone).
    """
    
    try:
        response = model.generate_content(prompt)
        narrative = response.text
        
        # Append to Journal
        with open(journal_path, "a", encoding="utf-8") as f:
            f.write(f"\n\n# {today_str} Narrative Consolidation\n\n")
            f.write(narrative)
            f.write("\n\n---\n")
            
        print("✅ Narrative Consolidated to daily_journal.md")
        
    except Exception as e:
        print(f"❌ Failed to generate narrative: {e}")

if __name__ == "__main__":
    consolidate_narrative()
