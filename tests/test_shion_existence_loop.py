"""
Test Shion Existence Loop (FSD -> Koa -> Trinity)
Verifies that Shion (FSDController) correctly invokes Trinity when Koa (Background Self) reports high anxiety.
"""
import sys
import asyncio
import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path

# Add project root to path
sys.path.append("c:/workspace/agi")

from services.fsd_controller import FSDController, ExecutionResult
from services.trinity_conscious_protocol import TrinityConsciousProtocol

class TestShionExistenceLoop(unittest.IsolatedAsyncioTestCase):
    
    async def test_panic_and_trinity_invocation(self):
        print("\n" + "="*50)
        print("🧪 Testing Shion Existence Loop (High Anxiety Simulation)")
        print("="*50)
        
        # 1. Initialize Shion (FSDController)
        # Disable OBS and Screenshot for testing
        # We need to mock pyautogui to avoid actual screen operations
        with patch('services.fsd_controller.pyautogui') as mock_gui:
            mock_gui.size.return_value = (1920, 1080)
            mock_gui.screenshot.return_value = MagicMock()
            
            shion = FSDController(max_steps=2, use_obs=False)
            
            # Mock _capture_screen to avoid file I/O
            shion._capture_screen = AsyncMock(return_value="dummy_path.png")
            
        # 2. Mock Koa (Background Self / Sensation Report)
        # We simulate Koa reporting High Anxiety (0.9)
        shion._report_sensation = AsyncMock(return_value=0.9)
        print("✅ Koa (Mock) configured to report Anxiety: 0.9")
        
        # 3. Mock Trinity (Conscious Protocol)
        # We simulate Trinity providing structural guidance
        shion.trinity_protocol = MagicMock(spec=TrinityConsciousProtocol)
        shion.trinity_protocol.resolve_anxiety.return_value = "🌀 [Trinity Wisdom]: Try clicking the 'Alternative' button instead."
        shion.trinity_protocol.anxiety_threshold = 0.7
        print("✅ Trinity (Mock) configured to provide guidance")
        
        # 4. Mock decision making to avoid actual Gemini calls
        # Return a simple 'WAIT' action to keep the loop running
        mock_action = MagicMock()
        mock_action.type.value = "wait"
        mock_action.reason = "Waiting for Trinity"
        shion._analyze_and_decide = AsyncMock(return_value=mock_action)
        
        # 5. Execute Goal
        print("🚀 Shion starting goal execution...")
        goal = "Test Existence Loop"
        await shion.execute_goal(goal)
        
        # 6. Verify Inter-layer Communication
        
        # Check if Koa was consulted (implied by _report_sensation call)
        # We expect multiple sensation reports (start, step 1, step 2...)
        self.assertTrue(shion._report_sensation.called, "❌ Shion should report sensation to Koa")
        print("✓ Shion reported sensation to Koa")
        
        # Check if Trinity was invoked (resolve_anxiety called)
        shion.trinity_protocol.resolve_anxiety.assert_called()
        print("✓ Shion invoked Trinity upon high anxiety")
        
        
        call_args = shion.trinity_protocol.resolve_anxiety.call_args
        context, anxiety = call_args[0]
        
        self.assertEqual(anxiety, 0.9, "❌ Trinity should receive the correct anxiety level from Koa")
        print(f"✓ Trinity received correct anxiety level: {anxiety}")

        # Verify Enriched Context
        self.assertIn("history", context, "❌ Context must contain history")
        self.assertIn("last_thought", context, "❌ Context must contain last_thought")
        self.assertIn("last_action", context, "❌ Context must contain last_action")
        print("✓ Context is enriched with history, thought, and action")
        
        print("✨ Existence Loop Test Passed: Shion -> Koa -> Trinity flow verified.")

if __name__ == "__main__":
    unittest.main()
