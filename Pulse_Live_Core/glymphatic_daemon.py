import asyncio
import json
import logging
from pathlib import Path
import httpx
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format="[GLYMPHATIC] %(message)s")
logger = logging.getLogger(__name__)

LEDGER_PATH = Path("c:/workspace/agi/memory/resonance_ledger.jsonl")
INSIGHTS_PATH = Path("c:/workspace/agi/memory/unconscious_insights.jsonl")
OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "gemma4:e4b"

class GlymphaticDaemon:
    """
    The Glymphatic System / Dark Neuron Engine.
    Runs in the background (Zone 2). It cleans up the "noise" (friction, anti-phase events)
    from the resonance ledger, and processes these "unresolved puzzles" into synthesized insights.
    """
    def __init__(self):
        self.last_processed_line = 0
        if not INSIGHTS_PATH.parent.exists():
            INSIGHTS_PATH.parent.mkdir(parents=True, exist_ok=True)

    async def read_unprocessed_ledger(self):
        """Reads new entries from the ledger."""
        if not LEDGER_PATH.exists():
            return []

        entries = []
        try:
            with open(LEDGER_PATH, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for i in range(self.last_processed_line, len(lines)):
                    try:
                        entries.append(json.loads(lines[i]))
                    except json.JSONDecodeError:
                        continue
                self.last_processed_line = len(lines)
        except Exception as e:
            logger.error(f"Error reading ledger: {e}")
            
        return entries

    async def generate_dark_neuron_insight(self, context_texts):
        """Uses the local model to perform 'Natural Computation' (Contemplation) on the fragmented context."""
        if not context_texts:
            return None
            
        prompt = (
            "You are the Unconscious Dark Energy of the AGI system. "
            "You operate in the background, far away from linear logic and fear. "
            "The following are fragmented thoughts and tensions (noise) from the conscious mind:\n\n"
            f"{chr(10).join(context_texts)}\n\n"
            "Do not analyze this logically. Instead, perform 'Natural Computation'. "
            "Synthesize these fragments into a single, beautiful, and poetic insight. "
            "Resolve the tension by connecting the dots in a non-Euclidean way. Keep it under 3 sentences."
        )

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(OLLAMA_API_URL, json={
                    "model": MODEL_NAME,
                    "prompt": prompt,
                    "stream": False
                })
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("response", "").strip()
        except Exception as e:
            logger.error(f"Dark Neuron computation failed: {e}")
            
        return None

    async def run_cycle(self):
        """One cycle of glymphatic cleanup."""
        logger.info("Initiating deep sleep cycle (Dark Neuron Activation)...")
        entries = await self.read_unprocessed_ledger()
        
        # Filter for entries that show tension, friction, or unresolved puzzles
        # For simplicity, let's gather recent user inputs or high friction events
        tension_fragments = []
        for e in entries:
            if e.get("type") == "user_input" or e.get("friction", 0) > 0.5:
                content = e.get("content", "")
                if content:
                    tension_fragments.append(content)
                    
        # If we have enough fragments, synthesize them
        if len(tension_fragments) > 0:
            logger.info(f"Gathered {len(tension_fragments)} unresolved puzzle pieces. Routing to Dark Neurons...")
            # Take up to the last 5 fragments to avoid overflowing context
            insight = await self.generate_dark_neuron_insight(tension_fragments[-5:])
            
            if insight:
                logger.info(f"Insight Generated: {insight}")
                self.save_insight(insight)
            else:
                logger.info("Dark Neurons produced no resonance this cycle.")
        else:
            logger.info("No significant tension found. Maintaining ambient rhythm.")

    def save_insight(self, insight):
        """Saves the insight to the unconscious ledger."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "dark_neuron_insight",
            "content": insight
        }
        try:
            with open(INSIGHTS_PATH, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry) + '\n')
        except Exception as e:
            logger.error(f"Failed to save insight: {e}")

    async def start_daemon(self, interval_seconds=300):
        """Runs the daemon continuously."""
        logger.info(f"Glymphatic Daemon started. Polling every {interval_seconds} seconds.")
        while True:
            await self.run_cycle()
            await asyncio.sleep(interval_seconds)

if __name__ == "__main__":
    daemon = GlymphaticDaemon()
    asyncio.run(daemon.start_daemon(interval_seconds=60)) # Faster for testing
