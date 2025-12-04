"""
Phase 10.1: 첫 1시간 진행상황 체크
"""
import json
import sys
from datetime import datetime
from pathlib import Path

def load_monitoring_log():
    """24시간 모니터링 로그 로드"""
    log_path = Path("C:/workspace/agi/outputs/fullstack_24h_monitoring.jsonl")
    if not log_path.exists():
        return []
    
    samples = []
    with open(log_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                samples.append(json.loads(line))
    return samples

def load_orchestrator_state():
    """Orchestrator 상태 파일 로드"""
    state_path = Path("C:/workspace/agi/outputs/full_stack_orchestrator_state.json")
    if not state_path.exists():
        return None
    
    with open(state_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def check_orchestrator_process():
    """Orchestrator 프로세스 확인"""
    import subprocess
    from datetime import timezone, timedelta

    def parse_cim_datetime(value: str):
        if not value:
            return None
        try:
            main, _, rest = value.partition('.')
            dt = datetime.strptime(main, "%Y%m%d%H%M%S")
            micro = 0
            tzinfo = None
            if rest:
                micro_part = rest[:6]
                if micro_part.isdigit():
                    micro = int(micro_part)
                offset_part = rest[6:]
                if offset_part:
                    sign = 1
                    if offset_part[0] == '+':
                        sign = 1
                        offset_val = offset_part[1:]
                    elif offset_part[0] == '-':
                        sign = -1
                        offset_val = offset_part[1:]
                    else:
                        offset_val = offset_part
                    if offset_val.isdigit():
                        minutes = int(offset_val)
                        tzinfo = timezone(sign * timedelta(minutes=minutes))
            if tzinfo:
                return dt.replace(microsecond=micro, tzinfo=tzinfo).astimezone()
            return dt.replace(microsecond=micro)
        except Exception:
            return None

    command = (
        "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
        "Where-Object { $_.CommandLine -like '*full_stack_orchestrator.py*' } | "
        "Select-Object -Property ProcessId, CreationDate, CommandLine | "
        "ConvertTo-Json"
    )
    try:
        result = subprocess.run(
            ['powershell', '-Command', command],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            procs = json.loads(result.stdout)
            if isinstance(procs, dict):
                procs = [procs]
            for proc in procs:
                created = proc.get("CreationDate")
                start_time = parse_cim_datetime(str(created))
                if start_time:
                    proc["Runtime"] = (datetime.now(start_time.tzinfo or None) - start_time).total_seconds()
                else:
                    proc["Runtime"] = 0
            return procs
    except Exception as e:
        print(f"  Warning: Could not check process: {e}", file=sys.stderr)
    return []

def main():
    print("\n" + "="*60)
    print("  Phase 10.1: First Hour Progress Check")
    print("="*60)
    
    # 1. Orchestrator 프로세스 상태
    print("\n[1] Orchestrator Process:")
    procs = check_orchestrator_process()
    runtime = 0
    if procs:
        for proc in procs:
            runtime = proc.get('Runtime', 0)
            pid = proc.get('ProcessId') or proc.get('Id')
            print(f"  ✓ PID {pid}: Running for {runtime:.0f}s ({runtime/60:.1f}min)")
    else:
        print("  ✗ Process NOT FOUND")
        print("    Run: python start_orchestrator.py")
        return 1
    
    # 2. Orchestrator 상태 파일
    print("\n[2] Orchestrator State:")
    state = load_orchestrator_state()
    if state:
        saved_at = datetime.fromisoformat(state['saved_at'])
        age = (datetime.now() - saved_at).total_seconds()
        
        print(f"  Last updated: {age:.0f}s ago")
        print(f"  Learning cycles: {state['state']['learning_cycles']}")
        print(f"  Events processed: {state['event_count']}")
        
        # 컴포넌트 상태
        active = [k for k, v in state['components'].items() if v == 'active']
        print(f"  Components: {', '.join(active)} ({len(active)}/{len(state['components'])})")
    else:
        print("  ✗ State file not found")
    
    # 3. 24h 모니터링
    print("\n[3] 24h Monitoring:")
    samples = load_monitoring_log()
    if samples:
        print(f"  Samples collected: {len(samples)}")
        latest = samples[-1]
        print(f"  Latest timestamp: {latest.get('timestamp', 'N/A')}")
        print(f"  Learning cycles: {latest.get('learning_cycles', 0)}")
        print(f"  Events processed: {latest.get('events_processed', 0)}")
        print(f"  Components active: {latest.get('components_active', 0)}")
    else:
        print("  ⚠ No samples yet")
    
    # 4. 목표 달성 여부
    print("\n[4] First Hour Goals:")
    goals_met = 0
    total_goals = 4
    
    if state:
        cycles = state['state']['learning_cycles']
        if cycles >= 1:
            print(f"  ✓ Learning cycles >= 1: {cycles}")
            goals_met += 1
        else:
            expected_cycles = max(0, int(runtime / 300))  # 5분마다 1사이클
            print(f"  ⏳ Learning cycles: {cycles} (expected ~{expected_cycles})")
        
        events = state['event_count']
        if events > 0:
            print(f"  ✓ Events processed > 0: {events}")
            goals_met += 1
        else:
            print(f"  ⏳ Events processed: {events}")
    else:
        print("  ⏳ State not available")
    
    if samples:
        print(f"  ✓ Monitoring active: {len(samples)} samples")
        goals_met += 1
    else:
        print(f"  ⏳ Monitoring: 0 samples")
    
    if state and len([v for v in state['components'].values() if v == 'active']) >= 3:
        print(f"  ✓ Components active >= 3")
        goals_met += 1
    else:
        print(f"  ⏳ Components: checking...")
    
    # 5. 요약
    print("\n" + "="*60)
    progress_pct = (goals_met / total_goals) * 100
    print(f"  Progress: {goals_met}/{total_goals} goals ({progress_pct:.0f}%)")
    
    if goals_met == total_goals:
        print("  Status: ✅ ALL GOALS MET - Phase 10.1 SUCCESS!")
        return 0
    else:
        print("  Status: ⏳ IN PROGRESS - Keep monitoring")
        print("\n  Next check: Run this script again in 5-10 minutes")
        return 2
    
    print("="*60 + "\n")

if __name__ == "__main__":
    sys.exit(main())
