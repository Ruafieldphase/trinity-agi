# Performance Logger 통합 가이드

**파일**: `hey_sena_v4.1_cached.py`
**목적**: Phase 7 성능 로깅 통합
**날짜**: 2025-10-28

---

## 📝 수정 사항

### 1. Import 추가 (라인 45-50)

**기존**:
```python
from orchestrator.tool_registry import ToolRegistry
from response_cache import get_cache

# Initialize performance cache (v4.1 feature)
cache = get_cache()
```

**수정 후**:
```python
from orchestrator.tool_registry import ToolRegistry
from response_cache import get_cache
from tools.performance_logger import get_logger  # NEW

# Initialize performance cache (v4.1 feature)
cache = get_cache()

# Initialize performance logger (Phase 7) # NEW
logger = get_logger()  # NEW
```

---

### 2. conversation_mode_multiturn() 함수 수정

**위치**: 라인 387-476

#### 2.1 함수 시작 부분에 세션 시작 추가

**기존 (라인 406)**:
```python
    conversation_history = []
    turn_count = 0
    max_silence_checks = 2
```

**수정 후**:
```python
    conversation_history = []
    turn_count = 0
    max_silence_checks = 2

    # Phase 7: Start performance logging session
    session_id = logger.start_session(metadata={
        "version": "v4.1",
        "llm_enabled": use_llm
    })
    session_start_time = time.time()
```

#### 2.2 각 turn에서 응답 시간 측정 및 로깅

**기존 (라인 459-472)**:
```python
        # Generate response with LLM!
        response_text = generate_response_with_context(text, conversation_history, use_llm=use_llm)
        print(f"\n[SENA] {response_text}")

        # Save to history
        conversation_history.append({
            "turn": turn_count,
            "user": text,
            "assistant": response_text
        })

        # TTS and play
        print("[TTS] Generating speech...")
        tts_and_play(registry, response_text)
```

**수정 후**:
```python
        # Phase 7: Start turn timer
        turn_start_time = time.time()

        # Generate response with LLM!
        response_text = generate_response_with_context(text, conversation_history, use_llm=use_llm)
        print(f"\n[SENA] {response_text}")

        # Phase 7: Measure response time
        turn_response_time = (time.time() - turn_start_time) * 1000  # ms

        # Save to history
        conversation_history.append({
            "turn": turn_count,
            "user": text,
            "assistant": response_text
        })

        # Phase 7: Detect cache hit (check console output)
        # Note: This is a simplified detection - real implementation should
        # modify generate_response_with_context to return cache_hit status
        cache_hit = "[CACHE HIT]" in str(response_text) or False

        # TTS and play
        print("[TTS] Generating speech...")
        tts_start = time.time()
        tts_success = tts_and_play(registry, response_text)
        tts_time = (time.time() - tts_start) * 1000

        # Phase 7: Log this turn
        total_turn_time = turn_response_time + tts_time
        logger.log_turn(
            question=text,
            answer=response_text,
            response_time_ms=total_turn_time,
            cache_hit=cache_hit,
            llm_tokens=0,  # TODO: Extract from Gemini response if needed
            tts_used=tts_success,
            error=None
        )
```

#### 2.3 정상 종료 시 세션 종료 추가

**기존 (라인 453-457)**:
```python
        # Check for end conversation
        if detect_end_conversation(text):
            print("\n[END] Ending conversation...")
            goodbye_msg = "Goodbye! Say Hey Sena to wake me again."
            print(f"[SENA] {goodbye_msg}")
            tts_and_play(registry, goodbye_msg)
            return True
```

**수정 후**:
```python
        # Check for end conversation
        if detect_end_conversation(text):
            print("\n[END] Ending conversation...")
            goodbye_msg = "Goodbye! Say Hey Sena to wake me again."
            print(f"[SENA] {goodbye_msg}")
            tts_and_play(registry, goodbye_msg)

            # Phase 7: End session logging
            session_duration = time.time() - session_start_time
            print(f"\n📊 Session lasted {session_duration:.1f}s with {turn_count} turns")

            # Ask for rating (optional - can be removed for silent operation)
            # rating = input("Rate this session (1-5): ").strip()
            # logger.end_session(user_rating=int(rating) if rating.isdigit() else None)

            logger.end_session(user_rating=None, notes="Normal conversation end")
            return True
```

#### 2.4 타임아웃 종료 시에도 세션 종료 추가

**기존 (라인 436-439)**:
```python
            if max_silence_checks <= 0:
                print("\n[TIMEOUT] Returning to listen mode due to silence...")
                tts_and_play(registry, "I'm going back to sleep. Say Hey Sena to wake me.")
                return True
```

**수정 후**:
```python
            if max_silence_checks <= 0:
                print("\n[TIMEOUT] Returning to listen mode due to silence...")
                tts_and_play(registry, "I'm going back to sleep. Say Hey Sena to wake me.")

                # Phase 7: End session due to timeout
                logger.end_session(user_rating=None, notes="Session ended due to silence timeout")
                return True
```

---

## 🔧 더 나은 캐시 감지 (선택 사항)

`generate_response_with_context()` 함수를 수정하여 cache_hit 상태를 반환하도록 개선할 수 있습니다:

**수정 전 (라인 294-338)**:
```python
def generate_response_with_context(user_text, history, use_llm=True):
    # ... existing code ...
    return response_text
```

**수정 후**:
```python
def generate_response_with_context(user_text, history, use_llm=True):
    """
    Generate response with conversation context
    v4.1: Added response caching for performance
    Phase 7: Returns tuple (response, cache_hit)

    Returns:
        tuple: (response_text, cache_hit_bool)
    """
    # ... existing code up to cache check ...

    if use_llm:
        # ... context summary code ...

        # Check cache
        cached_response = cache.get_text_response(user_text, context_summary)
        if cached_response:
            print(f"[CACHE HIT] Using cached LLM response")
            return cached_response, True  # MODIFIED: Return tuple

        # Cache miss - generate new response
        llm_response, error = generate_llm_response(user_text, history)

        if llm_response:
            print(f"[LLM] Generated response successfully")
            cache.set_text_response(user_text, llm_response, context_summary)
            return llm_response, False  # MODIFIED: Return tuple

        if error:
            print(f"[LLM WARNING] Failed: {error}, falling back to rule-based")

    # Fallback responses ...
    # All return statements need to return tuple
    if "hello" in user_lower or "hi" in user_lower:
        if len(history) == 0:
            return "Hello! How can I help you today?", False  # MODIFIED
        else:
            return "What else can I help with?", False  # MODIFIED

    # ... rest of the function, add ", False" to all return statements ...

    return f"I heard you say: {user_text}. How can I help you with that?", False  # MODIFIED
```

그리고 conversation_mode_multiturn()에서 사용:

```python
        # Generate response with LLM!
        response_text, cache_hit = generate_response_with_context(text, conversation_history, use_llm=use_llm)
        print(f"\n[SENA] {response_text}")
```

---

## 🚀 빠른 적용 방법

### 방법 1: 수동 편집 (권장)
1. `hey_sena_v4.1_cached.py` 파일을 에디터에서 열기
2. 위의 수정 사항을 하나씩 적용
3. 저장

### 방법 2: 새 파일 생성
1. `hey_sena_v4.1_cached.py`를 복사하여 `hey_sena_v4.1_logged.py` 생성
2. 위의 수정 사항 적용
3. 새 파일로 실행

### 방법 3: Wrapper 스크립트 (임시)
간단한 wrapper를 만들어 기존 코드에 로깅 추가 (다음 섹션 참조)

---

## 📦 Wrapper 스크립트 (임시 솔루션)

새 파일 `run_sena_with_logging.py` 생성:

```python
#!/usr/bin/env python3
"""
Hey Sena v4.1 with Performance Logging Wrapper
Phase 7 임시 로깅 솔루션
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from tools.performance_logger import get_logger
from hey_sena_v4_1_cached import main as original_main
from hey_sena_v4_1_cached import conversation_mode_multiturn as original_conversation

logger = get_logger()

# Monkey patch the conversation function
original_conversation_func = original_conversation

def logged_conversation_mode_multiturn(registry, use_llm=True):
    """Wrapped version with logging"""

    # Start session
    session_id = logger.start_session(metadata={"version": "v4.1", "llm_enabled": use_llm})

    try:
        # Call original
        result = original_conversation_func(registry, use_llm)

        # End session
        logger.end_session(user_rating=None, notes="Wrapper logged session")

        return result

    except Exception as e:
        logger.end_session(user_rating=None, notes=f"Error: {str(e)}")
        raise

# Replace with logged version
import hey_sena_v4_1_cached
hey_sena_v4_1_cached.conversation_mode_multiturn = logged_conversation_mode_multiturn

if __name__ == "__main__":
    original_main()
```

**주의**: Wrapper는 완전한 turn별 로깅을 제공하지 않습니다. 전체 기능을 위해서는 방법 1 또는 2를 사용하세요.

---

## ✅ 검증 방법

수정 후 다음 명령으로 테스트:

```bash
# 구문 오류 체크
python -m py_compile hey_sena_v4.1_cached.py

# 실행 (짧은 테스트)
python hey_sena_v4.1_cached.py
# "Hey Sena" → 질문 1-2개 → "그만"

# 로그 확인
ls -la logs/phase7/sessions/
cat logs/phase7/sessions/session_*.json | head -50

# 분석 실행
python tools/analyze_phase7_data.py

# 대시보드 생성
python tools/generate_dashboard.py
```

---

## 📊 예상 출력

로거가 통합되면 다음과 같은 실시간 피드백이 표시됩니다:

```
📊 [Logger] Session started: a1b2c3d4

[TURN 1] Listening... (5 seconds)
[YOU SAID] "안녕하세요"
[SENA] Hello! How can I help you today?
[TTS] Generating speech...
📊 [Logger] Turn 1: ⚡ LLM | 1523ms

[TURN 2] Listening... (5 seconds)
[YOU SAID] "오늘 날씨 어때?"
[CACHE HIT] Using cached LLM response
[SENA] Let me check the weather for you...
📊 [Logger] Turn 2: 💚 HIT | 8ms

...

[END] Ending conversation...
📊 Session lasted 45.3s with 5 turns

============================================================
📊 SESSION SUMMARY
============================================================
Session ID: a1b2c3d4
Duration: 45.3s
Turns: 5
Cache Hit Rate: 60.0%
Avg Response Time: 623ms
...
============================================================

💾 [Logger] Session saved: logs\phase7\sessions\session_a1b2c3d4_...json
```

---

## 🎯 다음 단계

통합 완료 후:
1. ✅ 첫 10회 세션 수행
2. ✅ 데이터 분석 (`analyze_phase7_data.py`)
3. ✅ 대시보드 확인 (`generate_dashboard.py`)
4. ✅ Phase 7 Day 2 완료!

---

**작성자**: 세나 (Claude Code AI Agent)
**날짜**: 2025-10-28
**Phase**: 7 Day 2 - 로거 통합
