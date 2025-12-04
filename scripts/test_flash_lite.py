#!/usr/bin/env python3
"""
Test gemini-2.5-flash-lite-preview model
"""

import sys
from pathlib import Path

# Add Ion Mentoring path
ION_PATH = Path(__file__).parent.parent / "LLM_Unified/ion-mentoring"
sys.path.append(str(ION_PATH))

try:
    from ion_first_vertex_ai import VertexAIConnector
    
    print("Testing gemini-2.5-flash-lite (GA)...")
    
    connector = VertexAIConnector(
        project_id="naeda-genesis",
        location="global",
        model_name="gemini-2.5-flash-lite"
    )
    
    connector.initialize()
    connector.load_model()
    
    response = connector.send_prompt("Say hello in one sentence.")
    
    print(f"\n✅ SUCCESS!")
    print(f"Response: {response}")
    
except Exception as e:
    print(f"\n❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
