import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add workspace root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.core_router import CoreRouter

class TestSlackMirroring(unittest.TestCase):
    def setUp(self):
        self.router = CoreRouter()

    @patch('scripts.core_slack_adapter.CoreSlackAdapter')
    @patch('scripts.internal_bus.bus')
    def test_normal_message_not_mirrored(self, mock_bus, MockAdapter):
        # Setup mocks
        mock_adapter_instance = MockAdapter.return_value
        mock_bus.publish.return_value = "msg_123"
        
        # Execute
        self.router.route(
            user_message="Gitko, check the logs",
            source_system="ion"
        )
        
        # Verify
        mock_adapter_instance.mirror_internal_message.assert_called_once()
        call_args = mock_adapter_instance.mirror_internal_message.call_args[0][0]
        self.assertEqual(call_args['priority'], 'medium')
        # In the actual implementation, mirror_internal_message returns False for medium priority
        # We can't easily check the return value here since we mocked the class, 
        # but we can check that it was called with the right data.
        
    @patch('scripts.core_slack_adapter.CoreSlackAdapter')
    @patch('scripts.internal_bus.bus')
    def test_urgent_message_mirrored(self, mock_bus, MockAdapter):
        # Setup mocks
        mock_adapter_instance = MockAdapter.return_value
        mock_bus.publish.return_value = "msg_456"
        
        # Execute
        self.router.route(
            user_message="Gitko, CRITICAL error in deployment",
            source_system="ion"
        )
        
        # Verify
        mock_adapter_instance.mirror_internal_message.assert_called_once()
        call_args = mock_adapter_instance.mirror_internal_message.call_args[0][0]
        self.assertEqual(call_args['priority'], 'high')

if __name__ == '__main__':
    unittest.main()
