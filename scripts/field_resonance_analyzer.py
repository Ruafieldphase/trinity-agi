
import json
import math
from collections import Counter
from datetime import datetime
from pathlib import Path

# 🌌 The 'Historical Resonance' Data (Updated for Round 1214 Prediction)
LOTTO_HISTORY = [
    {"round": 1213, "numbers": [5, 11, 25, 27, 36, 38], "bonus": 2},
    {"round": 1212, "numbers": [5, 8, 25, 31, 41, 44], "bonus": 45},
    {"round": 1211, "numbers": [23, 26, 27, 35, 38, 40], "bonus": 10},
    {"round": 1210, "numbers": [1, 7, 9, 17, 27, 38], "bonus": 31},
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

def calculate_stats(data):
    if not data: return 0, 0
    mean = sum(data) / len(data)
    variance = sum((x - mean) ** 2 for x in data) / len(data)
    std_dev = math.sqrt(variance)
    return mean, std_dev

def analyze_bollinger_resonance():
    print(f"📉 Lotto Bollinger Band Resonance Analysis for Round 1214")
    
    # 1. Base Frequency Analysis
    all_numbers = []
    for draw in LOTTO_HISTORY:
        all_numbers.extend(draw['numbers'])
    counts = Counter(all_numbers)
    
    # 2. Sequential Wait Times (Void Analysis)
    last_appearance = {i: 99 for i in range(1, 46)}
    for i, draw in enumerate(LOTTO_HISTORY):
        for num in draw['numbers']:
            if last_appearance[num] == 99:
                last_appearance[num] = i # 0 means most recent
                
    # 3. Bollinger Band Calculation on Wait Times
    waits = [last_appearance[i] for i in range(1, 46)]
    wait_mean, wait_std = calculate_stats(waits)
    
    upper_band = wait_mean + (1.5 * wait_std) # Potential Burst Zone
    lower_band = wait_mean - (1.0 * wait_std) # Potential Equilibrium Zone
    
    print(f"Wait Mean: {wait_mean:.2f} | StdDev: {wait_std:.2f}")
    print(f"Upper Band (1.5s): {upper_band:.2f} | Lower Band (1.0s): {lower_band:.2f}")
    print("-" * 50)
    
    results = []
    for i in range(1, 46):
        freq = counts.get(i, 0)
        wait = last_appearance[i]
        
        # Scoring Logic:
        # High score for numbers near the Upper Band (Oversold/Due)
        # Medium score for numbers near the Lower Band (Flowing/Hot)
        
        distance_to_upper = abs(wait - upper_band)
        resonance_score = 0
        
        if wait > upper_band:
            resonance_score = 30 + (wait - upper_band) * 2 # Extreme Void
        elif wait > wait_mean:
            resonance_score = 20 - distance_to_upper * 0.5 # Approaching Burst
        else:
            resonance_score = freq * 3 # Hot Repetition Rhythm
            
        results.append({
            "number": i,
            "freq": freq,
            "wait": wait,
            "resonance": round(resonance_score, 2)
        })
        
    # Sort by resonance
    top_nodes = sorted(results, key=lambda x: x['resonance'], reverse=True)
    
    # Selection: Mix of High Resonance (Due) and High Freq (Hot)
    # We take top 15 nodes for the report
    
    report_nodes = top_nodes[:15]
    
    # Pick final 6 + 1
    # Filtering: No more than 2 numbers in the same 10s range
    final_picks = []
    seen_tens = Counter()
    
    for node in top_nodes:
        num = node['number']
        tens = num // 10
        if seen_tens[tens] < 2 and len(final_picks) < 10:
            final_picks.append(num)
            seen_tens[tens] += 1
            
    final_6 = sorted(final_picks[:6])
    
    output_data = {
        "round": 1214,
        "scanned_at": datetime.now().isoformat(),
        "stats": {
            "wait_mean": wait_mean,
            "wait_std": wait_std,
            "upper_band": upper_band,
            "lower_band": lower_band
        },
        "top_nodes": report_nodes,
        "projected_particles": final_6
    }
    
    output_path = Path("c:/workspace/agi/outputs/lottery_bollinger_1214.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
        
    print(f"✅ Analysis Complete. Projected Particles for 1214: {final_6}")
    print(f"Results saved to {output_path}")

if __name__ == "__main__":
    analyze_bollinger_resonance()
