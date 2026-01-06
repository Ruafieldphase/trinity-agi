
import asyncio
import sys
from pathlib import Path
from workspace_root import get_workspace_root

# Add workspace root to sys.path
workspace_root = get_workspace_root()
sys.path.append(str(workspace_root))

from fdo_agi_repo.rpa.trial_error_engine import TrialErrorEngine, Action, Experience

async def train_music_memory():
    print("🧠 Training Music Memory...")
    
    engine = TrialErrorEngine()
    
    # Define the "correct" way to play music
    correct_action = Action(
        name="play_music",
        params={
            "script_path": "c:\\workspace\\agi\\scripts\\play_adaptive_session.ps1",
            "method": "adaptive_windowless",
            "keywords": "Resonance,Flow,Dawn"
        },
        description="Play adaptive music using windowless .NET player"
    )
    
    # Create a synthetic experience with high reward
    experience = Experience(
        state={"context": "user_request", "intent": "restore_music"},
        action=correct_action,
        reward=1.0,  # High reward to ensure it's chosen
        next_state={"status": "success", "user_feedback": "positive"}
    )
    
    # Save to memory
    await engine._save_experience(experience)
    print(f"✅ Memory seeded: {experience.trial_id}")
    print(f"   Action: {correct_action.name}")
    print(f"   Params: {correct_action.params}")

if __name__ == "__main__":
    asyncio.run(train_music_memory())
