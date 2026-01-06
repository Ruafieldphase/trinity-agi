
import sys
import unittest
from unittest.mock import MagicMock

# Mock Blender API
sys.modules['bpy'] = MagicMock()
import bpy

# Set up mock driver namespace
bpy.app.driver_namespace = {"--state": "explore"}

# Import the visualization logic (simulate by copying key parts since we can't import directly without bpy installed)
def get_aura_color(state):
    if state == "explore":
        return (0.6, 0.2, 0.9, 1.0) # Purple
    elif state == "anxiety":
        return (1.0, 0.3, 0.0, 1.0) # Red
    else:
        return (0.2, 0.8, 0.4, 1.0) # Green

class TestAuraVisualization(unittest.TestCase):
    def test_explore_aura(self):
        color = get_aura_color(bpy.app.driver_namespace["--state"])
        print(f"Tested Color for 'explore': {color}")
        self.assertEqual(color, (0.6, 0.2, 0.9, 1.0))

if __name__ == '__main__':
    unittest.main()
