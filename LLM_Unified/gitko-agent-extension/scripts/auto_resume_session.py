#!/usr/bin/env python3
"""
AGI Auto-Resume Script
Reads session state and automatically continues work from last checkpoint
"""
import json
import sys
import subprocess
from pathlib import Path
from typing import Dict, Any, List

STATE_FILE = Path(__file__).parent / ".gitko-session-state.json"


def load_session_state() -> Dict[str, Any]:
    """Load saved session state"""
    if not STATE_FILE.exists():
        print(f"❌ No session state found at {STATE_FILE}")
        sys.exit(1)
    
    with open(STATE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def print_banner(title: str):
    """Print colored banner"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60 + "\n")


def execute_next_actions(actions: List[Dict[str, Any]]):
    """Execute next actions from session state"""
    print("📋 Next Actions:")
    for action in actions:
        step = action.get('step', '?')
        desc = action.get('action', 'Unknown')
        cmd = action.get('command') or action.get('method')
        
        print(f"\n{step}. {desc}")
        if cmd:
            print(f"   → {cmd}")


def check_extension_status():
    """Check if VS Code extension is installed"""
    print("\n🔍 Checking VS Code extension status...")
    try:
        result = subprocess.run(
            ['code', '--list-extensions'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if 'gitko' in result.stdout.lower():
            print("✅ Gitko extension is installed")
            return True
        else:
            print("❌ Gitko extension NOT installed")
            return False
    except Exception as e:
        print(f"⚠️  Cannot check extensions: {e}")
        return None


def check_test_server():
    """Check if test server is still running"""
    import requests
    print("\n🔍 Checking test server...")
    try:
        resp = requests.get("http://localhost:8091/api/health", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            queue_size = data.get('queue_size', 0)
            print(f"✅ Test server running (queue: {queue_size} tasks)")
            return True
        else:
            print(f"❌ Test server returned {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ Test server not reachable: {e}")
        return False


def run_integration_tests():
    """Run integration tests"""
    print("\n🧪 Running integration tests...")
    test_script = Path(__file__).parent / "test_integration_simple.py"
    
    if not test_script.exists():
        print(f"❌ Test script not found: {test_script}")
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, str(test_script)],
            timeout=120
        )
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return False


def main():
    print_banner("🤖 AGI Auto-Resume: Integration Test Session")
    
    # Load session state
    state = load_session_state()
    
    print(f"📂 Session: {state['session_id']}")
    print(f"🎯 Phase: {state['phase']}")
    print(f"📅 Last Update: {state['timestamp']}")
    
    current_task = state.get('current_task', {})
    print(f"\n🔧 Current Task: {current_task.get('description', 'N/A')}")
    print(f"   Status: {current_task.get('status', 'unknown')}")
    
    blockers = current_task.get('blockers', [])
    if blockers:
        print(f"\n🚧 Blockers:")
        for blocker in blockers:
            print(f"   - {blocker}")
    
    # Show next actions
    next_actions = current_task.get('next_actions', [])
    if next_actions:
        execute_next_actions(next_actions)
    
    # Auto-diagnostic checks
    print_banner("🔍 Auto-Diagnostic Checks")
    
    server_ok = check_test_server()
    ext_installed = check_extension_status()
    
    # Provide guidance
    print_banner("📝 Recommended Next Steps")
    
    if not server_ok:
        print("❌ Test server not running")
        print("   → Start it: python task_queue_server.py --port 8091")
    
    if ext_installed is False:
        print("❌ Extension not installed")
        print("   → Package: npm run compile && vsce package")
        print("   → Install: code --install-extension gitko-agent-extension-0.1.0.vsix")
        print("   → Reload: Developer: Reload Window (Ctrl+Shift+P)")
    elif ext_installed is True:
        print("✅ Extension installed - check if HTTP Poller is running")
        print("   → Open Output channel: View → Output → 'Gitko HTTP Poller'")
        print("   → If not running, reload VS Code: Developer: Reload Window")
    
    if server_ok and ext_installed:
        print("\n✨ All systems ready - running integration tests...")
        success = run_integration_tests()
        if success:
            print("\n✅ Integration tests PASSED")
            return 0
        else:
            print("\n⚠️  Integration tests had issues - check output above")
            return 1
    else:
        print("\n⚠️  Prerequisites not met - complete setup steps above first")
        return 2


if __name__ == '__main__':
    sys.exit(main())
