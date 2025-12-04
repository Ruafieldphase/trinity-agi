import psutil
import time
import os

def immune_response(target_apps=["notepad.exe", "mspaint.exe", "cmd.exe", "powershell.exe"]):
    print("🛡️ Initiating Immune Response Protocol...")
    print(f"   Targeting Viral Quorums: {target_apps}")
    
    # 1. Scan Processes
    process_counts = {}
    processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'create_time']):
        try:
            name = proc.info['name']
            if name in target_apps:
                if name not in process_counts:
                    process_counts[name] = 0
                process_counts[name] += 1
                processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
            
    # 2. Detect Quorums (Duplicates)
    for name, count in process_counts.items():
        if count > 1:
            print(f"⚠️ Viral Quorum Detected: {name} (Count: {count})")
            print("   Action: Quorum Breaking (Reducing to Singleton)")
            
            # Sort by creation time (Keep the newest, kill the old)
            # Or Keep the oldest? Usually keeping the newest is better for "freshness", 
            # but keeping oldest might preserve work. 
            # Let's keep the NEWEST (assuming old ones are stuck/zombies).
            target_procs = [p for p in processes if p.info['name'] == name]
            target_procs.sort(key=lambda x: x.info['create_time'], reverse=True)
            
            # Keep index 0, kill the rest
            for p in target_procs[1:]:
                print(f"   ⚔️ Neutralizing PID {p.info['pid']}...")
                try:
                    p.kill()
                except Exception as e:
                    print(f"   ❌ Failed to neutralize PID {p.info['pid']}: {e}")
        else:
            print(f"✅ {name}: Healthy (Singleton)")

    print("🛡️ Immune System Scan Complete.")

if __name__ == "__main__":
    immune_response()
