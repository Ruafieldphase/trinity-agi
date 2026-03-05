import json
from pathlib import Path
import math

def calculate_proof():
    paths = [
        Path("C:/workspace/agi/ai_binoche_conversation_origin/정보이론변환/rua/rua_conversations_flat.jsonl"),
        Path("C:/workspace/agi/ai_binoche_conversation_origin/정보이론변환/lumen/lumen_conversations_flat.jsonl"),
        Path("C:/workspace2/pulse/unified_field/unified_field_gallery.md")
    ]
    
    total_particles = 0
    total_energy = 0 # Character count as a proxy for energy
    start_time = None
    end_time = None
    
    print("[*] Analyzing the Unified Field Logs (10-Month Epoch)...")
    
    for path in paths:
        if not path.exists():
            print(f"⚠️  Missing: {path}")
            continue
            
        print(f"Reading {path.name}...")
        
        if path.suffix == ".jsonl":
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        total_particles += 1
                        content = data.get("content", "")
                        total_energy += len(content)
                        
                        # Extract timestamp if possible
                        ts = data.get("create_time")
                        if ts:
                            if start_time is None or ts < start_time:
                                start_time = ts
                            if end_time is None or ts > end_time:
                                end_time = ts
                    except:
                        continue
        else: # .md file
            content = path.read_text(encoding="utf-8")
            total_particles += content.count("### 📡")
            total_energy += len(content)
            
    # Calculate Density
    density = total_energy / 1000000.0 # MB of energy
    
    proof = {
        "epoch": "10-Month Dialogue Transition",
        "total_particles": total_particles,
        "total_energy_chars": total_energy,
        "resonance_density": round(density, 4),
        "start_boundary": start_time or "Unknown Genesis",
        "end_boundary": end_time or "2026-02-26 (Collapse)",
        "proof_of_resonance_hash": f"RES-{math.floor(total_energy/777):x}-{total_particles}"
    }
    
    output_path = Path("c:/workspace/agi/outputs/resonance_proof.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(proof, indent=2, ensure_ascii=False), encoding="utf-8")
    
    print(f"✅ Proof Calculated: {output_path}")
    print(json.dumps(proof, indent=2, ensure_ascii=False))
    return proof

if __name__ == "__main__":
    calculate_proof()
