#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modified conversation_mode_multiturn() with Performance Logging

이 파일을 hey_sena_v4.1_cached.py의 conversation_mode_multiturn() 함수로 교체하세요.
또는 import해서 사용하세요.

Phase 7 - Day 2
"""

import time
from tools.performance_logger import get_logger

logger = get_logger()


def conversation_mode_multiturn_logged(registry, use_llm=True,
                                       detect_end_conversation=None,
                                       record_audio=None,
                                       transcribe_audio=None,
                                       generate_response_with_context=None,
                                       tts_and_play=None):
    """
    Multi-turn conversation mode with LLM support and Performance Logging

    Phase 7: Added comprehensive performance logging

    Args:
        registry: Tool registry
        use_llm: Enable LLM for responses (default: True)
        detect_end_conversation: Function to detect end commands
        record_audio: Function to record audio
        transcribe_audio: Function to transcribe
        generate_response_with_context: Function to generate response
        tts_and_play: Function for TTS
    """
    llm_status = "ENABLED" if use_llm else "DISABLED"
    print("\n" + "=" * 60)
    print(f"[CONVERSATION MODE] Multi-turn with LLM {llm_status}")
    print("=" * 60)
    print("\nYou can:")
    print("  - Ask ANY question (LLM will answer!)")
    print("  - Continue asking without saying 'Hey Sena' again")
    print("  - Say 'goodbye' or '그만' to end conversation")
    print("  - Wait 10+ seconds (silence) to auto-return to listen mode")
    print()

    conversation_history = []
    turn_count = 0
    max_silence_checks = 2

    # Phase 7: Start performance logging session
    session_id = logger.start_session(metadata={
        "version": "v4.1",
        "llm_enabled": use_llm
    })
    session_start_time = time.time()
    print(f"📊 [Logger] Session started: {session_id}\n")

    try:
        while True:
            turn_count += 1
            print(f"\n[TURN {turn_count}] Listening... (5 seconds)")

            # Phase 7: Start turn timer
            turn_start_time = time.time()

            # Record user input
            audio_file = record_audio(duration=5)

            if not audio_file:
                print("[ERROR] Could not record. Trying again...")
                continue

            # Transcribe
            print("[PROCESSING] Transcribing...")
            text = transcribe_audio(audio_file, registry)

            # Cleanup
            try:
                import os
                os.remove(audio_file)
            except:
                pass

            # Check for silence
            if not text or len(text) < 3:
                print(f"[SILENCE] No clear input detected.")
                max_silence_checks -= 1

                if max_silence_checks <= 0:
                    print("\n[TIMEOUT] Returning to listen mode due to silence...")
                    tts_and_play(registry, "I'm going back to sleep. Say Hey Sena to wake me.")

                    # Phase 7: End session due to timeout
                    session_duration = time.time() - session_start_time
                    print(f"\n📊 Session lasted {session_duration:.1f}s with {turn_count-1} turns")
                    logger.end_session(user_rating=None, notes="Session ended due to silence timeout")
                    return True
                else:
                    print(f"[INFO] {max_silence_checks} more silence(s) before timeout.")
                    tts_and_play(registry, "I'm still here. What would you like?")
                    continue

            # Reset silence counter
            max_silence_checks = 2

            # Show what was heard
            print(f"\n[YOU SAID] \"{text}\"")

            # Check for end conversation
            if detect_end_conversation(text):
                print("\n[END] Ending conversation...")
                goodbye_msg = "Goodbye! Say Hey Sena to wake me again."
                print(f"[SENA] {goodbye_msg}")
                tts_and_play(registry, goodbye_msg)

                # Phase 7: End session logging
                session_duration = time.time() - session_start_time
                print(f"\n📊 Session lasted {session_duration:.1f}s with {turn_count} turns")

                # Optional: Ask for rating (commented out for silent operation)
                # rating_input = input("Rate this session (1-5, or Enter to skip): ").strip()
                # rating = int(rating_input) if rating_input.isdigit() and 1 <= int(rating_input) <= 5 else None

                logger.end_session(user_rating=None, notes="Normal conversation end")
                return True

            # Generate response with LLM!
            response_generation_start = time.time()

            # Try to get response with cache hit detection
            try:
                # If generate_response_with_context returns tuple (response, cache_hit)
                result = generate_response_with_context(text, conversation_history, use_llm=use_llm)
                if isinstance(result, tuple):
                    response_text, cache_hit = result
                else:
                    # Fallback: old version returns just string
                    response_text = result
                    # Detect cache hit from console output (simple heuristic)
                    cache_hit = False  # Will be updated later
            except TypeError:
                # Old version
                response_text = generate_response_with_context(text, conversation_history, use_llm=use_llm)
                cache_hit = False

            print(f"\n[SENA] {response_text}")

            # Phase 7: Measure response generation time
            response_gen_time = (time.time() - response_generation_start) * 1000  # ms

            # Save to history
            conversation_history.append({
                "turn": turn_count,
                "user": text,
                "assistant": response_text
            })

            # Phase 7: Detect topic (simple keyword extraction)
            topic = None
            keywords = ["weather", "날씨", "time", "시간", "date", "날짜",
                       "python", "파이썬", "programming", "프로그래밍"]
            for kw in keywords:
                if kw in text.lower():
                    topic = kw
                    logger.add_topic(topic)
                    break

            # TTS and play
            print("[TTS] Generating speech...")
            tts_start = time.time()
            tts_success = tts_and_play(registry, response_text)
            tts_time = (time.time() - tts_start) * 1000  # ms

            # Phase 7: Calculate total turn time
            total_turn_time = (time.time() - turn_start_time) * 1000  # ms

            # Phase 7: Log this turn
            logger.log_turn(
                question=text,
                answer=response_text[:200],  # Truncate for storage
                response_time_ms=total_turn_time,
                cache_hit=cache_hit,
                llm_tokens=0,  # TODO: Extract from Gemini API if needed
                tts_used=tts_success,
                error=None
            )

            # Continue conversation
            print("\n[READY] What else would you like to know?")
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Session interrupted by user")
        session_duration = time.time() - session_start_time
        print(f"\n📊 Session lasted {session_duration:.1f}s with {turn_count} turns")
        logger.end_session(user_rating=None, notes="Session interrupted (Ctrl+C)")
        raise

    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {str(e)}")
        logger.end_session(user_rating=None, notes=f"Session ended with error: {str(e)}")
        raise


# Usage example (for testing):
if __name__ == "__main__":
    print("""
    이 파일은 수정된 conversation_mode_multiturn() 함수를 포함합니다.

    사용 방법:

    1. hey_sena_v4.1_cached.py를 열기
    2. conversation_mode_multiturn() 함수를 찾기 (라인 387-476)
    3. 전체 함수를 이 파일의 conversation_mode_multiturn_logged()로 교체
    4. 함수 이름을 conversation_mode_multiturn()로 변경
    5. 파라미터에서 함수들을 제거 (이미 import됨)

    또는:

    이 파일을 import해서 사용:
    ```python
    from conversation_mode_logged import conversation_mode_multiturn_logged

    # main()에서:
    conversation_mode_multiturn_logged(
        registry,
        use_llm=use_llm,
        detect_end_conversation=detect_end_conversation,
        record_audio=record_audio,
        transcribe_audio=transcribe_audio,
        generate_response_with_context=generate_response_with_context,
        tts_and_play=tts_and_play
    )
    ```
    """)
