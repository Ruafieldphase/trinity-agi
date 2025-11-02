"""
Phase 2.9 E2E Streaming Pipeline Test
"""
import os
import sys
import time

# Ensure streaming DISABLED (Baseline)
os.environ["THESIS_STREAMING"] = "false"
os.environ["ANTITHESIS_STREAMING"] = "false"
os.environ["SYNTHESIS_STREAMING"] = "false"

from orchestrator.pipeline import run_task

task_spec = {
    "task_id": "e2e-smoke",
    "title": "E2E Test",
    "goal": "AGI 자율 시스템 핵심 3문장"
}

print("\n=== E2E Baseline (No Streaming) Test ===")
print("All streaming DISABLED")

t0 = time.perf_counter()
try:
    result = run_task({}, task_spec)
    t1 = time.perf_counter()
    print(f"\nTotal: {t1 - t0:.2f}s")
    print(f"Summary: {result.get('summary', '')[:150]}...")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

# Check ledger
import json
ledger_path = "memory/resonance_ledger.jsonl"
if os.path.exists(ledger_path):
    with open(ledger_path, 'r', encoding='utf-8') as f:
        for line in list(f)[-30:]:  # Last 30 lines
            try:
                entry = json.loads(line)
                if entry.get('event') == 'pipeline_e2e_complete':
                    print(f"\nPipeline Metrics:")
                    print(f"  Duration: {entry.get('total_duration_sec', 0):.2f}s")
                    print(f"  Streaming: {entry.get('streaming_enabled')}")
                    if 'pipeline_ttft_sec' in entry:
                        print(f"  TTFT: {entry['pipeline_ttft_sec']:.2f}s")
                        print(f"  Perceived: {entry['pipeline_perceived_improvement_pct']:.1f}%")
                    break
            except:
                pass
