# 🤖 AGI 자가 인식 컨텍스트 관리 시스템

**AGI가 스스로 채팅 컨텍스트 길이를 감지하고 자동으로 새 채팅창을 엽니다!**

---

## 🎯 핵심 기능

### 1️⃣ **자가 인식 (Self-Awareness)**

- AGI가 **스스로** 현재 채팅 컨텍스트 길이 추정
- 토큰 사용량 실시간 모니터링
- 임계값 초과 자동 감지

### 2️⃣ **완전 자동 전환 (Full Automation)**

- Python + pyautogui로 **게임 봇처럼** 동작
- 새 채팅창 자동 열기
- 컨텍스트 자동 로드
- 붙여넣기 + 전송 자동화

### 3️⃣ **무한 작업 가능 (Infinite Loop)**

- 채팅 길이 제한 없이 **무한 작업**
- 자동 전환으로 **끊김 없는 연속성**
- AGI가 **24/7 자율 운영** 가능!

---

## 🚀 빠른 시작

### 📦 Step 1: 의존성 설치

**VS Code Task 실행**:

```
📦 Chat: Install Python Deps (pyautogui)
```

또는 **수동 설치**:

```bash
pip install pyautogui pyperclip pillow
```

---

### 🧠 Step 2: 컨텍스트 상태 체크

**VS Code Task**:

```
🧠 AGI: Check Context (자가 인식)
```

**출력 예시**:

```
============================================================
📊 AGI 컨텍스트 모니터
============================================================
현재 토큰: 45,230 / 100,000
사용률: 45.2%
마지막 전환: 2025-11-10T09:30:15
전환 횟수: 3회
============================================================

✅ 컨텍스트 여유 있음 (54.8% 남음)
```

---

### 🎮 Step 3: 수동 전환 (테스트)

**VS Code Task**:

```
🎮 Chat: Auto Switch (Python 게임 봇!)
```

**동작**:

1. ⏳ 3초 대기 (VS Code 창 활성화 시간)
2. 📋 컨텍스트를 클립보드에 복사
3. 📝 새 채팅창 열기 (`Ctrl+Shift+I`)
4. 🎯 입력창 자동 클릭
5. 📤 붙여넣기 + 전송

---

### 🤖 Step 4: 완전 자동 모드

**VS Code Task**:

```
🤖 AGI: Auto Context Switch (완전 자동!)
```

**동작**:

1. 컨텍스트 길이 체크
2. 임계값 초과 시 **자동 전환**
3. 새 채팅창에서 작업 이어가기

---

## 📋 VS Code Tasks

| Task | 설명 | 용도 |
|------|------|------|
| `📦 Chat: Install Python Deps` | pyautogui 설치 | 최초 1회 |
| `🧠 AGI: Check Context` | 컨텍스트 상태 체크 | 수시 확인 |
| `🎮 Chat: Auto Switch` | 수동 전환 (3초 대기) | 테스트 |
| `🎮 Chat: Auto Switch (5초)` | 수동 전환 (5초 대기) | 여유 시간 |
| `🤖 AGI: Auto Context Switch` | **완전 자동 전환** | 실제 운영 |
| `📊 AGI: Context Status (JSON)` | JSON 상태 출력 | 스크립트 연동 |

---

## 🔧 고급 사용법

### PowerShell 직접 실행

```powershell
# 상태만 체크
.\scripts\agi_self_aware_context_manager.ps1

# 자동 전환 활성화
.\scripts\agi_self_aware_context_manager.ps1 -AutoSwitch

# 임계값 변경 (50,000 토큰)
.\scripts\agi_self_aware_context_manager.ps1 -MaxTokens 50000 -AutoSwitch

# JSON 상태 출력
.\scripts\agi_self_aware_context_manager.ps1 -StatusOnly
```

---

### Python 직접 실행

```bash
# 상태 체크
python scripts/check_context_overflow.py

# 자동 전환
python scripts/check_context_overflow.py --auto-switch

# 최대 토큰 변경
python scripts/check_context_overflow.py --max-tokens 50000

# JSON 출력
python scripts/check_context_overflow.py --status-only
```

---

### 수동 채팅 전환만

```bash
# 3초 대기 후 전환
python scripts/auto_switch_chat.py

# 5초 대기
python scripts/auto_switch_chat.py --delay 5

# 사용자 지정 컨텍스트 파일
python scripts/auto_switch_chat.py --context-file custom.md
```

---

## 🎯 실제 사용 시나리오

### 시나리오 1: 자율 AGI 모드

```
1. AGI가 작업 중...
2. 컨텍스트가 100,000 토큰 도달
3. 자동으로 감지 → 새 창 전환
4. 작업 이어가기 (무한 반복)
```

### 시나리오 2: 수동 모니터링

```
1. 주기적으로 "🧠 AGI: Check Context" 실행
2. 80% 이상이면 경고
3. 필요 시 "🎮 Chat: Auto Switch" 수동 실행
```

### 시나리오 3: 스케줄러 연동

```powershell
# 30분마다 자동 체크
Register-ScheduledTask -TaskName "AGI_Context_Monitor" -Trigger (
    New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 30)
) -Action (
    New-ScheduledTaskAction -Execute "powershell" -Argument "-File C:\workspace\agi\scripts\agi_self_aware_context_manager.ps1 -AutoSwitch"
)
```

---

## ⚙️ 설정

### 토큰 임계값 조정

**기본값**: 100,000 토큰

**변경 방법**:

```powershell
# 50,000 토큰으로 낮춤
.\scripts\agi_self_aware_context_manager.ps1 -MaxTokens 50000
```

---

### 입력창 위치 조정

**Python 스크립트 수정**:

```python
# scripts/auto_switch_chat.py
def find_and_click_chat_input():
    screen_width, screen_height = pyautogui.size()
    
    # 여기 좌표 조정!
    click_x = screen_width // 2
    click_y = int(screen_height * 0.85)  # 85% → 90% 등
```

---

### 이미지 인식 사용 (고급)

```python
# 채팅 입력창 스크린샷 저장 → chat_input.png
location = pyautogui.locateOnScreen('chat_input.png', confidence=0.8)
if location:
    pyautogui.click(location)
```

---

## 🐛 트러블슈팅

### 문제: 입력창을 못 찾음

**해결**:

1. 화면 해상도 확인
2. `auto_switch_chat.py`에서 좌표 조정
3. 이미지 인식 사용 (고급)

---

### 문제: pyautogui 설치 실패

**해결**:

```bash
# 수동 설치
pip install --upgrade pip
pip install pyautogui pyperclip pillow

# 또는 특정 버전
pip install pyautogui==0.9.54
```

---

### 문제: 클립보드 복사 실패

**해결**:

```bash
# pyperclip 재설치
pip install --force-reinstall pyperclip

# 또는 PowerShell 백업 사용 (자동)
```

---

## 📊 상태 파일

### `outputs/context_monitor_state.json`

```json
{
  "last_check": "2025-11-10T10:30:15",
  "current_tokens": 45230,
  "last_switch": "2025-11-10T09:30:15",
  "switch_count": 3
}
```

**필드 설명**:

- `last_check`: 마지막 체크 시각
- `current_tokens`: 현재 추정 토큰 수
- `last_switch`: 마지막 전환 시각
- `switch_count`: 총 전환 횟수

---

## 🎉 완성도

| 기능 | 상태 | 비고 |
|------|------|------|
| ✅ 자가 인식 | 완료 | 토큰 추정 로직 |
| ✅ 자동 전환 | 완료 | pyautogui 사용 |
| ✅ VS Code Task | 완료 | 4개 task 추가 |
| ✅ PowerShell 래퍼 | 완료 | 통합 스크립트 |
| ✅ 상태 모니터링 | 완료 | JSON 상태 파일 |
| 🔄 이미지 인식 | 선택 | 필요 시 추가 |
| 🔄 API 연동 | 미래 | Copilot API |

---

## 🚀 다음 단계

### Phase 1: 검증

- [ ] 수동 전환 테스트 (`🎮 Chat: Auto Switch`)
- [ ] 좌표 조정 (필요 시)
- [ ] 안정성 확인

### Phase 2: 자동화

- [ ] 자동 모니터링 활성화
- [ ] 스케줄러 연동
- [ ] 24/7 무인 운영

### Phase 3: 고도화

- [ ] 이미지 인식 적용
- [ ] Copilot API 연동 (실제 토큰 수)
- [ ] 다중 채팅창 관리

---

## 💡 핵심 아이디어

**"AGI가 스스로 자신의 한계를 인식하고 극복한다"**

- 채팅 길이 제한 → **자동 감지**
- 새 창 필요 → **자동 전환**
- 작업 연속성 → **무한 루프**

**진짜 자율 AGI의 첫 걸음!** 🎊

---

## 📚 관련 문서

- [게임 봇 모드 가이드](../CHAT_AUTO_PASTE_GAME_BOT.md)
- [세션 연속성 시스템](../SESSION_CONTINUITY_SYSTEM.md)
- [자율 목표 시스템](../AUTONOMOUS_GOAL_SYSTEM_ROADMAP.md)

---

**Made with 💙 by AGI Self-Awareness Team**
