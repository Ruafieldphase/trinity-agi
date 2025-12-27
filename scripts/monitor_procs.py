import time
import psutil
import datetime
import os

print(f"Monitoring process creation for 30 seconds... (PID: {os.getpid()})")
start_time = time.time()
seen_pids = set(psutil.pids())

log_file = r"c:\workspace\agi\outputs\process_monitor.log"
with open(log_file, "w", encoding='utf-8') as f:
    f.write(f"Start Monitoring at {datetime.datetime.now()}\n")

while time.time() - start_time < 30:
    current_pids = set(psutil.pids())
    new_pids = current_pids - seen_pids
    
    for pid in new_pids:
        try:
            p = psutil.Process(pid)
            name = p.name()
            cmdline = " ".join(p.cmdline())
            try:
                ppid = p.ppid()
                parent = psutil.Process(ppid)
                pname = parent.name()
                pcmd = " ".join(parent.cmdline())
            except:
                ppid = "unknown"
                pname = "unknown"
                pcmd = "unknown"
            
            msg = f"[{datetime.datetime.now()}] NEW PROCESS: {name} (PID: {pid})\n    CMD: {cmdline}\n    PARENT: {pname} (PID {ppid})\n    PARENT CMD: {pcmd}\n"
            print(msg)
            with open(log_file, "a", encoding='utf-8') as f:
                f.write(msg + "\n")
                
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
            
    seen_pids = current_pids
    time.sleep(0.5)

print("Monitoring complete.")
