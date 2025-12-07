import sys
from pathlib import Path
import paramiko

# Add scripts directory to path to import credentials_manager
sys.path.insert(0, str(Path(__file__).parent))
from credentials_manager import get_linux_vm_credentials

def install_visualizers():
    creds = get_linux_vm_credentials()
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        print(f"Connecting to {creds['host']}...")
        client.connect(creds['host'], username=creds['user'], password=creds['password'])
        
        print("Installing screenkey and key-mon...")
        # sudo 권한이 필요할 수 있으므로 -S 옵션과 stdin으로 비밀번호 전달
        # key-mon은 일부 배포판에 없을 수 있으므로 screenkey를 우선 설치
        cmd = "echo " + creds['password'] + " | sudo -S apt-get update && echo " + creds['password'] + " | sudo -S apt-get install screenkey -y"
        
        # key-mon 시도 (실패해도 screenkey는 설치됨)
        cmd_full = cmd + " && echo " + creds['password'] + " | sudo -S apt-get install key-mon -y"
        
        stdin, stdout, stderr = client.exec_command(cmd_full, get_pty=True)
        
        # 실시간 출력 확인은 어렵지만 결과 대기
        exit_status = stdout.channel.recv_exit_status()
        
        output = stdout.read().decode()
        print(output)
        
        if exit_status == 0:
            print("\n✅ Installation successful!")
            print("\n[사용 방법]")
            print("1. 리눅스 터미널을 엽니다.")
            print("2. 다음 명령어를 입력하세요:")
            print("   screenkey &")
            print("   (또는 key-mon &)")
        else:
            print(f"\n❌ Installation failed with status {exit_status}")
            
    except Exception as e:
        print(f"Failed: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    install_visualizers()
