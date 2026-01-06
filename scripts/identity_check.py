#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Identity Integrity Check v2
===========================
SSOT(IDENTITY_ANCHOR)를 위반하는 하드코딩된 명칭 및 레거시 명칭을 탐색합니다.
하드코딩된 문자열 위반과 IDENTITY_ANCHOR 정적 참조를 구분합니다.
"""

import os
import re
import sys
from pathlib import Path
from workspace_root import get_workspace_root

WORKSPACE = get_workspace_root()

if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

# NOTE: IDENTITY_ANCHOR 값 자체는 이 스크립트에서 사용하지 않으므로
# import로 인해 감사 도구가 죽는 상황을 피하기 위해 제거
# (문자열 매칭 시 "IDENTITY_ANCHOR" 키워드만 체크함)

# 검사 제외 대상 (상대 경로 기준: 도구 자신 및 기술적/대용량 데이터)
EXCLUDE_PATHS = {
    "scripts/identity_check.py",
    "outputs/PATCH_NOTES_SYNC.json",
    "outputs/identity_anchor.json",
    "knowledge_base/vector_store.json",
    "fdo_agi_repo/memory/vector_store.json",
}

# 의미 보호 대상 (상대 경로 기준: 발견 시 WARNING으로 리포트)
PROTECTED_PATHS = {
    "scripts/identity_grounding.py",
    "AGENTS.md",
    "ARCHITECTURE_OVERVIEW.md"
}

# Windows/대소문자/슬래시 안정화: 비교용 정규화 세트
EXCLUDE_PATHS_N = {p.lower() for p in EXCLUDE_PATHS}
PROTECTED_PATHS_N = {p.lower() for p in PROTECTED_PATHS}

# 허용되는 RUD/Field 패턴 (Regex)
ALLOWED_RUD_REGEX = r"Rua\s+Field|RUD\s+\(Rua\s+Field\)|RuaField|RUD"

# 금지된 하드코딩 패턴 (정규표현식)
FORBIDDEN_PATTERNS = {
    "Legacy Core/Koa": r"(Koa|Lumen|Lumen_Flow)",
    "Legacy Rua (Identity)": r"\bRua\b(?!\s*Field\b)",
    "Legacy Shion/Binoche": r"(Sian|Binoche_Internal)", # Binoche_Observer is allowed
    "Hardcoded Ruby": r'"Ruby \(루비\)"|\'Ruby \(루비\)\'|"루비 \(Ruby\)"|\'루비 \(Ruby\)\'',
}

def check_identity_integrity(fail_on_warnings=False):
    print(f"🔍 Checking Identity Integrity in {WORKSPACE}...")
    violations = []
    warnings = []

    EXCLUDE_DIRS = {
        ".git", "node_modules", ".venv", ".venv_local", "venv", "env",
        "__pycache__", "backups", "session_memory", "tests",
        "ai_binoche_conversation_origin", "LLM_Unified", "dist", "build"
    }

    for root, dirs, files in os.walk(WORKSPACE):
        # prune: 아예 하위 탐색을 막아 속도/오탐 개선
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            
        for file in files:
            path = Path(root) / file
            rel_path = path.relative_to(WORKSPACE).as_posix()
            rel_norm = rel_path.lower()
            
            # EXCLUDE_PATHS (상대경로) 또는 특정 파일명은 완전히 스킵
            if rel_norm in EXCLUDE_PATHS_N or file in {"PATCH_NOTES_SYNC.json", "identity_anchor.json"} or not file.endswith((".py", ".ps1", ".md", ".json")):
                continue
            
            is_protected = rel_norm in PROTECTED_PATHS_N
            
            try:
                # Handle encoding gracefully
                content = None
                for enc in ["utf-8", "cp949", "utf-16"]:
                    try:
                        content = path.read_text(encoding=enc)
                        break
                    except:
                        continue
                
                if content is None:
                    continue
                
                for name, pattern in FORBIDDEN_PATTERNS.items():
                    # master_ai_router.py는 폴백을 위해 레거시 키워드를 포함해야 하므로 일부 예외 처리
                    if file == "master_ai_router.py" and "Legacy" in name:
                        continue
                        
                    matches = list(re.finditer(pattern, content, re.IGNORECASE if "Legacy" in name else 0))
                    for match in matches:
                        # 1. RUD/Field 계열 정밀 예외 처리
                        if name == "Legacy Rua (Identity)":
                            # 매칭된 지점부터 80자 내에 ALLOWED 패턴이 있는지 확인 (Rua Field 변종 대응)
                            window = content[match.start() : match.start() + 80]
                            if re.search(ALLOWED_RUD_REGEX, window, re.IGNORECASE):
                                continue
                        
                        # 2. IDENTITY_ANCHOR 참조 여부 확인 (휴리스틱)
                        # 문자열 'IDENTITY_ANCHOR[' 또는 "IDENTITY_ANCHOR[" 가 근처(앞 40자)에 있으면 참조로 간주
                        context_prev = content[max(0, match.start()-40) : match.start()]
                        if "IDENTITY_ANCHOR" in context_prev:
                            continue
                            
                        line_count = content[:match.start()].count('\n') + 1
                        entry = {
                            "file": rel_path,
                            "type": name,
                            "line": line_count,
                            "match": match.group()
                        }
                        
                        if is_protected:
                            warnings.append(entry)
                        else:
                            violations.append(entry)
            except Exception:
                continue

    if warnings:
        print(f"⚠️  Found {len(warnings)} protected context warnings (Manual verification recommended):")
        for w in warnings:
            print(f"  [PROTECTED/WARNING] {w['file']}:L{w['line']} -> '{w['match']}'")
        print()

    if violations:
        print(f"❌ Found {len(violations)} identity violations:")
        for v in violations:
            print(f"  [{v['type']}] {v['file']}:L{v['line']} -> '{v['match']}'")
        return 1 # Error
    
    if warnings and fail_on_warnings:
        print("❌ FAILED: Warnings detected and --fail-on-warnings is set.")
        return 2 # Warning Error
        
    print("✅ Identity integrity is clean (SSOT enforced).")
    return 0 # Success

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Identity Integrity Check")
    parser.add_argument("--fail-on-warnings", action="store_true", help="Fail if warnings are found")
    args = parser.parse_args()
    
    exit_code = check_identity_integrity(fail_on_warnings=args.fail_on_warnings)
    sys.exit(exit_code)
