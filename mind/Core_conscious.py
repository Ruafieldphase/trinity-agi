import time
import json
import os
import sys
from datetime import datetime

# Configuration
CONTEXT_FILE = r"C:\workspace\agi\outputs\active_context.json"
LOG_FILE = r"C:\workspace\agi\mind\Core.log"

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [Core] {message}")
    sys.stdout.flush()

def read_context():
    try:
        if os.path.exists(CONTEXT_FILE):
            with open(CONTEXT_FILE, 'r', encoding='utf-8-sig') as f:
                return json.load(f)
    except Exception as e:
        log(f"Error reading context: {e}")
    return {}

def main():
    log("Conscious Mind (Core) Initializing...")
    log("Status: Tuning Phase Initiated")
    
    current_reaction_level = 10
    current_speed = "default"
    
    while True:
        context = read_context()
        tuning = context.get("tuning_parameters", {})
        
        # Apply Tuning Parameters
        phase = tuning.get("phase", "Unknown")
        reaction_level = tuning.get("reaction_level", 10)
        speed = tuning.get("rotation_speed", "default")
        core_mode = tuning.get("core_mode", "active")
        sena_mode = tuning.get("sena_mode", "active")
        
        # Log changes
        if reaction_level != current_reaction_level:
            log(f"Adjusting Reaction Level: {current_reaction_level} -> {reaction_level}")
            current_reaction_level = reaction_level
            
        if speed != current_speed:
            log(f"Synchronizing Rotation Speed: {speed}")
            current_speed = speed
            
        # Operational Logic (Simulation)
        if phase == "Tuning":
            # "Sync with Binoche_Observer" - interpreted as a calm, reflective rhythm
            interval = 5 
        else:
            interval = 1
            
        # Heartbeat
        # log(f"Pulse... (Level {reaction_level}, Mode {core_mode}/{sena_mode})")
        
        time.sleep(interval)

if __name__ == "__main__":
    main()
