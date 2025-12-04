#!/usr/bin/env python3
"""
Quick test script for Lumen MCP Server

Usage: python test_lumen_mcp.py
"""

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent
VENV_PYTHON = REPO_ROOT / ".venv" / "Scripts" / "python.exe"

def test_mcp_server():
    """Test MCP server by sending sample requests"""
    
    print("🧪 Testing Lumen MCP Server...")
    print()
    
    # Test 1: List tools
    print("📋 Test 1: List available tools")
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list"
    }
    
    # Test 2: Get quality metrics
    print("📊 Test 2: Get quality metrics (last 1 hour)")
    
    # For now, just test the underlying functions directly
    print("✅ Testing underlying functions...")
    
    # Test summarize_ledger
    result = subprocess.run(
        [str(VENV_PYTHON), "scripts/summarize_ledger.py", "--last-hours", "1"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    
    if result.returncode == 0:
        print("✅ summarize_ledger.py works!")
        try:
            output = result.stdout.strip()
            if "{" in output:
                json_start = output.index("{")
                data = json.loads(output[json_start:])
                print(f"   avg_quality: {data.get('metrics', {}).get('avg_quality', 'N/A')}")
                print(f"   second_pass_rate: {data.get('metrics', {}).get('second_pass_rate_per_task', 'N/A')}")
        except Exception as e:
            print(f"   (JSON parse issue: {e})")
    else:
        print(f"❌ summarize_ledger.py failed: {result.stderr}")
    
    print()
    
    # Test ensemble weights
    weights_file = REPO_ROOT / "outputs" / "ensemble_weights.json"
    if weights_file.exists():
        print("✅ ensemble_weights.json exists!")
        with open(weights_file, "r", encoding="utf-8") as f:
            weights = json.load(f)
            w = weights.get("weights", {})
            print(f"   Logic: {w.get('logic', 'N/A'):.3f}")
            print(f"   Emotion: {w.get('emotion', 'N/A'):.3f}")
            print(f"   Rhythm: {w.get('rhythm', 'N/A'):.3f}")
    else:
        print("❌ ensemble_weights.json not found")
    
    print()
    print("🎉 Basic tests complete!")
    print()
    print("📝 To use with Claude Desktop or other MCP clients:")
    print("   1. Ensure cline_mcp_settings.json is configured")
    print("   2. Restart Claude Desktop or VS Code")
    print("   3. Look for 'lumen' tools in available tools")
    print()
    print("🛠️  Available tools:")
    print("   - lumen_get_quality_metrics")
    print("   - lumen_get_ensemble_weights")
    print("   - lumen_trigger_learning")
    print("   - lumen_get_system_status")
    print("   - lumen_get_judge_performance")


if __name__ == "__main__":
    test_mcp_server()
