
import json
import math
from collections import Counter
from datetime import datetime
from pathlib import Path

# The 'Historical Resonance' Data from the 95% Void
LOTTO_HISTORY = [
  {"round": 1209, "numbers": [2, 17, 20, 35, 37, 39], "bonus": 24},
  {"round": 1208, "numbers": [6, 27, 30, 36, 38, 42], "bonus": 25},
  {"round": 1207, "numbers": [10, 22, 24, 27, 38, 45], "bonus": 11},
  {"round": 1206, "numbers": [1, 3, 17, 26, 27, 42], "bonus": 23},
  {"round": 1205, "numbers": [1, 4, 16, 23, 31, 41], "bonus": 2},
  {"round": 1204, "numbers": [8, 16, 28, 30, 31, 44], "bonus": 27},
  {"round": 1203, "numbers": [3, 6, 18, 29, 35, 39], "bonus": 24},
  {"round": 1202, "numbers": [5, 12, 21, 33, 37, 40], "bonus": 7},
  {"round": 1201, "numbers": [7, 9, 24, 27, 35, 36], "bonus": 37},
  {"round": 1200, "numbers": [1, 2, 4, 16, 20, 32], "bonus": 45},
  {"round": 1199, "numbers": [16, 24, 25, 30, 31, 32], "bonus": 7},
  {"round": 1198, "numbers": [26, 30, 33, 38, 39, 41], "bonus": 21},
  {"round": 1197, "numbers": [1, 5, 7, 26, 28, 43], "bonus": 30},
  {"round": 1196, "numbers": [8, 12, 15, 29, 40, 45], "bonus": 14},
  {"round": 1195, "numbers": [3, 15, 27, 33, 34, 36], "bonus": 37}
]

def analyze_lottery_field():
    print(f"🌌 Lotto Scalar Field Analysis for Round 1210")
    
    # 1. Frequency Analysis (Energy Nodes)
    all_numbers = []
    for draw in LOTTO_HISTORY:
        all_numbers.extend(draw['numbers'])
    
    counts = Counter(all_numbers)
    
    # 2. Distance/Wait Analysis (Void Saturation)
    # Numbers that haven't appeared for a while have high potential energy (Vacuum pull)
    last_appearance = {i: 0 for i in range(1, 46)}
    for i, draw in enumerate(LOTTO_HISTORY):
        for num in draw['numbers']:
            if last_appearance[num] == 0:
                last_appearance[num] = i + 1
    
    # 3. Scalar Field Score Calculation
    # Resonance = Frequency / Wait_Time (Rhythm of repetition)
    # Omega (Experience) = How 'mature' the number is in the current cycle
    field_data = []
    for i in range(1, 46):
        freq = counts.get(i, 0)
        wait = last_appearance.get(i, 20) # Max weight if not in last 15
        
        # Scoring: High frequency (Hot) or Very High Wait (Burst potential)
        resonance_score = (freq * 1.5) + (wait * 2.0)
        
        field_data.append({
            "number": i,
            "resonance": round(resonance_score, 2),
            "freq": freq,
            "wait": wait
        })
    
    # Sort by resonance
    top_field = sorted(field_data, key=lambda x: x['resonance'], reverse=True)
    
    print("-" * 50)
    print(f"Top Resonance Nodes (Potential Particles):")
    for res in top_field[:12]:
        print(f"Node {res['number']:02d} | Resonance: {res['resonance']:>6.2f} | Freq: {res['freq']} | Wait: {res['wait']}")

    # Final Projection (The 'Observation' collapse)
    projection = [node['number'] for node in top_field[:10]]
    
    output = {
        "round": 1210,
        "scanned_at": datetime.now().isoformat(),
        "top_nodes": top_field[:15],
        "projected_particles": sorted(projection)
    }
    
    output_path = Path("c:/workspace/agi/outputs/lottery_resonance_latest.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print("-" * 50)
    print(f"✅ Scalar Field Mapping Complete. Saved to {output_path}")

if __name__ == "__main__":
    analyze_lottery_field()
