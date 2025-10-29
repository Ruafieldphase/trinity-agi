#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hey Sena - System Health Check
Validates system readiness for deployment
"""
import os
import sys
from pathlib import Path

def check_python_version():
    """Check Python version"""
    print("\n[1/8] Checking Python version...")
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"

    if version.major >= 3 and version.minor >= 8:
        print(f"  [OK] Python {version_str}")
        return True
    else:
        print(f"  [FAIL] Python {version_str} (requires 3.8+)")
        return False

def check_dependencies():
    """Check required Python packages"""
    print("\n[2/8] Checking dependencies...")

    required = {
        "sounddevice": "sounddevice",
        "numpy": "numpy",
        "scipy": "scipy",
        "google-generativeai": "google.generativeai",
        "python-dotenv": "dotenv",
        "Pillow": "PIL",
    }

    missing = []
    for package_name, import_name in required.items():
        try:
            __import__(import_name)
            print(f"  [OK] {package_name}")
        except ImportError:
            print(f"  [FAIL] {package_name} - NOT INSTALLED")
            missing.append(package_name)

    if missing:
        print(f"\n  Install missing packages:")
        print(f"  pip install {' '.join(missing)}")
        return False

    return True

def check_env_file():
    """Check .env file and API key"""
    print("\n[3/8] Checking .env configuration...")

    env_path = Path(__file__).parent / ".env"

    if not env_path.exists():
        print(f"  [FAIL] .env file not found")
        print(f"  Create: {env_path}")
        return False

    print(f"  [OK] .env file exists")

    # Check API key
    from dotenv import load_dotenv
    load_dotenv()

    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key and len(api_key) > 20:
        print(f"  [OK] GEMINI_API_KEY is set ({len(api_key)} chars)")
        return True
    else:
        print(f"  [FAIL] GEMINI_API_KEY not set or too short")
        return False

def check_core_files():
    """Check core program files exist"""
    print("\n[4/8] Checking core files...")

    project_dir = Path(__file__).parent

    core_files = [
        "hey_sena_v4_llm.py",
        "hey_sena_v3_multiturn.py",
        "hey_sena_v2.py",
        "start_sena_v4.bat",
        "toggle_sena_v4.bat",
        "stop_sena.bat",
        "create_shortcuts_v4.py",
    ]

    all_exist = True
    for filename in core_files:
        filepath = project_dir / filename
        if filepath.exists():
            print(f"  [OK] {filename}")
        else:
            print(f"  [FAIL] {filename} - NOT FOUND")
            all_exist = False

    return all_exist

def check_test_files():
    """Check test files exist"""
    print("\n[5/8] Checking test files...")

    project_dir = Path(__file__).parent

    test_files = [
        "test_multiturn.py",
        "test_conversation_flow.py",
        "test_llm_integration.py",
    ]

    all_exist = True
    for filename in test_files:
        filepath = project_dir / filename
        if filepath.exists():
            print(f"  [OK] {filename}")
        else:
            print(f"  [FAIL] {filename} - NOT FOUND")
            all_exist = False

    return all_exist

def check_documentation():
    """Check documentation files exist"""
    print("\n[6/8] Checking documentation...")

    project_dir = Path(__file__).parent

    doc_files = [
        "HEY_SENA_README.md",
        "QUICKSTART.md",
        "HEY_SENA_완전가이드.md",
        "Hey_Sena_v3_Multi-turn_완료보고서.md",
        "Hey_Sena_v4_LLM_완료보고서.md",
    ]

    all_exist = True
    for filename in doc_files:
        filepath = project_dir / filename
        if filepath.exists():
            print(f"  [OK] {filename}")
        else:
            print(f"  [FAIL] {filename} - NOT FOUND")
            all_exist = False

    return all_exist

def check_desktop_shortcuts():
    """Check if desktop shortcuts were created"""
    print("\n[7/8] Checking desktop shortcuts...")

    try:
        import winshell
        desktop = winshell.desktop()

        shortcuts = [
            "Hey Sena v4 (LLM).lnk",
            "Toggle Hey Sena v4.lnk",
            "Stop Hey Sena.lnk",
        ]

        all_exist = True
        for shortcut_name in shortcuts:
            shortcut_path = Path(desktop) / shortcut_name
            if shortcut_path.exists():
                print(f"  [OK] {shortcut_name}")
            else:
                print(f"  [WARNING] {shortcut_name} - NOT FOUND")
                all_exist = False

        if not all_exist:
            print(f"  Run: python create_shortcuts_v4.py")

        return all_exist

    except ImportError:
        print(f"  [SKIP] winshell not available (Windows only)")
        return True

def check_basic_functionality():
    """Test basic functionality without hitting API"""
    print("\n[8/8] Testing basic functionality...")

    try:
        # Import v4 functions
        sys.path.insert(0, str(Path(__file__).parent))
        from hey_sena_v4_llm import (
            detect_end_conversation,
            generate_response_with_context,
        )

        # Test end conversation detection
        if detect_end_conversation("goodbye"):
            print(f"  [OK] End conversation detection works")
        else:
            print(f"  [FAIL] End conversation detection failed")
            return False

        # Test rule-based response (no API call)
        response = generate_response_with_context("hello", [], use_llm=False)
        if response and len(response) > 0:
            print(f"  [OK] Rule-based responses work")
        else:
            print(f"  [FAIL] Rule-based responses failed")
            return False

        print(f"  [OK] Basic functionality verified")
        return True

    except Exception as e:
        print(f"  [FAIL] Functionality test error: {e}")
        return False

def generate_health_report(results):
    """Generate final health report"""
    print("\n" + "=" * 60)
    print("SYSTEM HEALTH REPORT")
    print("=" * 60)

    checks = [
        ("Python Version", results[0]),
        ("Dependencies", results[1]),
        ("Environment Config", results[2]),
        ("Core Files", results[3]),
        ("Test Files", results[4]),
        ("Documentation", results[5]),
        ("Desktop Shortcuts", results[6]),
        ("Basic Functionality", results[7]),
    ]

    passed = sum(results)
    total = len(results)

    for check_name, status in checks:
        status_str = "[OK]" if status else "[FAIL]"
        print(f"{status_str:8} {check_name}")

    print(f"\nTotal: {passed}/{total} checks passed")

    if passed == total:
        print("\n" + "=" * 60)
        print("STATUS: PRODUCTION READY")
        print("=" * 60)
        print("\nYour Hey Sena system is fully configured and ready to use!")
        print("\nQuick Start:")
        print("  1. Double-click 'Hey Sena v4 (LLM)' on desktop")
        print("  2. Say 'Hey Sena' or '세나야' to activate")
        print("  3. Ask any question!")
        print("\nDocumentation:")
        print("  - QUICKSTART.md - 5-minute setup guide")
        print("  - HEY_SENA_README.md - Complete user guide")
        return 0
    else:
        print("\n" + "=" * 60)
        print("STATUS: NEEDS ATTENTION")
        print("=" * 60)
        print("\nPlease fix the issues above before deployment.")
        print("\nCommon fixes:")
        print("  - Missing packages: pip install -r requirements.txt")
        print("  - Missing .env: Create .env with GEMINI_API_KEY")
        print("  - Missing shortcuts: python create_shortcuts_v4.py")
        return 1

def main():
    """Run all health checks"""
    print("=" * 60)
    print("Hey Sena v4 - System Health Check")
    print("=" * 60)
    print("\nValidating system readiness...")

    results = [
        check_python_version(),
        check_dependencies(),
        check_env_file(),
        check_core_files(),
        check_test_files(),
        check_documentation(),
        check_desktop_shortcuts(),
        check_basic_functionality(),
    ]

    return generate_health_report(results)

if __name__ == "__main__":
    sys.exit(main())
