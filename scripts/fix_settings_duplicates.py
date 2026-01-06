#!/usr/bin/env python3
"""
settings.json의 중복 키를 안전하게 제거하는 스크립트 (v2)
정규식 기반 전체 텍스트 매칭으로 중복 제거
"""
import os
import json
import re
from pathlib import Path
from datetime import datetime

def remove_check_monitoring_duplicates(settings_path):
    """check_monitoring_status.ps1 중복 항목만 제거"""
    print(f"📁 파일 로드: {settings_path}")
    
    with open(settings_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_length = len(content)
    print(f"📊 원본 크기: {original_length:,} 문자")
    
    # 백업
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{settings_path}.before_safe_fix_{timestamp}"
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"💾 백업: {backup_path}")
    
    # 제거할 패턴들 (첫 번째는 유지)
    patterns_to_remove = [
        # 패턴 1: 따옴표 없는 버전 (라인 3012)
        r',\s*\n\s*"powershell -NoProfile -ExecutionPolicy Bypass -File d:\\\\nas_backup\\\\LLM_Unified\\\\ion-mentoring\\\\scripts\\\\check_monitoring_status\.ps1":\s*\{\s*\n\s*"approve":\s*true,\s*\n\s*"matchCommandLine":\s*true\s*\n\s*\}',
        
        # 패턴 2: 상대 경로 버전 (라인 3148)
        r',\s*\n\s*"powershell -NoProfile -ExecutionPolicy Bypass -File \.\\\\LLM_Unified\\\\ion-mentoring\\\\scripts\\\\check_monitoring_status\.ps1":\s*\{\s*\n\s*"approve":\s*true,\s*\n\s*"matchCommandLine":\s*true\s*\n\s*\}',
        
        # 패턴 3: 대문자 D 버전 (이스케이프된 따옴표)
        r',\s*\n\s*"powershell -NoProfile -ExecutionPolicy Bypass -File \\"D:\\\\\\\\nas_backup\\\\\\\\LLM_Unified\\\\\\\\ion-mentoring\\\\\\\\scripts\\\\\\\\check_monitoring_status\.ps1\\":\s*\{\s*\n\s*"approve":\s*true,\s*\n\s*"matchCommandLine":\s*true\s*\n\s*\}',
    ]
    
    removed_count = 0
    for i, pattern in enumerate(patterns_to_remove, 1):
        if re.search(pattern, content):
            print(f"✅ 패턴 {i} 발견")
            content = re.sub(pattern, '', content, count=1)
            removed_count += 1
        else:
            print(f"⚠️  패턴 {i} 미발견")
    
    new_length = len(content)
    print(f"\n📊 결과: {original_length:,} → {new_length:,} 문자 (제거: {original_length - new_length:,})")
    print(f"   중복 항목 제거: {removed_count}개")
    
    # 저장
    with open(settings_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ 저장 완료")
    
    # JSON 검증
    print("\n🔍 JSON 유효성 검증...")
    try:
        json.loads(content)
        print("✅ JSON 유효!")
        return True
    except json.JSONDecodeError as e:
        print(f"❌ JSON 에러: {e}")
        print(f"   라인 {e.lineno}, 컬럼 {e.colno}")
        print(f"\n주변 내용:")
        lines = content.split('\n')
        start = max(0, e.lineno - 3)
        end = min(len(lines), e.lineno + 3)
        for i in range(start, end):
            prefix = ">>> " if i == e.lineno - 1 else "    "
            print(f"{prefix}{i+1}: {lines[i][:100]}")
        return False

if __name__ == '__main__':
    settings_path = Path(os.environ['APPDATA']) / 'Code' / 'User' / 'settings.json'
    
    if not settings_path.exists():
        print(f"❌ 파일 없음: {settings_path}")
        exit(1)
    
    success = remove_check_monitoring_duplicates(str(settings_path))
    exit(0 if success else 1)
