#!/usr/bin/env python3
"""
Lumen MCP Server - Model Context Protocol interface for Lumen AGI System

Provides tools for external AI systems to interact with Lumen's:
- Quality metrics (resonance ledger analysis)
- Ensemble weights (Phase 6l learned parameters)
- Learning execution (trigger Phase 6l)
- System status (schedulers, health)

Usage:
    python lumen_mcp_server.py
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

# MCP SDK import (install: pip install mcp)
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    print("❌ MCP SDK not installed. Run: pip install mcp", file=sys.stderr)
    sys.exit(1)

# Project paths
REPO_ROOT = Path(__file__).parent
VENV_PYTHON = REPO_ROOT / ".venv" / "Scripts" / "python.exe"
OUTPUTS_DIR = REPO_ROOT / "outputs"
MEMORY_DIR = REPO_ROOT / "memory"

# Initialize MCP server
app = Server("lumen-agi")


# ===== Helper Functions =====

def run_python_script(script_path: str, *args: str) -> dict[str, Any]:
    """Run a Python script in the venv and return JSON output"""
    cmd = [str(VENV_PYTHON), script_path, *args]
    result = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    
    if result.returncode != 0:
        return {
            "ok": False,
            "error": result.stderr,
            "exit_code": result.returncode
        }
    
    # Try to parse JSON output
    try:
        # Find JSON in output (might have other text)
        output = result.stdout.strip()
        if "{" in output:
            json_start = output.index("{")
            json_str = output[json_start:]
            return json.loads(json_str)
        return {"ok": True, "output": output}
    except json.JSONDecodeError:
        return {"ok": True, "output": result.stdout}


def read_json_file(filepath: Path) -> dict[str, Any]:
    """Read and parse a JSON file"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return {"ok": True, "data": json.load(f)}
    except FileNotFoundError:
        return {"ok": False, "error": f"File not found: {filepath}"}
    except json.JSONDecodeError as e:
        return {"ok": False, "error": f"Invalid JSON: {e}"}


def count_ledger_events() -> int:
    """Count total events in resonance ledger"""
    ledger_path = MEMORY_DIR / "resonance_ledger.jsonl"
    try:
        with open(ledger_path, "r", encoding="utf-8") as f:
            return sum(1 for _ in f)
    except FileNotFoundError:
        return 0


# ===== MCP Tools =====

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available Lumen tools"""
    return [
        Tool(
            name="lumen_get_quality_metrics",
            description="Get AGI quality metrics (avg_quality, second_pass_rate, confidence) from resonance ledger",
            inputSchema={
                "type": "object",
                "properties": {
                    "hours": {
                        "type": "number",
                        "description": "Time window in hours (default: 24)",
                        "default": 24
                    }
                }
            }
        ),
        Tool(
            name="lumen_get_ensemble_weights",
            description="Get current Phase 6l ensemble weights (Logic/Emotion/Rhythm judges)",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="lumen_trigger_learning",
            description="Trigger Phase 6l online learning (gradient descent weight adjustment)",
            inputSchema={
                "type": "object",
                "properties": {
                    "window_hours": {
                        "type": "number",
                        "description": "Learning window in hours (default: 24)",
                        "default": 24
                    },
                    "learning_rate": {
                        "type": "number",
                        "description": "Gradient descent learning rate (default: 0.01)",
                        "default": 0.01
                    }
                }
            }
        ),
        Tool(
            name="lumen_get_system_status",
            description="Get Lumen system status (ledger size, files, health)",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="lumen_get_judge_performance",
            description="Get detailed judge performance metrics (accuracy, confidence, calibration)",
            inputSchema={
                "type": "object",
                "properties": {
                    "hours": {
                        "type": "number",
                        "description": "Time window in hours (default: 24)",
                        "default": 24
                    }
                }
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Execute a Lumen tool"""
    
    if name == "lumen_get_quality_metrics":
        hours = arguments.get("hours", 24)
        result = run_python_script(
            "scripts/summarize_ledger.py",
            "--last-hours", str(hours)
        )
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "lumen_get_ensemble_weights":
        weights_file = OUTPUTS_DIR / "ensemble_weights.json"
        result = read_json_file(weights_file)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "lumen_trigger_learning":
        window_hours = arguments.get("window_hours", 24)
        learning_rate = arguments.get("learning_rate", 0.01)
        result = run_python_script(
            "scripts/rune/binoche_online_learner.py",
            "--window-hours", str(window_hours),
            "--learning-rate", str(learning_rate)
        )
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "lumen_get_system_status":
        status = {
            "ok": True,
            "system": "Lumen AGI",
            "ledger_events": count_ledger_events(),
            "files": {
                "ensemble_weights": (OUTPUTS_DIR / "ensemble_weights.json").exists(),
                "resonance_ledger": (MEMORY_DIR / "resonance_ledger.jsonl").exists(),
                "learning_log": (OUTPUTS_DIR / "online_learning_log.jsonl").exists()
            },
            "repo_root": str(REPO_ROOT)
        }
        return [TextContent(type="text", text=json.dumps(status, indent=2))]
    
    elif name == "lumen_get_judge_performance":
        hours = arguments.get("hours", 24)
        # Get weights file (contains judge stats)
        weights_file = OUTPUTS_DIR / "ensemble_weights.json"
        result = read_json_file(weights_file)
        
        if result["ok"]:
            # Extract judge_stats from metadata
            data = result["data"]
            judge_stats = data.get("metadata", {}).get("judge_stats", {})
            performance = {
                "ok": True,
                "window_hours": hours,
                "timestamp": data.get("timestamp"),
                "judges": judge_stats
            }
            return [TextContent(type="text", text=json.dumps(performance, indent=2))]
        else:
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    else:
        error = {"ok": False, "error": f"Unknown tool: {name}"}
        return [TextContent(type="text", text=json.dumps(error, indent=2))]


# ===== Server Entry Point =====

async def main():
    """Run the Lumen MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    print("🌟 Lumen MCP Server starting...", file=sys.stderr)
    print(f"📂 Repo root: {REPO_ROOT}", file=sys.stderr)
    print(f"🐍 Python: {VENV_PYTHON}", file=sys.stderr)
    asyncio.run(main())
