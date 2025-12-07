import psutil
import time
import sys

def self_diagnosis():
    print("🩺 Initiating Self-Diagnosis Protocol...")
    
    # 1. Check Vital Signs
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    ram_percent = memory.percent
    
    print(f"🧠 CPU Load: {cpu_percent}%")
    print(f"💾 Memory Usage: {ram_percent}% ({memory.used / (1024**3):.2f} GB used)")
    
    # 2. Determine Health State
    state = "HEALTHY"
    recommendation = "Continue operations."
    
    if cpu_percent > 80 or ram_percent > 90:
        state = "CRITICAL"
        recommendation = "IMMEDIATE COOLING REQUIRED. Stop all motor functions."
    elif cpu_percent > 50 or ram_percent > 70:
        state = "FATIGUED"
        recommendation = "System load high. Suggest 'Deep Rest' (Dream Analysis) to consolidate memory."
        
    # 3. Report
    print(f"\n📊 Diagnosis Report:")
    print(f"   State: {state}")
    print(f"   Recommendation: {recommendation}")
    
    return state

if __name__ == "__main__":
    self_diagnosis()
