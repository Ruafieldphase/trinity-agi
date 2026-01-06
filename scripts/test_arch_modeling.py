import asyncio
import os
import sys
import logging

# Add workspace root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.fsd_controller import FSDController

async def run_arch_modeling_test():
    logging.basicConfig(level=logging.INFO)
    
    # Initialize FSD Controller with the newly integrated strategy
    # Note: Use verify_mode to avoid actual mouse movement during the first integration test if needed
    controller = FSDController(max_steps=5, verify_mode=True)
    
    # Set the goal that triggers the ArchFSDStrategy
    goal = "Fold the elevation references and extrude the wall boundaries using Constant C."
    
    print(f"\n🚀 Starting Architectural Modeling Simulation...")
    print(f"Goal: {goal}")
    print("-" * 50)
    
    result = await controller.execute_goal(goal)
    
    print("\n" + "=" * 50)
    print(f"Simulation Result: {'SUCCESS' if result.success else 'FAILED'}")
    print(f"Message: {result.message}")
    print(f"Total Steps: {len(result.steps)}")
    print(f"Total Time: {result.total_time:.2f}s")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(run_arch_modeling_test())
