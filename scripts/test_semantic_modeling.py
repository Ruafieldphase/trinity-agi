import os
import sys
import asyncio
import logging

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.fsd_controller import FSDController, ExecutionResult

async def test_semantic_flow():
    logging.basicConfig(level=logging.INFO)
    controller = FSDController()
    
    print("--- Testing Autonomous Semantic Modeling ---")
    print("Goal: 'Generate a 3-story RC office building via Direct Bridge'")
    print("Pre-requisite: Blender must be running with blender_connector.py listener.")
    
    goal = "Generate a 3-story RC office building via Direct Bridge"
    
    # Run the controller
    # We use a mock sensation to avoid HTTP errors if background system isn't running
    result = await controller.execute_goal(goal)
    
    print(f"\nSimulation Result: {result.status.upper()}")
    print(f"Message: {result.message}")
    print(f"Total Time: {result.total_time:.2f}s")
    
    if result.status == "success":
        print("\n✅ Semantic Modeling successful!")
    else:
        print("\n❌ Semantic Modeling failed. Did you forget to start Blender listener?")

if __name__ == "__main__":
    asyncio.run(test_semantic_flow())
