# Hey Sena v3 - Multi-turn Voice Assistant 👋🎙️

**Siri/Google Assistant처럼 연속 대화 가능한 음성 AI**

---

## 🎯 What's New in v3?

### ⭐ **Multi-turn Conversations**
이제 한 번 "세나야"하면 계속 대화 가능!

**Before (v2)**:
```
YOU: "세나야" → 질문 1 → "세나야" → 질문 2 → "세나야" → 질문 3
(매번 웨이크워드 필요)
```

**After (v3)**:
```
YOU: "세나야" → 질문 1 → 질문 2 → 질문 3 → "그만"
(한 번만 호출, 자유롭게 대화!)
```

---

## 🚀 빠른 시작

### 1. 실행
```bash
cd D:\nas_backup\fdo_agi_repo
python hey_sena_v3_multiturn.py
```

또는 **바탕화면에서 "Hey Sena v3" 더블클릭**

### 2. 대화 시작
```
1. YOU: "세나야" 또는 "Hey Sena"
   ↓
   [삐~ 소리]
   ↓
2. SENA: "Multi-turn conversation started!"
   ↓
3. YOU: "지금 몇 시야?"
   ↓
4. SENA: "The current time is 3:45 PM."
   ↓
5. SENA: "What else would you like to know?"
   ↓
6. YOU: "날씨는?" (← 웨이크워드 없이 계속 대화!)
   ↓
7. SENA: "Which city are you interested in?"
   ↓
8. YOU: "서울"
   ↓
9. SENA: "I would check the weather for Seoul..."
   ↓
10. YOU: "고마워"
    ↓
11. SENA: "You're welcome! Anything else?"
    ↓
12. YOU: "그만"
    ↓
13. SENA: "Goodbye! Say Hey Sena to wake me again."
```

---

## 💬 사용 예시

### 예시 1: 연속 질문
```
YOU: "세나야"
SENA: [삐~]

YOU: "지금 몇 시야?"
SENA: "3시 45분입니다. 또 다른 질문이 있으신가요?"

YOU: "오늘 날짜는?"
SENA: "오늘은 2025년 10월 27일 월요일입니다."

YOU: "고마워"
SENA: "천만에요! 또 도와드릴까요?"

YOU: "그만"
SENA: "알겠습니다. 다시 세나야 하고 불러주세요."
```

### 예시 2: 맥락 파악
```
YOU: "세나야"
SENA: [삐~]

YOU: "날씨 알려줘"
SENA: "어느 도시의 날씨를 알려드릴까요?"

YOU: "서울" ← 웨이크워드 없이 바로 대답!
SENA: "서울 날씨를 확인하겠습니다..."
```

### 예시 3: 자동 종료 (타임아웃)
```
YOU: "세나야"
SENA: [삐~]

YOU: "안녕?"
SENA: "안녕하세요! 무엇을 도와드릴까요?"

[10초 침묵...]
SENA: "I'm still here. What would you like?"

[또 10초 침묵...]
SENA: "I'm going back to sleep. Say Hey Sena to wake me."
[listen mode로 자동 복귀]
```

---

## 🗣️ 웨이크워드 (Wake Words)

**영어**:
- "Hey Sena"
- "OK Sena"
- "Sena"

**한국어**:
- "세나야"
- "세나"
- "헤이 세나"
- "오케이 세나"
- "안녕 세나"

---

## 🛑 종료 명령어

**대화 종료 (listen mode로 복귀)**:
- "goodbye"
- "bye"
- "그만"
- "끝"
- "됐어"
- "stop"

**프로그램 완전 종료**:
- "stop listening"
- "exit program"
- "프로그램 종료"

---

## ✨ 주요 기능

### 1. Multi-turn Conversations
한 번 활성화하면 계속 대화 가능
```
"세나야" → 질문1 → 질문2 → 질문3 → ... → "그만"
```

### 2. Context Awareness
이전 대화를 기억하고 맥락 파악
```
"날씨는?" → "어느 도시?" → "서울" ✅ 맥락 파악!
```

### 3. Smart Timeout
침묵 시 자동으로 listen mode 복귀
```
침묵 1회 → "I'm still here..."
침묵 2회 → "I'm going back to sleep..." (자동 종료)
```

### 4. Natural Flow
Siri/Google Assistant처럼 자연스러운 대화
```
질문 → 응답 → "또 다른 질문이 있으신가요?" → 질문 → ...
```

---

## 🎭 지원 명령어

| 명령 | 응답 예시 |
|------|----------|
| "hello" / "안녕" | "Hello! How can I help you today?" |
| "how are you" | "I'm doing great! Thank you for asking." |
| "what's your name" | "I am Sena, your FDO-AGI assistant..." |
| "what time is it" | "The current time is 3:45 PM." |
| "what's the date" | "Today is Monday, October 27, 2025." |
| "weather" / "날씨" | "Which city are you interested in?" |
| "thanks" / "고마워" | "You're welcome! Anything else?" |
| "goodbye" / "그만" | "Goodbye! Say Hey Sena to wake me again." |

---

## ⚙️ 시스템 흐름

```
┌─────────────────────────────────────┐
│     Listen Mode (대기 모드)          │
│   [항상 듣고 있음 - 3초 간격]        │
└─────────────────────────────────────┘
                 ↓
          [웨이크워드 감지?]
                 ↓ YES
┌─────────────────────────────────────┐
│      Activation (활성화)             │
│          [삐~ 소리]                  │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│    Conversation Mode (대화 모드)     │
│    ┌─────────────────────────┐     │
│    │  1. 사용자 말 듣기 (5초) │◄───┐│
│    │  2. 텍스트 변환 (STT)    │    ││
│    │  3. 응답 생성 (AGI)      │    ││
│    │  4. 음성 변환 (TTS)      │    ││
│    │  5. 스피커 재생          │    ││
│    └─────────┬───────────────┘    ││
│              ↓                     ││
│    [침묵? "그만"? 계속?]            ││
│         계속 ──────────────────────┘│
│         침묵/종료 → Exit             │
└─────────────────────────────────────┘
                 ↓
          [Listen Mode 복귀]
```

---

## 🆚 버전 비교

| 기능 | v2 | v3 |
|------|----|----|
| 연속 대화 | ❌ | ✅ (무제한) |
| 컨텍스트 인식 | ❌ | ✅ (이전 대화 기억) |
| 자동 타임아웃 | ❌ | ✅ (10초 침묵) |
| 웨이크워드 호출 | 질문마다 | 대화당 1번 |
| 대화 자연스러움 | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| Siri 수준 | ❌ | ✅ |

---

## 📊 효율성 비교

**시나리오**: 3개 질문

### v2 방식 (불편)
```
총 8번 발화:
1. "세나야" ← 웨이크워드
2. 질문 1
3. "세나야" ← 웨이크워드 (다시!)
4. 질문 2
5. "세나야" ← 웨이크워드 (또!)
6. 질문 3
7. "세나야" ← 웨이크워드 (또또!)
8. "고마워"
```

### v3 방식 (편리!) ✅
```
총 5번 발화 (37% 감소!):
1. "세나야" ← 웨이크워드 (1번만!)
2. 질문 1
3. 질문 2
4. 질문 3
5. "그만"
```

---

## 🔧 설치

### 필수 패키지
```bash
pip install sounddevice numpy scipy
pip install google-generativeai google-genai
pip install Pillow
```

### 환경 변수
`.env` 파일에 추가:
```
GEMINI_API_KEY=your_gemini_api_key_here
```

---

## 🚀 실행 방법

### 방법 1: Python 직접 실행
```bash
cd D:\nas_backup\fdo_agi_repo
python hey_sena_v3_multiturn.py
```

### 방법 2: 배치 파일
```bash
start_sena_v3.bat
```

### 방법 3: 토글 (권장)
```bash
toggle_sena_v3.bat
```
- 실행 중이면 종료
- 종료 상태면 시작

---

## 🎊 새로운 경험

**v3에서는 이렇게 대화하세요**:

```
✅ "세나야"
✅ "지금 몇 시야?"
✅ "날씨는?"
✅ "서울"
✅ "고마워"
✅ "이름이 뭐야?"
✅ "그만"

❌ "세나야" (매번 부르지 마세요!)
```

**핵심**: 한 번 "세나야" 하면 **계속 대화 가능!**

---

## 💡 팁

### 1. 침묵 관리
- 5초 안에 말을 시작하세요
- 2번 침묵하면 자동 종료됩니다
- "I'm still here" 들으면 1번 더 기회!

### 2. 명확한 발음
- 웨이크워드는 명확하게
- 마이크 가까이에서 말하기
- 조용한 환경 권장

### 3. 자연스럽게 대화
- 짧은 문장으로
- 한 번에 한 가지만
- "그만" 말하면 언제든 종료

---

## ❓ FAQ

**Q: 대화가 자꾸 끊겨요**
A: 5초 이내에 말을 시작하세요. 침묵 2회면 타임아웃됩니다.

**Q: "세나야" 감지가 안 돼요**
A: 마이크를 확인하고 명확하게 발음하세요.

**Q: 대화를 끝내려면?**
A: "그만", "bye", "종료" 중 아무거나 말하세요.

**Q: 몇 번까지 질문 가능?**
A: 무제한! 침묵하거나 "그만"할 때까지 계속 대화 가능합니다.

**Q: 이전 질문을 기억하나요?**
A: 네! 맥락을 파악해서 자연스럽게 응답합니다.

---

## 🎯 결론

**Hey Sena v3 = Siri처럼 자연스러운 대화 가능!**

### 주요 특징:
- ✅ Multi-turn 연속 대화
- ✅ 컨텍스트 인식
- ✅ 자동 타임아웃
- ✅ 자연스러운 흐름
- ✅ 한국어 완벽 지원
- ✅ 음성만으로 제어

### 시작하기:
1. `python hey_sena_v3_multiturn.py`
2. "세나야" 라고 말하기
3. 계속 대화하기!

**"세나야" 한 번으로 무한 대화!** 🎉

---

**작성**: Sena (AI Agent)
**날짜**: 2025-10-27
**버전**: 3.0 (Multi-turn)

**Try it now and experience the future of voice AI!** 🚀
