# Gitko Agent Extension - 설정 가이드

## Python 환경 설정하기

Gitko Agent Extension이 제대로 작동하려면 Python 환경이 필요합니다.

### 1단계: Python 설치 확인

PowerShell에서 실행:

```powershell
python --version
```

Python이 설치되어 있지 않다면 [python.org](https://www.python.org/downloads/)에서 다운로드하세요.

### 2단계: gitko_cli.py 스크립트 위치 확인

Python 스크립트 파일이 어디에 있는지 확인하세요.

### 3단계: VS Code 설정

`Ctrl + ,`를 눌러 설정을 열고 "Gitko Agent"를 검색한 후 다음을 입력:

```json
{
  "gitkoAgent.pythonPath": "C:/Python39/python.exe",
  "gitkoAgent.scriptPath": "C:/Projects/gitko/gitko_cli.py",
  "gitkoAgent.workingDirectory": "C:/Projects/gitko"
}
```

**경로는 사용자 환경에 맞게 수정하세요!**

### 4단계: 설정 확인

VS Code를 재시작하고 `@gitko` 명령어를 테스트하세요.

## 자주 묻는 질문

### Q: "Python 환경을 찾을 수 없습니다" 오류가 나옵니다

A: 위의 3단계를 따라 수동으로 경로를 설정하세요.

### Q: Output Channel은 어디서 확인하나요?

A: `View` > `Output` > 드롭다운에서 "Gitko Agent" 선택

### Q: 에이전트가 응답하지 않습니다

A: 
1. Output Channel에서 오류 로그 확인
2. Python 스크립트를 직접 실행해보세요:
   ```powershell
   python path/to/gitko_cli.py "test message"
   ```
3. 타임아웃 설정을 늘려보세요 (기본 5분)

## 도움이 필요하신가요?

이슈를 생성하거나 개발자에게 문의하세요.
