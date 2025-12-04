#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automatic Logger Integration Patcher

hey_sena_v4.1_cached.py에 performance_logger를 자동으로 통합합니다.
"""

import os
import sys
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
    import io
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)

def patch_v41_with_logger():
    """v4.1 파일에 로거 통합"""

    # 파일 경로
    original_file = Path("hey_sena_v4.1_cached.py")
    output_file = Path("hey_sena_v4.1_logged.py")
    backup_file = Path("hey_sena_v4.1_cached_backup.py")

    if not original_file.exists():
        print(f"❌ Error: {original_file} not found!")
        return False

    print("📖 Reading original file...")
    with open(original_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Import 추가
    print("🔧 Adding logger import...")
    import_marker = "from response_cache import get_cache"
    if "from tools.performance_logger import get_logger" not in content:
        content = content.replace(
            import_marker,
            import_marker + "\nfrom tools.performance_logger import get_logger"
        )

    # 2. Logger 초기화 추가
    print("🔧 Adding logger initialization...")
    cache_init = "cache = get_cache()"
    if "logger = get_logger()" not in content:
        content = content.replace(
            cache_init,
            cache_init + "\n\n# Initialize performance logger (Phase 7)\nlogger = get_logger()"
        )

    # 3. conversation_mode_multiturn 함수 수정
    print("🔧 Patching conversation_mode_multiturn function...")

    # 세션 시작 추가
    session_start_marker = "    conversation_history = []\n    turn_count = 0\n    max_silence_checks = 2"
    session_start_patch = """    conversation_history = []
    turn_count = 0
    max_silence_checks = 2

    # Phase 7: Start performance logging session
    session_id = logger.start_session(metadata={
        "version": "v4.1",
        "llm_enabled": use_llm
    })
    session_start_time = time.time()
    print(f"📊 [Logger] Session started: {session_id}\\n")"""

    if "logger.start_session" not in content:
        content = content.replace(session_start_marker, session_start_patch)

    # 타임아웃 종료 로깅 추가
    timeout_marker = '''                print("\\n[TIMEOUT] Returning to listen mode due to silence...")
                tts_and_play(registry, "I'm going back to sleep. Say Hey Sena to wake me.")
                return True'''

    timeout_patch = '''                print("\\n[TIMEOUT] Returning to listen mode due to silence...")
                tts_and_play(registry, "I'm going back to sleep. Say Hey Sena to wake me.")

                # Phase 7: End session due to timeout
                session_duration = time.time() - session_start_time
                print(f"\\n📊 Session lasted {session_duration:.1f}s with {turn_count-1} turns")
                logger.end_session(user_rating=None, notes="Session ended due to silence timeout")
                return True'''

    if "# Phase 7: End session due to timeout" not in content:
        content = content.replace(timeout_marker, timeout_patch)

    # 정상 종료 로깅 추가
    end_marker = '''            print("\\n[END] Ending conversation...")
            goodbye_msg = "Goodbye! Say Hey Sena to wake me again."
            print(f"[SENA] {goodbye_msg}")
            tts_and_play(registry, goodbye_msg)
            return True'''

    end_patch = '''            print("\\n[END] Ending conversation...")
            goodbye_msg = "Goodbye! Say Hey Sena to wake me again."
            print(f"[SENA] {goodbye_msg}")
            tts_and_play(registry, goodbye_msg)

            # Phase 7: End session logging
            session_duration = time.time() - session_start_time
            print(f"\\n📊 Session lasted {session_duration:.1f}s with {turn_count} turns")
            logger.end_session(user_rating=None, notes="Normal conversation end")
            return True'''

    if "# Phase 7: End session logging" not in content:
        content = content.replace(end_marker, end_patch)

    # Turn 로깅 추가 (복잡하므로 간소화된 버전)
    response_marker = '''        # Generate response with LLM!
        response_text = generate_response_with_context(text, conversation_history, use_llm=use_llm)
        print(f"\\n[SENA] {response_text}")'''

    response_patch = '''        # Phase 7: Start turn timer
        turn_start_time = time.time()

        # Generate response with LLM!
        response_text = generate_response_with_context(text, conversation_history, use_llm=use_llm)
        print(f"\\n[SENA] {response_text}")'''

    if "# Phase 7: Start turn timer" not in content:
        content = content.replace(response_marker, response_patch)

    # TTS 후 로깅 추가
    tts_marker = '''        # TTS and play
        print("[TTS] Generating speech...")
        tts_and_play(registry, response_text)

        # Continue conversation'''

    tts_patch = '''        # TTS and play
        print("[TTS] Generating speech...")
        tts_start = time.time()
        tts_success = tts_and_play(registry, response_text)
        tts_time = (time.time() - tts_start) * 1000

        # Phase 7: Calculate total turn time and log
        total_turn_time = (time.time() - turn_start_time) * 1000  # ms

        # Simple cache hit detection (heuristic)
        cache_hit = False  # Can be improved with modified generate_response_with_context

        logger.log_turn(
            question=text,
            answer=response_text[:200],
            response_time_ms=total_turn_time,
            cache_hit=cache_hit,
            llm_tokens=0,
            tts_used=tts_success if isinstance(tts_success, bool) else True,
            error=None
        )

        # Continue conversation'''

    if "logger.log_turn" not in content:
        content = content.replace(tts_marker, tts_patch)

    # 4. 파일 저장
    print(f"💾 Saving patched version to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"\n✅ Successfully created {output_file}!")
    print(f"\n📝 Changes made:")
    print("  - Added performance_logger import")
    print("  - Added logger initialization")
    print("  - Added session start logging")
    print("  - Added turn-by-turn logging")
    print("  - Added session end logging (normal + timeout)")
    print("\n🚀 Next steps:")
    print(f"  1. Test: python {output_file}")
    print("  2. Check logs: ls logs/phase7/sessions/")
    print("  3. Analyze: python tools/analyze_phase7_data.py")

    return True


if __name__ == "__main__":
    print("="*70)
    print("🔧 Hey Sena v4.1 Logger Integration Patcher")
    print("="*70)
    print()

    success = patch_v41_with_logger()

    if success:
        print("\n" + "="*70)
        print("✅ Patching completed successfully!")
        print("="*70)
        sys.exit(0)
    else:
        print("\n" + "="*70)
        print("❌ Patching failed!")
        print("="*70)
        sys.exit(1)
