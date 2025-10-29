# GitHub Copilot 단축 명령어

## 오케스트레이터 Assist 명령

빠른 실행을 위한 터미널 스니펫:

```powershell
# 상태 확인
D:\nas_backup\LLM_Unified\.venv\Scripts\python.exe D:\nas_backup\LLM_Unified\ion-mentoring\extension_api.py assist --prompt "상태 확인" --workspace-dir "D:\nas_backup"

# 카나리 10% 배포 (드라이런)
D:\nas_backup\LLM_Unified\.venv\Scripts\python.exe D:\nas_backup\LLM_Unified\ion-mentoring\extension_api.py assist --prompt "카나리 10% 배포" --workspace-dir "D:\nas_backup"

# 카나리 10% 배포 (실행)
D:\nas_backup\LLM_Unified\.venv\Scripts\python.exe D:\nas_backup\LLM_Unified\ion-mentoring\extension_api.py assist --prompt "카나리 10% 배포" --workspace-dir "D:\nas_backup" --execute

# 프로브 젠틀 (3회)
D:\nas_backup\LLM_Unified\.venv\Scripts\python.exe D:\nas_backup\LLM_Unified\ion-mentoring\extension_api.py assist --prompt "프로브 젠틀" --workspace-dir "D:\nas_backup" --execute

# 프로브 노멀 (10회)
D:\nas_backup\LLM_Unified\.venv\Scripts\python.exe D:\nas_backup\LLM_Unified\ion-mentoring\extension_api.py assist --prompt "프로브 노멀" --workspace-dir "D:\nas_backup" --execute

# 롤백
D:\nas_backup\LLM_Unified\.venv\Scripts\python.exe D:\nas_backup\LLM_Unified\ion-mentoring\extension_api.py assist --prompt "롤백" --workspace-dir "D:\nas_backup" --execute
```

## 단축 별칭 설정 (PowerShell Profile)

```powershell
# 프로필에 추가: $PROFILE
function ion-assist { D:\nas_backup\LLM_Unified\.venv\Scripts\python.exe D:\nas_backup\LLM_Unified\ion-mentoring\extension_api.py assist --workspace-dir "D:\nas_backup" @args }
function ion-status { ion-assist --prompt "상태 확인" }
function ion-deploy { ion-assist --prompt "카나리 10% 배포" --execute }
function ion-probe { ion-assist --prompt "프로브 노멀" --execute }
function ion-rollback { ion-assist --prompt "롤백" --execute }
```

## VS Code Tasks.json 스니펫

```json
{
  "label": "Assist: 상태 확인",
  "type": "shell",
  "command": "powershell",
  "args": [
    "-NoProfile",
    "-ExecutionPolicy",
    "Bypass",
    "-Command",
    "D:\\nas_backup\\LLM_Unified\\.venv\\Scripts\\python.exe D:\\nas_backup\\LLM_Unified\\ion-mentoring\\extension_api.py assist --prompt '상태 확인' --workspace-dir 'D:\\nas_backup'"
  ],
  "group": "test"
}
```
