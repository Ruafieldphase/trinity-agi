import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add workspace root to path
workspace_root = Path("c:/workspace/agi")
sys.path.append(str(workspace_root))

from scripts.introspection_logic import perform_introspection

def test_introspection_trigger():
    print("🧪 Testing Introspection Logic...")
    
    # Mock Data
    mock_state = {
        "recommended_actions": ["🧘 내면 스캔", "Other Action"],
        "somatic_anomaly": {
            "is_anomaly": True,
            "feeling_desc": "Test Anomaly Feeling",
            "anomalous_metrics": ["cpu_usage", "queue_depth"]
        },
        "decompressed_memories": [
            {"timestamp": "2023-01-01T12:00:00", "summary": "Heavy build task started"}
        ],
        "body_signals": {
            "cpu_usage": 95.5,
            "memory_usage": 80.0,
            "queue_depth": 150
        }
    }
    
    # Mock LLM
    with patch('scripts.introspection_logic.ollama_generate') as mock_llm:
        mock_llm.return_value = ("🤔 내면의 소리: CPU 사용량이 높고 큐가 밀려있어 불안감을 느낍니다. "
                                 "아마도 빌드 작업 때문인 것 같습니다.", {})
        
        # Run
        result = perform_introspection(mock_state, workspace_root)
        
        # Verify
        if result['performed']:
            print("✅ Introspection performed successfully")
            print(f"   Report Path: {result['report_path']}")
            print(f"   Analysis: {result['analysis']}")
            
            # Check if file exists
            if os.path.exists(result['report_path']):
                print("✅ Report file created")
                # Clean up
                # os.remove(result['report_path']) 
            else:
                print("❌ Report file NOT created")
                sys.exit(1)
        else:
            print(f"❌ Introspection NOT performed: {result.get('reason')}")
            sys.exit(1)

if __name__ == "__main__":
    test_introspection_trigger()
