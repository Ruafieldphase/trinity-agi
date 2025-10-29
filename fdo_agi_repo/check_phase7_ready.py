#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 7 준비 상태 체크 스크립트

Hey Sena v4.1 첫 세션 실행 전 환경을 검증합니다.
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

def check_files():
    """필수 파일 확인"""
    print("=" * 60)
    print("1. 필수 파일 체크")
    print("=" * 60)

    required_files = [
        "hey_sena_v4.1_logged.py",
        "tools/performance_logger.py",
        "tools/analyze_phase7_data.py",
        "tools/generate_dashboard.py",
    ]

    all_exist = True
    for file in required_files:
        path = Path(file)
        if path.exists():
            size = path.stat().st_size / 1024  # KB
            print(f"  ✅ {file} ({size:.1f} KB)")
        else:
            print(f"  ❌ {file} (NOT FOUND)")
            all_exist = False

    return all_exist


def check_directories():
    """로그 디렉토리 확인"""
    print("\n" + "=" * 60)
    print("2. 로그 디렉토리 체크")
    print("=" * 60)

    required_dirs = [
        "logs/phase7",
        "logs/phase7/sessions",
        "logs/phase7/daily_stats",
        "logs/phase7/analysis",
    ]

    all_exist = True
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists() and path.is_dir():
            print(f"  ✅ {dir_path}/")
        else:
            print(f"  ❌ {dir_path}/ (NOT FOUND)")
            all_exist = False

    return all_exist


def check_write_permissions():
    """쓰기 권한 확인"""
    print("\n" + "=" * 60)
    print("3. 쓰기 권한 체크")
    print("=" * 60)

    test_file = Path("logs/phase7/sessions/.test_write")

    try:
        test_file.touch()
        test_file.unlink()
        print("  ✅ logs/phase7/sessions/ (WRITABLE)")
        return True
    except Exception as e:
        print(f"  ❌ logs/phase7/sessions/ (NOT WRITABLE)")
        print(f"     Error: {str(e)}")
        return False


def check_dependencies():
    """Python 패키지 확인"""
    print("\n" + "=" * 60)
    print("4. Python 패키지 체크")
    print("=" * 60)

    packages = {
        "speech_recognition": "음성 인식",
        "sounddevice": "오디오 입력",
        "soundfile": "오디오 파일 처리",
        "pyttsx3": "TTS (Text-to-Speech)",
        "google.generativeai": "Gemini LLM",
    }

    all_installed = True
    for package, description in packages.items():
        try:
            __import__(package)
            print(f"  ✅ {package} ({description})")
        except ImportError:
            print(f"  ⚠️  {package} ({description}) - NOT INSTALLED")
            all_installed = False

    if not all_installed:
        print("\n  📝 설치 명령어:")
        print("     pip install SpeechRecognition sounddevice soundfile pyttsx3 google-generativeai")

    return all_installed


def check_logger_import():
    """로거 모듈 임포트 확인"""
    print("\n" + "=" * 60)
    print("5. 로거 모듈 임포트 체크")
    print("=" * 60)

    try:
        sys.path.insert(0, '.')
        from tools.performance_logger import get_logger
        logger = get_logger()
        print("  ✅ performance_logger 임포트 성공")
        print(f"     Logger instance: {type(logger).__name__}")
        return True
    except Exception as e:
        print(f"  ❌ performance_logger 임포트 실패")
        print(f"     Error: {str(e)}")
        return False


def check_existing_sessions():
    """기존 세션 로그 확인"""
    print("\n" + "=" * 60)
    print("6. 기존 세션 로그 체크")
    print("=" * 60)

    sessions_dir = Path("logs/phase7/sessions")

    if not sessions_dir.exists():
        print("  ⚠️  세션 디렉토리 없음")
        return 0

    session_files = list(sessions_dir.glob("session_*.json"))

    if not session_files:
        print("  📝 기존 세션 없음 (첫 세션 준비)")
        return 0
    else:
        print(f"  📊 기존 세션: {len(session_files)}개")
        for file in session_files[:5]:  # 최대 5개만 표시
            size = file.stat().st_size
            print(f"     - {file.name} ({size} bytes)")
        if len(session_files) > 5:
            print(f"     ... and {len(session_files) - 5} more")
        return len(session_files)


def check_syntax():
    """구문 검증"""
    print("\n" + "=" * 60)
    print("7. 구문 검증")
    print("=" * 60)

    try:
        import py_compile
        py_compile.compile("hey_sena_v4.1_logged.py", doraise=True)
        print("  ✅ hey_sena_v4.1_logged.py 구문 검사 통과")
        return True
    except py_compile.PyCompileError as e:
        print(f"  ❌ 구문 오류 발견")
        print(f"     {str(e)}")
        return False


def main():
    """메인 실행"""
    print("\n" + "=" * 60)
    print("Phase 7 준비 상태 체크")
    print("=" * 60)
    print()

    # 모든 체크 실행
    checks = {
        "파일": check_files(),
        "디렉토리": check_directories(),
        "쓰기 권한": check_write_permissions(),
        "Python 패키지": check_dependencies(),
        "로거 임포트": check_logger_import(),
        "구문 검증": check_syntax(),
    }

    session_count = check_existing_sessions()

    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 체크 결과 요약")
    print("=" * 60)

    for check_name, result in checks.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}  {check_name}")

    print(f"\n  📝 기존 세션: {session_count}개")

    # 전체 결과
    all_passed = all(checks.values())

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 모든 체크 통과!")
        print("=" * 60)
        print()
        print("🚀 실행 준비 완료!")
        print()
        print("다음 명령어로 Hey Sena를 시작하세요:")
        print("  python hey_sena_v4.1_logged.py")
        print()
        print("실행 가이드:")
        print("  PHASE7_첫세션_실행가이드.md 참고")
        print()
        return 0
    else:
        print("⚠️  일부 체크 실패")
        print("=" * 60)
        print()
        print("위의 오류를 해결한 후 다시 실행하세요.")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
