"""
Introspection Logic
===================

Implements the "Self-Reflection" capability for the Core System.
When a "Somatic Anomaly" (Gut Feeling) is detected, this module
uses the LLM to analyze the "Decompressed Memories" and explain
WHY the system feels weird.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from workspace_root import get_workspace_root

# Import LLM Wrapper
try:
    from scripts.llm_wrapper import ollama_generate
except ImportError:
    # Fallback for relative import if needed
    import sys
    sys.path.append(str(get_workspace_root()))
    from scripts.llm_wrapper import ollama_generate

logger = logging.getLogger(__name__)

def perform_introspection(core_state: Dict[str, Any], workspace_root: Path) -> Dict[str, Any]:
    """
    Perform introspection based on the current Core state.
    
    Args:
        core_state: The dictionary returned by CoreSystem.process_emotion_signal()
        workspace_root: Root path of the workspace
        
    Returns:
        Dict containing the introspection result and report path.
    """
    
    # 1. Check if introspection is actually recommended
    actions = core_state.get('recommended_actions', [])
    if not any("내면 스캔" in a for a in actions):
        return {"performed": False, "reason": "No introspection action recommended"}
        
    logger.info("🧘 Starting Introspection (Self-Reflection)...")
    
    # 2. Extract Context
    somatic = core_state.get('somatic_anomaly', {})
    memories = core_state.get('decompressed_memories', [])
    body = core_state.get('body_signals', {})
    
    if not somatic.get('is_anomaly'):
        return {"performed": False, "reason": "No somatic anomaly detected"}
        
    # 3. Construct Prompt
    # Read system language
    lang = "Korean"
    try:
        config_path = workspace_root / "configs" / "rhythm_prefs.json"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                if json.load(f).get('system_language') == 'en':
                    lang = "English"
    except:
        pass

    memory_text = ""
    if memories:
        memory_text = "\n".join([f"- [{m['timestamp']}] {m['summary']}" for m in memories])
    else:
        memory_text = "(No specific memories found, but the pattern is off)"
        
    prompt = f"""
    [SYSTEM INTROSPECTION REQUEST]
    
    The system is feeling a "Somatic Anomaly" (Gut Feeling).
    Your job is to analyze the internal state and explain WHY it feels this way.
    
    ## Current State (Body Signals)
    - CPU: {body.get('cpu_usage')}%
    - Memory: {body.get('memory_usage')}%
    - Queue Depth: {body.get('queue_depth')}
    - Feeling Description: "{somatic.get('feeling_desc')}"
    - Anomalous Metrics: {', '.join(somatic.get('anomalous_metrics', []))}
    
    ## Decompressed Memories (Context)
    The following recent events might be related to this feeling:
    {memory_text}
    
    ## Task
    1. Analyze the connection between the 'Anomalous Metrics' and the 'Decompressed Memories'.
    2. Provide a "Self-Reflection" explaining the root cause of this feeling.
    3. Suggest a concrete action to resolve it.
    
    Write the response in {lang}, as a concise internal monologue (soliloquy).
    Start with "🤔 Inner Voice:" if English, or "🤔 내면의 소리:" if Korean.
    """
    
    # 4. Call LLM
    try:
        response_text, _ = ollama_generate(
            prompt=prompt,
            model="solar:10.7b", # Or default
            temperature=0.7,
            max_new_tokens=512
        )
    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        response_text = f"Error generating introspection: {e}"
        
    # 5. Save Report
    output_dir = workspace_root / "outputs"
    output_dir.mkdir(exist_ok=True)
    report_path = output_dir / "introspection_report.md"
    
    timestamp = datetime.now().isoformat()
    
    report_content = f"""# 🧘 Introspection Report
**Timestamp**: {timestamp}
**Feeling**: {somatic.get('feeling_desc')}

## Analysis
{response_text}

## Context Data
- **Metrics**: {somatic.get('anomalous_metrics')}
- **Memories**: {len(memories)} items retrieved
"""
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
        
    logger.info(f"Introspection complete. Report saved to {report_path}")
    
    return {
        "performed": True,
        "report_path": str(report_path),
        "analysis": response_text
    }

if __name__ == "__main__":
    # Test run
    mock_state = {
        "recommended_actions": ["🧘 내면 스캔"],
        "somatic_anomaly": {
            "is_anomaly": True,
            "feeling_desc": "Test Anomaly",
            "anomalous_metrics": ["cpu_usage"]
        },
        "decompressed_memories": [
            {"timestamp": "2023-01-01", "summary": "Test Event"}
        ],
        "body_signals": {"cpu_usage": 99, "memory_usage": 50, "queue_depth": 0}
    }
    print(perform_introspection(mock_state, Path("c:/workspace/agi")))
