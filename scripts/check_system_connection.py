#!/usr/bin/env python3
"""
System Connection Health Check (시스템 연결 점검)
================================================
윈도우(의식) ↔ 배경자아 ↔ 리눅스(무의식) 연결 상태 점검
"""
import json
import sys
from pathlib import Path
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))
from credentials_manager import get_linux_vm_credentials

import paramiko

# Configuration
WORKSPACE_ROOT = Path(__file__).parent.parent
OUTPUTS_DIR = WORKSPACE_ROOT / "outputs"

def check_consciousness_layer():
    """의식층 (Windows) 점검"""
    print("=" * 60)
    print("🧠 의식층 (Windows) 점검")
    print("=" * 60)
    
    # 1. Conscious Alert (L3)
    alert_file = OUTPUTS_DIR / "conscious_alert.md"
    if alert_file.exists():
        with open(alert_file, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"\n✅ conscious_alert.md 존재")
        print(f"   마지막 수정: {datetime.fromtimestamp(alert_file.stat().st_mtime)}")
        # Extract insight
        for line in content.split('\n'):
            if 'Insight' in line or '깨달음' in line:
                print(f"   💡 {line.strip()}")
    else:
        print(f"\n⚠️  conscious_alert.md 없음")
    
    # 2. Conscious Insight (L2)
    insight_file = OUTPUTS_DIR / "conscious_insight.md"
    if insight_file.exists():
        with open(insight_file, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"\n✅ conscious_insight.md 존재")
        print(f"   내용: {content.strip()[:100]}")
    else:
        print(f"\n⚠️  conscious_insight.md 없음")
    
    # 3. Background Self State
    bg_state_file = OUTPUTS_DIR / "alpha_background_self_state.json"
    if bg_state_file.exists():
        with open(bg_state_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"\n✅ 배경자아 상태: {data.get('state', 'unknown')}")
        print(f"   Drift Score: {data.get('drift_score', 0):.4f}")
        print(f"   마지막 업데이트: {data.get('timestamp', 'unknown')[:19]}")
    else:
        print(f"\n⚠️  배경자아 상태 파일 없음")

def check_unconscious_layer():
    """무의식층 (Linux) 점검"""
    print("\n" + "=" * 60)
    print("🌊 무의식층 (Linux) 점검")
    print("=" * 60)
    
    creds = get_linux_vm_credentials()
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(creds['host'], username=creds['user'], password=creds['password'], timeout=10)
        
        # 1. Services Status
        print(f"\n🔧 서비스 상태:")
        cmd = "systemctl --user is-active agi-rhythm agi-body agi-collaboration"
        stdin, stdout, stderr = client.exec_command(cmd)
        services = ["agi-rhythm", "agi-body", "agi-collaboration"]
        statuses = stdout.read().decode("utf-8").strip().split('\n')
        
        all_active = True
        for svc, status in zip(services, statuses):
            icon = "✅" if status == "active" else "❌"
            print(f"   {icon} {svc}: {status}")
            if status != "active":
                all_active = False
        
        # 2. ATP System
        print(f"\n⚡ ATP 시스템:")
        cmd = "cat /home/bino/agi/outputs/mitochondria_state.json 2>/dev/null || echo '{}'"
        stdin, stdout, stderr = client.exec_command(cmd)
        atp_output = stdout.read().decode("utf-8").strip()
        
        if atp_output and atp_output != '{}':
            try:
                atp_data = json.loads(atp_output)
                atp_level = atp_data.get('atp_level', 0)
                status = atp_data.get('status', 'unknown')
                print(f"   ATP Level: {atp_level:.1f}")
                print(f"   Status: {status}")
            except:
                print(f"   ⚠️  ATP 데이터 파싱 실패")
        else:
            print(f"   ℹ️  ATP 파일 없음 (정상 - 아직 미구현)")
        
        # 3. Recent Rhythm Output
        print(f"\n🎵 리듬 출력:")
        cmd = "ls -lh /home/bino/agi/outputs/thought_stream_latest.json /home/bino/agi/outputs/feeling_latest.json 2>/dev/null"
        stdin, stdout, stderr = client.exec_command(cmd)
        output = stdout.read().decode("utf-8").strip()
        
        if output:
            for line in output.split('\n'):
                if 'thought_stream' in line:
                    print(f"   ✅ thought_stream_latest.json 존재")
                if 'feeling' in line:
                    print(f"   ✅ feeling_latest.json 존재")
        
        # 4. L1/L2/L3 Cache
        print(f"\n🧠 인지 캐시 (L1/L2/L3):")
        cmd = "wc -l /home/bino/agi/outputs/cache/*.jsonl 2>/dev/null"
        stdin, stdout, stderr = client.exec_command(cmd)
        output = stdout.read().decode("utf-8").strip()
        
        if output:
            for line in output.split('\n'):
                if 'l1_sensory' in line:
                    count = line.strip().split()[0]
                    print(f"   L1 (Sensory): {count} 항목")
                elif 'l2_working' in line:
                    count = line.strip().split()[0]
                    print(f"   L2 (Working): {count} 항목")
                elif 'l3_deep' in line:
                    count = line.strip().split()[0]
                    print(f"   L3 (Deep): {count} 항목")
        else:
            print(f"   ℹ️  캐시 파일 없음 (첫 실행 전)")
        
        client.close()
        
        print("\n" + "=" * 60)
        if all_active:
            print("✅ 연결 상태: 정상")
            print("   의식층 ↔ 배경자아 ↔ 무의식층 모두 작동 중")
        else:
            print("⚠️  연결 상태: 일부 서비스 비활성")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 무의식층 연결 실패: {e}")
        client.close()

def main():
    print("\n🔍 시스템 연결 점검 시작...")
    print(f"   시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    check_consciousness_layer()
    check_unconscious_layer()
    
    print("\n✅ 점검 완료\n")

if __name__ == "__main__":
    main()
