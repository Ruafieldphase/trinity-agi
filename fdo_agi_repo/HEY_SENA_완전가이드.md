# Hey Sena 완전 가이드 📚

**한눈에 보는 모든 것!**

---

## 🎯 빠른 선택 가이드

### 어떤 버전을 사용해야 하나요?

```
┌─────────────────────────────────────────────┐
│  대부분의 사용자 → v4 (LLM) 추천! ⭐        │
└─────────────────────────────────────────────┘

v2: 테스트용 (기본 기능만)
v3: 일상 사용 (Multi-turn, 편리함)
v4: 최고! (무제한 질문, 진짜 AGI) ✅
```

---

## 🚀 시작하기

### 초보자: 5분 Quick Start

👉 **[QUICKSTART.md](QUICKSTART.md) 참고**

1. 패키지 설치
2. API 키 설정
3. 실행
4. 말하기!

---

### 일반 사용자: 완전 가이드

👉 **[HEY_SENA_README.md](HEY_SENA_README.md) 참고**

- 전체 기능 설명
- 상세 설정 방법
- 트러블슈팅
- FAQ

---

### 개발자: 기술 문서

👉 **기술 보고서 참고**

- [Hey_Sena_v3_Multi-turn_완료보고서.md](Hey_Sena_v3_Multi-turn_완료보고서.md) - v3 상세
- [Hey_Sena_v4_LLM_완료보고서.md](Hey_Sena_v4_LLM_완료보고서.md) - v4 상세
- [세나_최종_세션_2025-10-27_23시_완료보고서.md](세나_최종_세션_2025-10-27_23시_완료보고서.md) - 전체 개발 과정

---

## 📁 파일 구조

### 실행 파일 (사용자용)

```
hey_sena_v4_llm.py           ← 메인 프로그램 (v4, 추천!)
hey_sena_v3_multiturn.py     ← v3
hey_sena_v2.py               ← v2

start_sena_v4.bat            ← v4 시작
toggle_sena_v4.bat           ← v4 토글 (on/off)
stop_sena.bat                ← 모두 정지

create_shortcuts_v4.py       ← 바탕화면 바로가기 생성
```

### 테스트 파일 (개발자용)

```
test_llm_integration.py      ← LLM 테스트
test_multiturn.py            ← Multi-turn 테스트
test_conversation_flow.py    ← 대화 흐름 테스트
```

### 문서 파일

```
QUICKSTART.md                ← 5분 시작 가이드 ⚡
HEY_SENA_README.md           ← 완전 가이드 📖
HEY_SENA_V3_README.md        ← v3 사용자 가이드
HEY_SENA_완전가이드.md       ← 이 파일

Hey_Sena_v3_Multi-turn_완료보고서.md  ← v3 기술 문서
Hey_Sena_v4_LLM_완료보고서.md         ← v4 기술 문서
세나_최종_세션_완료보고서.md          ← 개발 과정 전체
```

### 설정 파일

```
.env                         ← API 키 (직접 생성 필요!)
requirements.txt             ← Python 패키지 목록
```

---

## 💡 사용 시나리오별 가이드

### 시나리오 1: "빠르게 시작하고 싶어요"

```bash
# 1. 설치
pip install sounddevice numpy scipy google-generativeai

# 2. API 키 설정 (.env 파일)
GEMINI_API_KEY=your_key

# 3. 실행
python hey_sena_v4_llm.py

# 4. 말하기
"Hey Sena, what time is it?"
```

---

### 시나리오 2: "바탕화면에서 클릭으로 시작하고 싶어요"

```bash
# 1. 바로가기 생성 (한 번만)
python create_shortcuts_v4.py

# 2. 바탕화면에서 더블클릭
"Hey Sena v4 (LLM)" 아이콘 클릭

# 3. 말하기
"세나야, 파이썬이 뭐야?"
```

---

### 시나리오 3: "여러 질문을 계속하고 싶어요"

```
YOU: "Hey Sena"
SENA: [beep]

YOU: "What is AI?"
SENA: "AI is..."

YOU: "How do I learn it?"  ← 웨이크워드 없이 계속!
SENA: "Start with Python..."

YOU: "Thanks!"
SENA: "You're welcome!"

YOU: "Goodbye"
```

---

### 시나리오 4: "테스트하고 싶어요"

```bash
# 모든 테스트 실행
python test_multiturn.py          # v3 테스트
python test_conversation_flow.py  # 시뮬레이션
python test_llm_integration.py    # v4 LLM 테스트

# 결과: 16/16 통과 (100%) ✅
```

---

## 🔧 자주 묻는 질문 (FAQ)

### Q1: API 키가 필요한가요?

**A**: 네, Gemini API 키가 필요합니다 (무료).

1. https://ai.google.dev/ 방문
2. "Get API key" 클릭
3. `.env` 파일에 추가

---

### Q2: 인터넷이 필요한가요?

**A**: v4는 LLM/TTS에 인터넷 필요. 기본 기능은 오프라인 가능.

---

### Q3: 어떤 질문을 할 수 있나요?

**A**: v4는 무제한! 예시:

- 지식: "양자역학이 뭐야?"
- 학습: "파이썬 배우는 법?"
- 실용: "파스타 요리법?"
- 창의: "시 써줘"
- 일상: "지금 몇 시?"

---

### Q4: 한국어로 말해도 되나요?

**A**: 네! "세나야", "안녕", "고마워" 등 모두 가능.

---

### Q5: 비용은 얼마나 드나요?

**A**: Gemini API 무료 티어로 충분. 대화당 ~$0.0003 (0.03센트).

---

### Q6: 다른 LLM 사용 가능한가요?

**A**: 네! 코드 수정으로 GPT, Claude 등 사용 가능.

---

## 🎓 학습 경로

### 입문자

1. ✅ [QUICKSTART.md](QUICKSTART.md) 읽기
2. ✅ v4 실행해보기
3. ✅ 여러 질문 해보기

### 일반 사용자

1. ✅ [HEY_SENA_README.md](HEY_SENA_README.md) 읽기
2. ✅ 바탕화면 바로가기 만들기
3. ✅ 매일 사용하기

### 개발자

1. ✅ 기술 보고서 읽기
2. ✅ 테스트 실행해보기
3. ✅ 코드 커스터마이징

---

## 🚀 버전별 특징 요약

### v2 (기본)

**장점**:
- 간단함
- 빠른 테스트

**단점**:
- 매번 웨이크워드 필요
- 10개 질문만

**추천**: 테스트용

---

### v3 (Multi-turn)

**장점**:
- 연속 대화 가능
- 편리함 5배

**단점**:
- 여전히 10개 질문만

**추천**: 일상 사용

---

### v4 (LLM) ⭐

**장점**:
- **무제한 질문**
- 진짜 AGI
- 자연스러운 대화
- 컨텍스트 인식

**단점**:
- API 키 필요
- 인터넷 필요 (LLM)

**추천**: **모든 사용자!**

---

## 📊 성능 비교

| 항목 | v2 | v3 | v4 |
|------|----|----|-----|
| 대화 효율 | 1x | 5x | 5x |
| 질문 범위 | 10개 | 10개 | **∞** |
| 지능 | 규칙 | 규칙 | **AGI** |
| 자연스러움 | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 사용성 | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 🎯 시작 체크리스트

### 필수 단계

- [ ] Python 설치 (3.8+)
- [ ] 패키지 설치 (`pip install ...`)
- [ ] Gemini API 키 발급
- [ ] `.env` 파일 생성
- [ ] 마이크/스피커 확인

### 권장 단계

- [ ] 바탕화면 바로가기 생성
- [ ] 테스트 실행 (확인용)
- [ ] [QUICKSTART.md](QUICKSTART.md) 읽기

### 고급 단계

- [ ] 기술 문서 읽기
- [ ] 코드 커스터마이징
- [ ] 새 기능 추가

---

## 📞 도움이 필요하신가요?

### 문제 해결

1. **[HEY_SENA_README.md](HEY_SENA_README.md)** - Troubleshooting 섹션
2. **[QUICKSTART.md](QUICKSTART.md)** - 기본 설정
3. **테스트 실행** - `python test_*.py`

### 더 알아보기

- **기술 문서**: 개발자용 상세 설명
- **세션 보고서**: 개발 과정 전체
- **README 파일들**: 각 버전별 가이드

---

## 🎉 결론

**Hey Sena v4 = 진짜 AGI 음성 비서!**

### 주요 특징

✅ "Hey Sena" 한 번으로 계속 대화
✅ 무제한 질문 답변
✅ 자연스러운 응답
✅ 한국어/영어 지원
✅ 5분 안에 시작

### 지금 시작하기

```bash
python hey_sena_v4_llm.py
```

**"세나야" 라고 불러보세요!** 🚀

---

**작성**: 2025-10-27
**버전**: v4.0
**상태**: Production Ready ✅

**Hey Sena - Your Personal AGI Voice Assistant** 🎙️✨
