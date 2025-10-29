# 🚀 Gitko Agent Extension - 빠른 시작 가이드

## ⚡ 3분 안에 시작하기

### 1️⃣ 확장 실행 (개발 모드)

```powershell
# 이미 디렉토리에 있다면
F5 키를 누르세요!
```

### 2️⃣ Extension Development Host에서 테스트

새로 열린 VS Code 창에서:

1. **GitHub Copilot Chat 열기** (Ctrl+Shift+I 또는 사이드바의 채팅 아이콘)

2. **자연어로 요청하기**
   ```
   이 코드를 리팩토링해줘
   → Sian 에이전트 자동 실행!
   ```

3. **또는 @gitko 명령어 사용**
   ```
   @gitko /help
   → 도움말 확인
   
   @gitko 코드 리뷰해줘
   → Lubit 에이전트 실행
   ```

### 3️⃣ 로그 확인하기

- **View** > **Output** > **드롭다운에서 "Gitko Agent" 선택**
- 모든 실행 로그를 실시간으로 확인할 수 있습니다!

## 🔧 Python 환경 설정

첫 실행 시 "Python 환경을 찾을 수 없습니다" 메시지가 나온다면:

1. **설정 열기**: `Ctrl + ,`
2. **"Gitko Agent" 검색**
3. **경로 입력**:
   - Python Path: `D:/nas_backup/LLM_Unified/.venv/Scripts/python.exe`
   - Script Path: `D:/nas_backup/LLM_Unified/ion-mentoring/gitko_cli.py`
   - Working Directory: `D:/nas_backup/LLM_Unified/ion-mentoring`

또는 자동 탐지가 실패한 경우만 설정하세요!

## 💡 사용 팁

### 자동 호출 (권장!)
GitHub Copilot이 자동으로 적절한 에이전트를 선택합니다:

```
"성능을 개선해줘" → Sian
"보안 취약점 찾아줘" → Lubit  
"프로젝트 전체 개선해줘" → Gitko
```

### 명령어로 직접 호출
```
@gitko /review    # 코드 리뷰
@gitko /improve   # 코드 개선
@gitko /parallel  # 병렬 작업
@gitko /help      # 도움말
```

## 🎯 체크리스트

- [ ] F5로 Extension Development Host 실행됨
- [ ] GitHub Copilot Chat 열림
- [ ] `@gitko /help` 명령어 실행됨
- [ ] Output Channel에서 로그 확인됨
- [ ] Python 환경 정상 확인됨

모두 체크되었다면 준비 완료! 🎉

## ❓ 문제 해결

### "Python 환경을 찾을 수 없습니다"
→ 위의 "Python 환경 설정" 참조

### "에이전트가 응답하지 않습니다"
→ Output Channel에서 에러 로그 확인

### "확장이 활성화되지 않습니다"
→ Watch 모드가 실행 중인지 확인 (터미널에 "watch" 탭 있어야 함)

## 📚 더 자세한 정보

- **README.md** - 전체 기능 설명
- **SETUP_GUIDE.md** - 상세 설정 가이드
- **COMPLETION_REPORT.md** - 개발 완료 보고서
- **AUTOMATIC_AGENT_GUIDE.md** - 자동 호출 가이드

---

**Ready to go! Happy coding! 🚀**
