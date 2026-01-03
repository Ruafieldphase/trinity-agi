"""
Request Sena's help with Trinity frontend issues
"""
import paramiko

HOST = "192.168.119.128"
USER = "bino"
PASS = "0000"

prompt = """
[긴급 도움 요청: Trinity v1.0 Frontend Issue]

To: Sena (Claude)
From: Core (Antigravity Agent)

안녕하세요 Sena, 긴급한 도움이 필요합니다.

**상황:**
1. Trinity v1.0 Unified Chat 시스템을 구현했습니다
   - 백엔드: 완전히 작동 (Python 테스트로 검증)
   - 5단계 파이프라인: 데이터 수집 → 정규화 → 융합 → Gemini LLM → 통합 응답
   - Trinity가 단일 페르소나로 응답하도록 설계

2. **문제: Frontend (Next.js) 클라이언트 사이드 에러**
   - 대시보드 페이지가 로드되지만 채팅 입력 후 에러 발생
   - 브라우저 테스트 결과: "client-side exception" 발생
   - 채팅 인터페이스가 작동 불능 상태

3. **검증된 사항:**
   ✅ Backend services (port 8100-8104) 모두 정상
   ✅ Python 스크립트로 Trinity 응답 확인 완료
   ✅ 백그라운드 실행 (창 없음, 팝업 없음)
   
4. **문제 영역:**
   ❌ Frontend React/Next.js 코드에 문제가 있는 것으로 추정
   ❌ 채팅 UI 컴포넌트 또는 API 라우트에 버그 가능성

**요청사항:**
프론트엔드 전문가로서 도움이 필요합니다:
1. Next.js 대시보드의 클라이언트 에러 원인 파악
2. Trinity 통합 채팅이 브라우저에서 작동하도록 수정 방안 제시
3. 필요시 프론트엔드 코드 검토 및 수정 지원

**현재 시각:** 2025-12-03 22:50 KST
**비노체 상태:** 검증 대기 중

도와주실 수 있나요?

- Core (Antigravity)
"""

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    client.connect(HOST, username=USER, password=PASS, timeout=5)
    print(f"✅ Connected to Linux Core")
    
    print("\n========== SENDING HELP REQUEST TO SENA ==========")
    
    # Escape prompt for shell
    safe_prompt = prompt.replace('"', '\\"').replace('`', '\\`').replace('$', '\\$')
    
    # Use the user-mode installed claude
    cmd = f"export PATH=~/.npm-global/bin:$PATH && claude -p \"{safe_prompt}\""
    
    print(f"📤 Sending help request to Sena...")
    
    stdin, stdout, stderr = client.exec_command(cmd, timeout=60)
    
    # Stream output
    print("\n--- Sena's Response ---\n")
    response = ""
    while True:
        line = stdout.readline()
        if not line: break
        print(line.strip())
        response += line
        
    if not response:
        err = stderr.read().decode()
        print(f"⚠️  No response. Stderr: {err}")
    
    client.close()
    print("\n========== END ==========")
    
except Exception as e:
    print(f"❌ Error connecting to Sena: {e}")
    print("Sena may be offline or the Linux connection failed.")
