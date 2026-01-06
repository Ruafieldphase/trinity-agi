"""
Simulate Code Failure & Patching (Phase 13.5)
============================================
1. Creates a file with a deliberate, repeatable bug.
2. Triggers an execution that logs the traceback.
3. Runs SelfOptimizer to detect and propose a patch.
"""

import sys
import os
import json
import logging
import traceback
from pathlib import Path

# Add root to sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

# Setup logging to a specific file for the analyst to find
log_path = WORKSPACE_ROOT / "arch_agent.log"
logging.basicConfig(
    filename=str(log_path),
    filemode='a',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("Simulator")

from agi_core.self_optimizer import SelfOptimizer

def create_buggy_file():
    target = WORKSPACE_ROOT / "agi_core" / "math_utils.py"
    code = """
def safe_divide(a, b):
    # 의도적인 버그: 0으로 나누기 예외 처리가 없음
    return a / b

if __name__ == "__main__":
    print(safe_divide(10, 0))
"""
    with open(target, "w", encoding="utf-8") as f:
        f.write(code)
    return target

def trigger_failure(file_path):
    print(f"🔥 Executing buggy file: {file_path.name}")
    try:
        # Run the buggy script
        import subprocess
        result = subprocess.run([sys.executable, str(file_path)], capture_output=True, text=True)
        
        if result.returncode != 0:
            # Manually inject the traceback into the log for scanning
            logger.error("Simulation Triggered Error:")
            logger.error(result.stderr)
            print("📝 Traceback written to arch_agent.log")
        else:
            print("❓ Execution unexpectedly succeeded.")
            
    except Exception:
        logger.error(traceback.format_exc())

def test_recursive_improvement():
    buggy_file = create_buggy_file()
    trigger_failure(buggy_file)
    
    print("\n🔍 Running Recursive Self-Improvement Analysis...")
    optimizer = SelfOptimizer(WORKSPACE_ROOT)
    patches = optimizer.run_recursive_code_improvement()
    
    if patches:
        print(f"✅ Found {len(patches)} potential improvement(s):")
        for i, patch in enumerate(patches, 1):
            print(f"\n--- Proposed Patch {i} ---")
            print(f"Target: {patch['target_file']}")
            print(f"Reason: {patch['reason']}")
            print(f"Original: \n{patch['original_snippet']}")
            print(f"Replacement: \n{patch['replacement_snippet']}")
            
            # Record it in a global patch proposal file for the user
            proposal_log = WORKSPACE_ROOT / "outputs" / "proposed_code_updates.json"
            with open(proposal_log, "w", encoding="utf-8") as f:
                json.dump(patches, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Full proposal saved to: {proposal_log}")
    else:
        print("❌ No patches generated. Check logs or LLM connection.")

if __name__ == "__main__":
    test_recursive_improvement()
