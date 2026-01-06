
import sys
import json
from pathlib import Path
from unittest.mock import MagicMock

# Add script directory to path
sys.path.append(str(Path(__file__).parent))

import rhythm_think

def test_escalation():
    print("🧪 Testing High-Fear Escalation...")
    
    # Mock state: CONTRACTION phase + High Fear
    mock_state = {
        'phase': 'CONTRACTION',
        'fear_level': 0.95,
        'body_signals': {'cpu_usage': 85},
        'strategy': 'survival'
    }
    
    mock_decision = {
        'decision': 'stabilize',
        'action': 'Emergency stabilization'
    }
    
    # Mock LEDGER_FILE to a temporary file
    temp_ledger = Path("c:/workspace/agi/outputs/test_ledger.jsonl")
    if temp_ledger.exists():
        temp_ledger.unlink()
        
    original_ledger = rhythm_think.LEDGER_FILE
    rhythm_think.LEDGER_FILE = temp_ledger
    
    try:
        # Run escalation
        rhythm_think.escalate_to_sena(mock_state, mock_decision)
        
        # Verify output
        if temp_ledger.exists():
            content = temp_ledger.read_text(encoding='utf-8')
            entry = json.loads(content)
            
            print(f"📝 Ledger Entry: {json.dumps(entry, indent=2, ensure_ascii=False)}")
            
            assert entry['type'] == 'diagnostic_request'
            assert entry['target'] == 'sena'
            assert entry['priority'] == 'high'
            assert entry['metadata']['fear_level'] == 0.95
            
            print("✅ Escalation logic verified: Request written to ledger.")
        else:
            print("❌ Test Failed: Ledger file not created.")
            
    finally:
        # Cleanup
        rhythm_think.LEDGER_FILE = original_ledger
        if temp_ledger.exists():
            temp_ledger.unlink()

if __name__ == "__main__":
    test_escalation()
