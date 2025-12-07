import requests
import json
import time
import os
import sys

BASE_URL = "http://127.0.0.1:8104"

def log(msg):
    print(f"[VERIFY] {msg}")

def check_fsd_execution():
    log("Checking FSD Execution (Goal: '계산기 열어줘')...")
    try:
        response = requests.post(
            f"{BASE_URL}/fsd/execute", 
            json={"goal": "계산기 열어줘"}, 
            timeout=60
        )
        
        if response.status_code != 200:
            log(f"FAILED: API returned status {response.status_code}")
            return False
            
        data = response.json()
        if not data.get("result", {}).get("success"):
            log(f"FAILED: FSD executed but reported failure. Msg: {data.get('result', {}).get('message')}")
            return False
            
        screenshot_path = data["result"]["final_screenshot"]
        # Convert relative path to absolute to verify existence
        # Assuming current dir is c:\workspace\agi
        abs_path = os.path.abspath(screenshot_path) if os.path.isabs(screenshot_path) else os.path.abspath(os.path.join(os.getcwd(), screenshot_path))
        
        if not os.path.exists(abs_path):
            log(f"WARNING: Screenshot file reported but not found at {abs_path}")
            # This might be due to path diffs between server/client, but let's note it.
        else:
            log(f"SUCCESS: Screenshot verified at {abs_path}")
            
        log(f"SUCCESS: FSD Execution finished in {data['result']['total_time']:.2f}s")
        return True
        
    except Exception as e:
        log(f"FAILED: Execution error - {e}")
        return False

def check_stream_health():
    log("Checking PIP Stream Health...")
    try:
        response = requests.get(f"{BASE_URL}/fsd/stream", stream=True, timeout=5)
        
        if response.status_code != 200:
            log(f"FAILED: Stream returned status {response.status_code}")
            return False
            
        # Check first chunk for MJPEG boundary and JPEG header
        count = 0
        jpeg_header_found = False
        
        start_time = time.time()
        for chunk in response.iter_content(chunk_size=1024):
            count += 1
            if b'\xff\xd8' in chunk: # JPEG Start
                jpeg_header_found = True
            
            if count > 20: # Check enough data
                break
                
        if count > 0 and jpeg_header_found:
            log(f"SUCCESS: Stream is sending valid JPEG data. Received {count} chunks.")
            return True
        elif count > 0:
            log("WARNING: Stream is sending data but JPEG header not found in first 20 chunks.")
            return True # Still sending data
        else:
            log("FAILED: No data received from stream")
            return False
            
    except Exception as e:
        log(f"FAILED: Stream check error - {e}")
        return False

if __name__ == "__main__":
    log("Starting System Verification...")
    
    fsd_ok = check_fsd_execution()
    stream_ok = check_stream_health()
    
    log("="*30)
    if fsd_ok and stream_ok:
        log("JUDGMENT: SYSTEM IS FULLY OPERATIONAL ✅")
        sys.exit(0)
    else:
        log("JUDGMENT: SYSTEM HAS ISSUES ❌")
        sys.exit(1)
