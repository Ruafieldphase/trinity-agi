
import time
import json
import logging
import subprocess
from pathlib import Path
from datetime import datetime

# Configuration
WORKSPACE_ROOT = Path(__file__).parent.parent
OUTPUTS_DIR = WORKSPACE_ROOT / "outputs"
THOUGHT_STREAM_FILE = OUTPUTS_DIR / "thought_stream_latest.json"
LOG_FILE = WORKSPACE_ROOT / "logs" / "ari_automator.log"

# Setup Logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ARI_Automator")

def load_thought_stream():
    try:
        if THOUGHT_STREAM_FILE.exists():
            with open(THOUGHT_STREAM_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load thought stream: {e}")
    return {}

def trigger_unconscious_learning(trigger_reason):
    """
    ARI Sub-layer task: Run learning without disturbing Shion.
    """
    logger.info(f"🌀 ARI Triggered: {trigger_reason}. Starting background learning...")
    
    try:
        # Run learn_from_conversation_history.py
        # This is the "Meaning Reconstruction" loop
        result = subprocess.run(
            ["python", "scripts/learn_from_conversation_history.py"],
            cwd=WORKSPACE_ROOT,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info("✅ ARI Learning Complete.")
            # We could update a separate 'ari_insight.json' here
        else:
            logger.error(f"❌ ARI Learning Failed: {result.stderr}")
            
    except Exception as e:
        logger.error(f"CRITICAL ARI ERROR: {e}")

def main():
    logger.info("ARI Automator Started (ASI Transition Layer)")
    
    last_processed_timestamp = ""
    
    while True:
        try:
            thought = load_thought_stream()
            timestamp = thought.get("timestamp", "")
            
            # Check if this is a new thought
            if timestamp != last_processed_timestamp:
                decision = thought.get("decision", "")
                feeling = thought.get("feeling", {}).get("tag", "")
                
                # ARI Trigger Conditions (Offloading interpretation from Shion)
                # If Shion says "explore" or "stabilize", ARI takes over the heavy lifting of memory sorting
                if decision == "explore" or feeling == "contrast":
                    trigger_unconscious_learning(f"Decision: {decision}, Feeling: {feeling}")
                
                last_processed_timestamp = timestamp
            
            time.sleep(10) # Check every 10 seconds
            
        except Exception as e:
            logger.error(f"Loop error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
