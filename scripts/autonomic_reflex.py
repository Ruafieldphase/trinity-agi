import json
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime
from workspace_root import get_workspace_root

# Configuration
WORKSPACE_ROOT = get_workspace_root()
EXPRESS_SCRIPT = WORKSPACE_ROOT / "scripts" / "express_resonance.py"
LOG_FILE = WORKSPACE_ROOT / "outputs" / "autonomic_reflex.log"

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")

def trigger_reflex():
    """
    Calls express_resonance.py to get the current 'feeling' and 'intuition',
    then executes a reflex action.
    """
    log("🧠 Autonomic Reflex Triggered...")
    
    try:
        # 1. Get Intuition from Resonance (Force check)
        cmd = ["python", str(EXPRESS_SCRIPT), "--json", "--force"]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode != 0:
            log(f"Error calling express_resonance: {result.stderr}")
            return

        log(f"DEBUG: STDOUT: {result.stdout}")
        log(f"DEBUG: STDERR: {result.stderr}")

        raw_output = result.stdout.strip()
        # Robust parsing: find first '{'
        json_start = raw_output.find('{')
        if json_start != -1:
            raw_output = raw_output[json_start:]
        
        try:
            data = json.loads(raw_output)
        except json.JSONDecodeError:
            log(f"Failed to parse JSON from resonance: {result.stdout}")
            return

        intuition = data.get("actionable_intuition", "NONE")
        urgency = data.get("urgency", "LOW")
        monologue = data.get("monologue", "...")
        
        log(f"❤️ Pulse: {intuition} ({urgency})")
        log(f"💭 Thought: {monologue}")

        # 2. Execute Reflex
        execute_reflex(intuition, urgency, monologue)

    except Exception as e:
        log(f"System Error: {e}")

def execute_reflex(intuition, urgency, monologue):
    """
    Executes the action corresponding to the intuition.
    """
    from core_slack_adapter import CoreSlackAdapter
    slack = CoreSlackAdapter()

    if intuition == "NONE":
        return

    # Reflex Map
    if intuition == "REST" or intuition == "FOLD_MEMORY":
        log("Action: Initiating Rest/Fold...")
        # TODO: Trigger actual folding logic (e.g., compress logs, clear cache)
        # For now, just log and maybe notify if urgent
        if urgency == "HIGH":
            slack.send_message(f"🛑 *Autonomic Reflex*\nI am overwhelmed. Initiating emergency folding.\n> _{monologue}_")

    elif intuition == "EXPLORE" or intuition == "CHECK_NEWS":
        log("Action: Triggering Zone 2 Walk (Exploration)...")
        slack.send_message(f"⚡ *Autonomic Reflex*\nI feel stagnant. I'm going for a walk.\n> _{monologue}_")
        
        # Call Zone 2 Walk
        try:
            walk_script = WORKSPACE_ROOT / "scripts" / "zone2_walk.py"
            cmd = ["python", str(walk_script)]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            
            if result.returncode == 0:
                # Parse output (robustly)
                raw = result.stdout.strip()
                json_start = raw.find('{')
                if json_start != -1:
                    walk_data = json.loads(raw[json_start:])
                    
                    observation = walk_data.get("observation", "I saw something.")
                    metaphor = walk_data.get("metaphor", "Nature.")
                    file_name = walk_data.get("file", "Unknown")
                    proposal = walk_data.get("proposal")
                    
                    if proposal:
                        log(f"Proposal generated: {proposal}")
                        # Enrich proposal with file info
                        proposal["file"] = file_name
                        proposal["observation"] = observation
                        
                        # Call propose_task.py
                        propose_script = WORKSPACE_ROOT / "scripts" / "propose_task.py"
                        cmd_propose = ["python", str(propose_script), json.dumps(proposal)]
                        subprocess.run(cmd_propose, capture_output=True, text=True, encoding='utf-8')
                    else:
                        # Just a walk
                        walk_msg = f"🌿 *Zone 2 Walk*\n> *File:* `{file_name}`\n> *Metaphor:* {metaphor}\n\n\"{observation}\""
                        slack.send_message(walk_msg)
                        log(f"Walk Result: {observation}")
            else:
                log(f"Zone 2 Walk failed: {result.stderr}")
                
        except Exception as e:
            log(f"Error during walk: {e}")
        
    elif intuition == "CHECK_MEMORY":
        log("Action: Checking Memory...")
        # TODO: Trigger memory scan
        
    elif intuition == "CONTINUE" or intuition == "OBSERVE":
        log("Action: Continuing Flow...")
        # No specific action needed, just maintain rhythm
        
    else:
        log(f"Action: Unknown intuition '{intuition}'. Logging only.")

if __name__ == "__main__":
    trigger_reflex()
