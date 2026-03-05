# SSH 키 설정 가이드

## 현재 상황
- SSH 비밀번호 인증이 실패하여 자동 동기화가 제대로 작동하지 않습니다
- SSH 키 기반 인증을 설정하면 비밀번호 없이 자동으로 연결할 수 있습니다

## SSH 키 설정 방법

### 1단계: SSH 키 생성 (Windows)
```powershell
# SSH 키가 없으면 생성
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
# Enter를 눌러 기본 경로 사용 (~/.ssh/id_rsa)
# 비밀번호는 비워두거나 설정 (비워두면 자동 로그인 가능)
```

### 2단계: 공개 키를 Linux VM에 복사
```powershell
# 공개 키 내용 확인
Get-Content $env:USERPROFILE\.ssh\id_rsa.pub

# Linux VM에 수동으로 복사하거나 ssh-copy-id 사용
# 옵션 1: 수동 복사 (권장)
# 1. 위에서 복사한 공개 키를 클립보드에 복사
# 2. Linux VM에 SSH로 접속
# 3. 다음 명령 실행:
#    mkdir -p ~/.ssh
#    echo "공개키내용" >> ~/.ssh/authorized_keys
#    chmod 700 ~/.ssh
#    chmod 600 ~/.ssh/authorized_keys

# 옵션 2: ssh-copy-id 사용 (WSL이나 Git Bash 필요)
# ssh-copy-id bino@192.168.119.128
```

### 3단계: 연결 테스트
```powershell
# 비밀번호 없이 연결되는지 테스트
ssh bino@192.168.119.128 "echo 'SSH key authentication works!'"
```

### 4단계: 동기화 스크립트 재시작
```powershell
# 동기화 스크립트가 이제 자동으로 작동합니다
python c:/workspace/agi/scripts/sync_rhythm_from_linux.py
```

## 다음 단계
SSH 키 설정 후에는:
1. ✅ 자동 동기화가 비밀번호 없이 작동
2. ✅ Linux 서비스 상태를 자동으로 모니터링 가능
3. ✅ 동기화 헬스체크 스크립트 실행 가능
