#!/usr/bin/env python3
"""
.env 파일 생성 헬퍼 스크립트

.env.example을 기반으로 대화형으로 .env 파일을 생성합니다.

사용법:
    python scripts/setup_env.py
    python scripts/setup_env.py --force  # 기존 .env 덮어쓰기
"""

import os
import sys
from pathlib import Path
from typing import Dict, Optional

# ANSI 색상
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"


def read_env_example() -> Dict[str, str]:
    """
    .env.example 파일을 읽어서 변수명과 기본값 추출
    
    Returns:
        변수명: 기본값 딕셔너리
    """
    example_file = Path(".env.example")
    if not example_file.exists():
        print(f"{RED}✗{RESET} .env.example file not found!")
        return {}

    env_vars = {}
    current_section = None

    with open(example_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            # 섹션 헤더
            if line.startswith("# ==="):
                current_section = line
                continue

            # 주석이나 빈 줄은 그대로 유지
            if line.startswith("#") or not line:
                continue

            # 변수 파싱
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                env_vars[key] = {
                    "default": value,
                    "section": current_section,
                    "current": os.getenv(key),  # 현재 환경변수 값
                }

    return env_vars


def prompt_for_value(key: str, config: Dict[str, str], skip_if_set: bool = True) -> Optional[str]:
    """
    사용자에게 환경변수 값 입력 받기
    
    Args:
        key: 환경변수 이름
        config: 변수 설정 정보 (default, current 등)
        skip_if_set: 이미 환경변수가 설정되어 있으면 건너뛰기
        
    Returns:
        입력된 값 또는 None (건너뛰기)
    """
    default_val = config["default"]
    current_val = config["current"]

    # 현재 환경변수가 있고 skip_if_set이면 그대로 사용
    if skip_if_set and current_val:
        print(f"{GREEN}✓{RESET} {key}: Using current value ({current_val[:20]}...)")
        return current_val

    # 프롬프트 구성
    prompt_parts = [f"\n{BOLD}{key}{RESET}"]
    if default_val:
        prompt_parts.append(f" (default: {default_val})")
    if current_val:
        prompt_parts.append(f" [current: {current_val[:20]}...]")

    print("".join(prompt_parts))

    # 특정 키에 대한 힌트
    hints = {
        "GCP_PROJECT": "Google Cloud Project ID (e.g., my-project-123)",
        "GCP_LOCATION": "GCP region (e.g., us-central1, asia-northeast3)",
        "GOOGLE_API_KEY": "Google AI Studio or Vertex AI API key",
        "REDIS_HOST": "Redis server hostname or IP",
        "REDIS_PASSWORD": "Redis password (leave empty if no auth)",
        "EVIDENCE_GATE_FORCE": "Enable forced evidence gathering (true/false)",
    }

    if key in hints:
        print(f"  {BLUE}ℹ{RESET}  {hints[key]}")

    user_input = input(f"  Enter value (or press Enter to use default): ").strip()

    # 입력이 없으면 기본값 사용
    if not user_input:
        if default_val:
            print(f"  → Using default: {default_val}")
            return default_val
        elif current_val:
            print(f"  → Using current: {current_val}")
            return current_val
        else:
            print(f"  → Skipping (no value)")
            return ""

    return user_input


def write_env_file(env_vars: Dict[str, Dict], output_file: Path):
    """
    .env 파일 작성
    
    Args:
        env_vars: 환경변수 딕셔너리
        output_file: 출력 파일 경로
    """
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# Auto-generated .env file\n")
        f.write(f"# Created by setup_env.py\n")
        f.write("# DO NOT COMMIT THIS FILE TO VERSION CONTROL\n\n")

        current_section = None
        for key, config in env_vars.items():
            # 섹션이 바뀌면 헤더 출력
            section = config.get("section")
            if section and section != current_section:
                f.write(f"\n{section}\n")
                current_section = section

            value = config.get("final", config.get("default", ""))
            f.write(f"{key}={value}\n")


def main():
    """메인 함수"""
    force = "--force" in sys.argv

    print(f"{BOLD}{BLUE}🔧 Environment Setup Helper{RESET}")
    print(f"{BLUE}Interactive .env file configuration{RESET}\n")

    # .env 파일 존재 확인
    env_file = Path(".env")
    if env_file.exists() and not force:
        print(f"{YELLOW}⚠{RESET} .env file already exists!")
        overwrite = input("Overwrite? (y/N): ").strip().lower()
        if overwrite != "y":
            print("Aborted.")
            sys.exit(0)

    # .env.example 읽기
    print(f"\n{BLUE}📖 Reading .env.example...{RESET}")
    env_vars = read_env_example()

    if not env_vars:
        print(f"{RED}✗{RESET} Failed to read .env.example")
        sys.exit(1)

    print(f"{GREEN}✓{RESET} Found {len(env_vars)} configuration variables\n")

    # 대화형 모드 vs 빠른 모드
    mode = input(
        f"{BOLD}Configuration mode:{RESET}\n"
        f"  1. Interactive (prompt for each variable)\n"
        f"  2. Quick (use defaults and current env)\n"
        f"Select (1/2, default=2): "
    ).strip()

    interactive = mode == "1"

    print(f"\n{BLUE}🔧 Configuring environment...{RESET}")

    # 각 변수에 대해 값 설정
    for key, config in env_vars.items():
        if interactive:
            value = prompt_for_value(key, config, skip_if_set=False)
        else:
            # 빠른 모드: 현재 환경변수 > 기본값
            value = config["current"] or config["default"]
            if value:
                print(f"{GREEN}✓{RESET} {key}={value}")

        config["final"] = value

    # 파일 작성
    print(f"\n{BLUE}💾 Writing .env file...{RESET}")
    write_env_file(env_vars, env_file)
    print(f"{GREEN}✓{RESET} .env file created successfully!")

    # 검증 스크립트 실행 제안
    print(f"\n{BLUE}💡 Next steps:{RESET}")
    print(f"  1. Review and edit {BOLD}.env{RESET} if needed")
    print(f"  2. Run {BOLD}python scripts/check_env_config.py{RESET} to validate")
    print(f"  3. Restart your application to load new configuration")

    print(f"\n{YELLOW}⚠️  Remember:{RESET}")
    print(f"  • Do NOT commit .env to version control")
    print(f"  • Keep your API keys and credentials secure")
    print(f"  • Use .env.example as a template for team members")


if __name__ == "__main__":
    main()
