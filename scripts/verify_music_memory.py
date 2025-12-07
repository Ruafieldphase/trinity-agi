
import asyncio
import sys
from pathlib import Path

# Add workspace root to sys.path
workspace_root = Path(__file__).parent.parent
sys.path.append(str(workspace_root))

from fdo_agi_repo.rpa.trial_error_engine import TrialErrorEngine

async def verify_music_memory():
    print("🔍 Verifying Music Memory...")
    
    engine = TrialErrorEngine()
    
    # Ask for the best action for "play_music"
    # We pass dummy params, expecting them to be overridden by the "best experience"
    action = engine._select_action(
        task_name="play_music",
        params={"script_path": "wrong_script.ps1"}, # Dummy default
        state={"context": "user_request"}
    )
    
    print(f"   Selected Action: {action.name}")
    print(f"   Selected Params: {action.params}")
    
    expected_script = "c:\\workspace\\agi\\scripts\\play_adaptive_session.ps1"
    actual_script = action.params.get("script_path")
    
    if actual_script == expected_script:
        print("✅ SUCCESS: Correct script recalled!")
    else:
        print(f"❌ FAILURE: Expected {expected_script}, got {actual_script}")
        # Force fail if verification fails
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(verify_music_memory())
