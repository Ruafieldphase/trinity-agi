import paramiko
import sys
import time
from pathlib import Path

# Add workspace root to path
sys.path.append("c:\\workspace\\agi\\scripts")
from credentials_manager import get_linux_vm_credentials

def test_self_healing():
    """자가 치유 시스템 테스트"""
    creds = get_linux_vm_credentials()
    host = creds['host']
    user = creds['user']
    password = creds['password']
    
    print("=" * 60)
    print("🧪 자가 치유 시스템 테스트")
    print("=" * 60)
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password, timeout=5)
        
        # 1. 현재 상태 확인
        print("\n1️⃣ 배경자아 서비스 초기 상태 확인...")
        stdin, stdout, stderr = client.exec_command("systemctl --user is-active agi-background-self")
        initial_status = stdout.read().decode().strip()
        print(f"   상태: {initial_status}")
        
        # 2. 서비스를 일부러 중단
        print("\n2️⃣ 배경자아 서비스를 일부러 중단...")
        client.exec_command("systemctl --user stop agi-background-self")
        time.sleep(2)
        
        stdin, stdout, stderr = client.exec_command("systemctl --user is-active agi-background-self")
        stopped_status = stdout.read().decode().strip()
        print(f"   상태: {stopped_status}")
        
        if stopped_status != "inactive":
            print("   ⚠️ 서비스가 완전히 중단되지 않았습니다.")
        
        # 3. 감시견이 자동 복구하는지 대기 (최대 90초)
        print("\n3️⃣ 감시견의 자동 복구를 대기 중... (최대 90초)")
        for i in range(18):  # 18번 * 5초 = 90초
            time.sleep(5)
            stdin, stdout, stderr = client.exec_command("systemctl --user is-active agi-background-self")
            current_status = stdout.read().decode().strip()
            
            print(f"   [{(i+1)*5}초] 상태: {current_status}")
            
            if current_status == "active":
                print("\n✅ 자가 치유 성공! 감시견이 서비스를 자동으로 복구했습니다.")
                client.close()
                return True
        
        print("\n❌ 자가 치유 실패: 90초 내에 서비스가 복구되지 않았습니다.")
        client.close()
        return False
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        return False

if __name__ == "__main__":
    result = test_self_healing()
    print("\n" + "=" * 60)
    if result:
        print("테스트 결과: 🎉 자가 치유 시스템 정상 작동")
    else:
        print("테스트 결과: ⚠️ 자가 치유 시스템 점검 필요")
    print("=" * 60)
