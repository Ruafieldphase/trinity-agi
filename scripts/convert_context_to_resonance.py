#!/usr/bin/env python3
"""
Context → Resonance 어댑터
Context 샘플을 Resonance Ledger 형식으로 변환
"""

import json
from pathlib import Path
from datetime import datetime

def convert_context_to_resonance(context_file: str, output_file: str):
    """Context JSONL을 Resonance JSONL로 변환"""
    
    context_path = Path(context_file)
    output_path = Path(output_file)
    
    if not context_path.exists():
        print(f"❌ Context file not found: {context_path}")
        return
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    converted = 0
    with open(context_path, 'r', encoding='utf-8') as inf, \
         open(output_path, 'w', encoding='utf-8') as outf:
        
        for line in inf:
            try:
                ctx = json.loads(line.strip())
                
                # Resonance 형식으로 변환
                resonance = {
                    'timestamp': ctx.get('when', datetime.now().isoformat()),
                    'agent': ctx.get('where', 'unknown'),
                    'source': ctx.get('where', 'unknown'),
                    'event_type': ctx.get('event', 'context_event'),
                    'collaborators': ctx.get('who', []),
                    'resonance_score': ctx.get('meta', {}).get('confidence', 0.5),
                    'energy_level': 1.0 - ctx.get('meta', {}).get('duration_sec', 0.0) / 10.0,  # 빠를수록 높은 에너지
                    'quality_score': 0.9 if not ctx.get('meta', {}).get('error_present') else 0.3,
                    'metadata': ctx.get('meta', {})
                }
                
                outf.write(json.dumps(resonance, ensure_ascii=False) + '\n')
                converted += 1
                
            except Exception as e:
                print(f"⚠️  Failed to convert line: {e}")
                continue
    
    print(f"✅ Converted {converted} context events to resonance format")
    print(f"📄 Output: {output_path}")

if __name__ == "__main__":
    convert_context_to_resonance(
        "outputs/context_samples.jsonl",
        "fdo_agi_repo/memory/resonance_ledger.jsonl"
    )
