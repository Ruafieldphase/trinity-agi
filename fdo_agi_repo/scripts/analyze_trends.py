import json
import os
import io
import sys
from collections import defaultdict, deque
from datetime import datetime, timedelta

# Define paths
repo_root = os.path.dirname(os.path.dirname(__file__))
ledger_path = os.path.join(repo_root, "memory", "resonance_ledger.jsonl")

def calculate_moving_average(data, window_size):
    if not data:
        return []
    numbers = [item[1] for item in data]
    moving_averages = []
    for i in range(len(numbers)):
        start_index = max(0, i - window_size + 1)
        window = numbers[start_index:i+1]
        moving_averages.append(sum(window) / len(window))
    return [(data[i][0], avg) for i, avg in enumerate(moving_averages)]

def analyze_trends():
    if not os.path.exists(ledger_path):
        print(f"Ledger file not found at {ledger_path}")
        return

    quality_scores = []
    second_pass_events = []
    meta_cognition_events = []

    with open(ledger_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                ts = entry.get("ts")
                if not ts:
                    continue
                
                dt_object = datetime.fromtimestamp(ts)

                if entry.get("event") == "eval":
                    eval_data = entry.get("eval", {})
                    quality = float(eval_data.get("quality", 0.0))
                    quality_scores.append((dt_object, quality))
                
                elif entry.get("event") == "second_pass":
                    second_pass_events.append((dt_object, 1))

                elif entry.get("event") == "meta_cognition":
                    meta_cognition_events.append({
                        "timestamp": dt_object,
                        "domain": entry.get("domain", "general"),
                        "confidence": float(entry.get("confidence", 0.0))
                    })

            except (json.JSONDecodeError, KeyError):
                continue

    # 1. 품질 점수 이동 평균 분석
    quality_scores.sort()
    ma_quality = calculate_moving_average(quality_scores, window_size=10)
    
    print("="*60)
    print("🚀 AGI Trend Analysis Report")
    print("="*60)
    
    print("\n📊 1. Quality Score Trend (10-point Moving Average)")
    if ma_quality:
        trend_points_indices = sorted(list(set([0, len(ma_quality)//2, len(ma_quality)-1])))
        trend_points = [ma_quality[i] for i in trend_points_indices]

        for dt, avg_q in trend_points:
            print(f"  - {dt.strftime('%Y-%m-%d %H:%M')}: Avg Quality = {avg_q:.3f}")
        
        start_q = ma_quality[0][1]
        end_q = ma_quality[-1][1]
        if end_q > start_q + 0.05:
            print("  - Trend: ✅ Improving")
        elif end_q < start_q - 0.05:
            print("  - Trend: ⚠️ Declining")
        else:
            print("  - Trend: ➖ Stable")
    else:
        print("  - Not enough data.")

    # 2. 자기 교정 빈도 분석
    print("\n🔄 2. Self-Correction (Second Pass) Frequency")
    if second_pass_events:
        daily_counts = defaultdict(int)
        for dt, _ in second_pass_events:
            daily_counts[dt.date()] += 1
        
        print(f"  - Total self-corrections: {len(second_pass_events)}")
        for day, count in sorted(daily_counts.items())[-3:]: # Last 3 days
             print(f"  - {day.strftime('%Y-%m-%d')}: {count} occurrences")
    else:
        print("  - No self-correction events found.")

    # 3. 도메인별 자신감 분석
    print("\n🧠 3. Confidence per Domain")
    if meta_cognition_events:
        domain_confidence = defaultdict(list)
        for event in meta_cognition_events:
            domain_confidence[event["domain"]].append(event["confidence"])
        
        print("  - Average confidence scores by domain:")
        for domain, scores in sorted(domain_confidence.items()):
            avg_conf = sum(scores) / len(scores)
            print(f"    - {domain:<10}: {avg_conf:.3f} (from {len(scores)} evaluations)")
    else:
        print("  - No meta-cognition events found.")
        
    print("\n" + "="*60)

def main():
    # UTF-8 출력 강제 설정 (Windows cp949 인코딩 문제 해결)
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    analyze_trends()

if __name__ == "__main__":
    main()