import sys
import os
import json
import subprocess

ROUTER_SCRIPT = r"c:\workspace\agi\scripts\core_router.py"

def run_test(message, expected_system):
    print(f"\n🧪 Testing: '{message}' (Expect: {expected_system})")
    try:
        cmd = ["python", ROUTER_SCRIPT, message, "--json"]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode != 0:
            print(f"❌ Failed with code {result.returncode}")
            print(f"Stderr: {result.stderr}")
            return False

        try:
            data = json.loads(result.stdout)
            system = data.get("system")
            status = data.get("status")
            summary = data.get("summary")
            
            print(f"   System: {system}")
            print(f"   Status: {status}")
            print(f"   Summary: {summary[:100]}..." if summary else "   Summary: None")
            
            if system == expected_system and status == "success":
                print("✅ Pass")
                return True
            else:
                print(f"❌ Fail (System: {system}, Status: {status})")
                return False
                
        except json.JSONDecodeError:
            print(f"❌ JSON Decode Error. Output: {result.stdout}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    print("🚀 Verifying Core Router Bridge...")
    
    # 1. Core (Chat)
    if not run_test("안녕, 너 지금 어디에 있어?", "Core"):
        print("⚠️ Core test failed.")
        
    # 2. Resonance (Status)
    # Note: "상태" might trigger ChatOps (local) if I didn't disable it, but I modified route_to_resonance.
    # However, parse_intent maps "상태" to resonance.
    # Let's try "리듬 상태" to be sure it hits resonance.
    if not run_test("리듬 상태 어때?", "resonance"):
        print("⚠️ Resonance test failed.")
        
    # 3. Binoche_Observer (Goals)
    if not run_test("새로운 목표를 생성해줘", "Binoche_Observer"):
        print("⚠️ Binoche_Observer test failed.")

if __name__ == "__main__":
    main()
