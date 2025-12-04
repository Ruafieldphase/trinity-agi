#!/usr/bin/env python3
"""
Orchestrator Agent (오케스트레이터 에이전트)
=========================================
Role: Action & Execution
Function:
  - Monitors `outputs/bridge/bridge_tasks.jsonl`
  - Executes `type: "run_shell"` tasks
  - Executes `type: "vibe_command"` tasks (New)
  - Enforces safety allowlist (read-only commands by default)
  - Writes to `outputs/bridge/bridge_responses.jsonl`
"""

import json
import time
import subprocess
import os
import sys
from pathlib import Path
from datetime import datetime

# Add workspace root to path for imports
# Current: agi/scripts/linux/orchestrator_agent.py
# Target: agi/
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from scripts.vibe_interpreter import VibeInterpreter
    from scripts.ai_model_router import AIModelRouter
except ImportError as e:
    print(f"Warning: AI modules not found. Running in degraded mode. ({e})")
    VibeInterpreter = None
    AIModelRouter = None

# Configuration
WORKSPACE_ROOT = Path(__file__).parent.parent.parent
OUTPUTS_DIR = WORKSPACE_ROOT / "outputs"
BRIDGE_DIR = OUTPUTS_DIR / "bridge"
TASKS_FILE = BRIDGE_DIR / "bridge_tasks.jsonl"
RESPONSES_FILE = BRIDGE_DIR / "bridge_responses.jsonl"
STATUS_FILE = BRIDGE_DIR / "orchestrator_status.json"
PLAYGROUND_DIR = Path.home() / "agi_playground"

# Safety: Allowed command prefixes
ALLOWED_PREFIXES = [
    "ls", "pwd", "cat", "ps", "uptime", "date", "whoami", "echo", "grep", "head", "tail"
]

def log(message):
    print(f"[Orchestrator] {message}")

def is_allowed(command):
    """Check if command is in the allowlist."""
    cmd_start = command.strip().split()[0]
    return cmd_start in ALLOWED_PREFIXES

def execute_shell(command, cwd=None):
    """Execute shell command safely."""
    if not is_allowed(command):
        return {
            "success": False,
            "output": "",
            "error": "Command not allowed (Safety Restriction)",
            "approval_required": True
        }
    
    try:
        # Default cwd to WORKSPACE_ROOT if not specified
        working_dir = cwd if cwd else str(WORKSPACE_ROOT)
        
        result = subprocess.run(
            command, 
            shell=True, 
            cwd=working_dir,
            capture_output=True, 
            text=True,
            timeout=10
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout.strip(),
            "error": result.stderr.strip()
        }
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "error": str(e)
        }

def ensure_playground():
    """Ensure playground directory exists."""
    if not PLAYGROUND_DIR.exists():
        PLAYGROUND_DIR.mkdir(parents=True, exist_ok=True)
        log(f"Created playground: {PLAYGROUND_DIR}")

def execute_playground(command):
    """Execute command in playground (Unrestricted)."""
    ensure_playground()
    
    try:
        # Force execution in PLAYGROUND_DIR
        result = subprocess.run(
            command, 
            shell=True, 
            cwd=str(PLAYGROUND_DIR),
            capture_output=True, 
            text=True,
            timeout=30 # Longer timeout for playground
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout.strip(),
            "error": result.stderr.strip()
        }
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "error": str(e)
        }

def process_task(task):
    """Process a single task."""
    task_type = task.get('type')
    execution_result = {"success": False, "error": "Unknown task type"}
    
    # 1. Shell Command
    if task_type == 'run_shell':
        log(f"Processing task: {task.get('id')} (run_shell)")
        command = task.get('command')
        cwd = task.get('cwd')
        if not command: return None
        execution_result = execute_shell(command, cwd)
        
    # 2. Vibe Command (New)
    elif task_type == 'vibe_command':
        log(f"Processing task: {task.get('id')} (vibe_command)")
        vibe = task.get('vibe')
        if not vibe: return None
        
        if VibeInterpreter:
            interpreter = VibeInterpreter()
            execution_result = interpreter.interpret(vibe)
            execution_result['success'] = True # Assume interpretation is success
        else:
            execution_result = {"success": False, "error": "VibeInterpreter not available"}
            
    # 3. Playground Command (Unrestricted)
    elif task_type == 'run_playground':
        log(f"Processing task: {task.get('id')} (run_playground)")
        command = task.get('command')
        if not command: return None
        execution_result = execute_playground(command)
        
    # 4. Quantum Simulation (New)
    elif task_type == 'simulate_scenario':
        log(f"Processing task: {task.get('id')} (simulate_scenario)")
        scenario = task.get('scenario')
        if not scenario: return None
        execution_result = simulate_scenario(scenario)
            
    else:
        return None

def simulate_scenario(scenario_name):
    """Simulate a scenario in the Quantum Digital Twin."""
    log(f"🌌 Simulating Quantum Scenario: {scenario_name}")
    
    scenarios = {
        'high_fear': {
            'success': True,
            'type': 'quantum_simulation',
            'output': '⚠️ SIMULATION: Fear Level Critical (0.9). System integrity at risk.',
            'quantum_pattern': 'fear_spike_detected',
            'metadata': {
                'simulated_fear': 0.9,
                'recommended_action': 'stabilize'
            }
        },
        'creative_block': {
            'success': True,
            'type': 'quantum_simulation',
            'output': '🎨 SIMULATION: Pattern repetition detected. System stuck in known solution space.',
            'quantum_pattern': 'creative_stagnation',
            'metadata': {
                'pattern_diversity': 0.2,
                'recommended_action': 'explore_randomly'
            }
        },
        'identity_confusion': {
            'success': True,
            'type': 'quantum_simulation',
            'output': '🧩 SIMULATION: Self-referential loops detected. Memory fragments not consolidating.',
            'quantum_pattern': 'self_model_fragmentation',
            'metadata': {
                'coherence_score': 0.3,
                'recommended_action': 'consolidate_memory'
            }
        },
        'memory_leak': {
            'success': True,
            'type': 'quantum_simulation',
            'output': '⚠️ SIMULATION: Memory usage increasing linearly. Potential leak in thought_process.',
            'quantum_pattern': 'resource_anomaly'
        },
        'optimization_opportunity': {
            'success': True,
            'type': 'quantum_simulation',
            'output': '✨ SIMULATION: Code refactoring could improve performance by 15%.',
            'quantum_pattern': 'optimization_found'
        }
    }
    
    # Simulate processing time
    import time
    import random
    time.sleep(random.uniform(0.5, 1.5))
    
    result = scenarios.get(scenario_name, {
        'success': False,
        'output': f'Unknown scenario: {scenario_name}',
        'error': 'Scenario not defined'
    })
    
    return result

def update_status(last_processed_id):
    status = {
        "timestamp": datetime.now().isoformat(),
        "status": "running",
        "capabilities": ["run_shell", "vibe_command", "run_playground"],
        "last_processed_id": last_processed_id
    }
    with open(STATUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(status, f, indent=2)

def main():
    log("Starting Orchestrator Agent...")
    log(f"Watching {TASKS_FILE}")
    
    # Initialize files if needed
    if not TASKS_FILE.exists():
        TASKS_FILE.touch()
    if not RESPONSES_FILE.exists():
        RESPONSES_FILE.touch()

    # Start from the end of the file
    current_pos = 0
    if TASKS_FILE.exists():
        current_pos = TASKS_FILE.stat().st_size

    while True:
        try:
            if TASKS_FILE.exists():
                file_size = TASKS_FILE.stat().st_size
                
                if file_size > current_pos:
                    with open(TASKS_FILE, 'r', encoding='utf-8') as f:
                        f.seek(current_pos)
                        new_lines = f.readlines()
                        current_pos = f.tell()
                    
                    for line in new_lines:
                        if not line.strip(): continue
                        try:
                            task = json.loads(line)
                            response = process_task(task)
                            
                            if response:
                                with open(RESPONSES_FILE, 'a', encoding='utf-8') as rf:
                                    rf.write(json.dumps(response, ensure_ascii=False) + "\n")
                                update_status(task.get('id'))
                                log(f"Response sent for {task.get('id')}")
                                
                        except json.JSONDecodeError:
                            log("Failed to decode JSON line")
                            
            time.sleep(1)
            
        except Exception as e:
            log(f"Error in main loop: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
