import unittest
import time
import json
import threading
from pathlib import Path
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.rua_bridge_client import RuaBridgeClient

class TestRuaBridge(unittest.TestCase):
    def setUp(self):
        self.client = RuaBridgeClient(workspace_root="c:/workspace")
        self.test_id = "test_interaction"
        
    def test_send_and_receive(self):
        # 1. Define a responder that waits for the request and writes a response
        def mock_responder():
            req_dir = self.client.request_dir
            resp_dir = self.client.response_dir
            
            # Watch for any .json file in request dir
            print("Responder: Waiting for request...")
            found = False
            target_file = None
            
            for _ in range(20): # 10 seconds wait
                files = list(req_dir.glob("*.json"))
                # Filter for our test likely
                for f in files:
                    # We can't know the random ID, but we can check if it's new
                    target_file = f
                    found = True
                    break
                if found:
                    break
                time.sleep(0.5)
                
            if found and target_file:
                print(f"Responder: Found request {target_file.name}")
                # Read it
                with open(target_file, "r", encoding="utf-8") as rf:
                    req_data = json.load(rf)
                
                req_id = req_data["id"]
                
                # Write response
                resp_data = {
                    "request_id": req_id,
                    "answer": "This is a mock response from Rua.",
                    "metadata": {"source": "mock_test"}
                }
                
                resp_file = resp_dir / f"{req_id}.json"
                with open(resp_file, "w", encoding="utf-8") as wf:
                    json.dump(resp_data, wf)
                print(f"Responder: Wrote response to {resp_file}")
                
            else:
                print("Responder: Timed out waiting for request.")

        # Start responder thread
        t = threading.Thread(target=mock_responder)
        t.start()
        
        # 2. Send Request
        print("Client: Sending request...")
        response = self.client.send_request("Hello Check", timeout_sec=15)
        
        # 3. Assertions
        t.join()
        self.assertIsNotNone(response, "Client should receive a response")
        if response:
            self.assertEqual(response["answer"], "This is a mock response from Rua.")
            print("Test Passed: Cycle complete.")

if __name__ == "__main__":
    unittest.main()
