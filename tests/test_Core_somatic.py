import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
import random

# Add workspace root to path
workspace_root = Path("c:/workspace/agi")
sys.path.insert(0, str(workspace_root))

from fdo_agi_repo.orchestrator.core_system import CoreSystem, BodySignals

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestSomatic")

def create_mock_signal(timestamp, cpu=20.0, mem=40.0, queue=10):
    return {
        'timestamp': timestamp,
        'body_signals': {
            'cpu_usage': cpu,
            'memory_usage': mem,
            'queue_depth': queue,
            'queue_status': 'OK',
            'hours_since_rest': 1.0,
            'recent_tasks': 5,
            'recent_quality': 0.9
        },
        'fear_signal': {'level': 0.1, 'reasons': []},
        'background_self': {'strategy': 'FLOW'}
    }

def test_somatic_anomaly():
    Core = CoreSystem(workspace_root)
    
    # 1. Populate history with "Normal" data (Baseline)
    logger.info("Phase 1: Establishing Baseline (Normal State)...")
    base_time = datetime.now() - timedelta(hours=24)
    
    for i in range(20):
        # Normal variations
        cpu = 20.0 + random.uniform(-5, 5)
        mem = 40.0 + random.uniform(-2, 2)
        queue = 10 + random.randint(-2, 2)
        
        signal = create_mock_signal(
            (base_time + timedelta(hours=i)).isoformat(),
            cpu, mem, queue
        )
        Core.signal_history.append(signal)
        
    # 2. Test Normal Case
    logger.info("Phase 2: Testing Normal Input...")
    # Inject current mock body signal
    Core.collect_body_signals = lambda: BodySignals(
        datetime.now().isoformat(), 
        22.0, 41.0, 11, "OK", 1.0, 5, 0.9
    )
    
    result = Core.process_emotion_signal()
    print(f"\n[Normal Case] Anomaly: {result['somatic_anomaly']['is_anomaly']}")
    print(f"Desc: {result['somatic_anomaly']['feeling_desc']}")
    
    if result['somatic_anomaly']['is_anomaly']:
        print("❌ FAILED: Normal case detected as anomaly")
    else:
        print("✅ PASSED: Normal case OK")

    # 3. Test Anomaly Case (Sudden Spike)
    logger.info("\nPhase 3: Testing Anomaly Input (Sudden Spike)...")
    
    # [MOCK LEDGER] Create a temporary ledger file for decompression test
    ledger_path = workspace_root / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Backup existing ledger if any
    backup_path = None
    if ledger_path.exists():
        backup_path = ledger_path.with_suffix('.jsonl.bak')
        ledger_path.rename(backup_path)
        
    try:
        # Write mock events related to CPU spike
        with open(ledger_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps({'timestamp': '2025-11-26T10:00:00', 'type': 'build', 'summary': 'Heavy build process started'}) + '\n')
            f.write(json.dumps({'timestamp': '2025-11-26T10:05:00', 'type': 'error', 'summary': 'Queue processing failed'}) + '\n')
            f.write(json.dumps({'timestamp': '2025-11-26T10:10:00', 'type': 'task', 'summary': 'Complex calculation running'}) + '\n')

        # Inject abnormal body signal (CPU Spike 80%, Queue Spike 100)
        Core.collect_body_signals = lambda: BodySignals(
            datetime.now().isoformat(), 
            80.0, 45.0, 100, "OK", 1.0, 5, 0.9
        )
        
        result = Core.process_emotion_signal()
        print(f"\n[Anomaly Case] Anomaly: {result['somatic_anomaly']['is_anomaly']}")
        print(f"Desc: {result['somatic_anomaly']['feeling_desc']}")
        print(f"Metrics: {result['somatic_anomaly']['anomalous_metrics']}")
        
        # Check Decompression
        memories = result.get('decompressed_memories', [])
        print(f"Decompressed Memories: {len(memories)}")
        for mem in memories:
            print(f" - {mem['summary']}")
            
        print(f"Actions: {result['recommended_actions'][0]}")
        
        if result['somatic_anomaly']['is_anomaly']:
            print("✅ PASSED: Anomaly detected")
            if len(memories) > 0:
                 print("✅ PASSED: Memories retrieved (Decompression successful)")
            else:
                 print("❌ FAILED: No memories retrieved")
        else:
            print("❌ FAILED: Anomaly NOT detected")
            
    finally:
        # Restore backup
        if ledger_path.exists():
            ledger_path.unlink()
        if backup_path and backup_path.exists():
            backup_path.rename(ledger_path)

if __name__ == "__main__":
    test_somatic_anomaly()
