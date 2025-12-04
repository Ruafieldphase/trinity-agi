"""
UTF-8 인코딩 강제 설정 모듈

Windows 환경에서 한글 깨짐 방지를 위한 공통 유틸리티.
모든 Python 스크립트 시작 부분에서 import하여 사용.

Usage:
    import encoding_setup  # 이것만으로 자동 적용
    
또는:
    from encoding_setup import ensure_utf8
    ensure_utf8()

Author: GitHub Copilot
Created: 2025-10-29
"""

import sys
import io
import locale

def ensure_utf8():
    """
    stdout, stderr, stdin을 UTF-8로 강제 설정
    
    Windows PowerShell에서 CP949 인코딩으로 인한 한글 깨짐 방지.
    이 함수는 스크립트 시작 시 한 번만 호출하면 됩니다.
    """
    # Python 3.7+ 에서 권장하는 방법: reconfigure
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
            if hasattr(sys.stdin, 'reconfigure'):
                sys.stdin.reconfigure(encoding='utf-8')
        except Exception:
            # reconfigure 실패 시 fallback
            pass
    
    # 이전 방식 (Python 3.6 이하 호환)
    if sys.stdout.encoding != 'utf-8':
        try:
            sys.stdout = io.TextIOWrapper(
                sys.stdout.buffer if hasattr(sys.stdout, 'buffer') else sys.stdout,
                encoding='utf-8',
                errors='replace'
            )
        except Exception:
            pass
    
    if sys.stderr.encoding != 'utf-8':
        try:
            sys.stderr = io.TextIOWrapper(
                sys.stderr.buffer if hasattr(sys.stderr, 'buffer') else sys.stderr,
                encoding='utf-8',
                errors='replace'
            )
        except Exception:
            pass
    
    # 환경변수 설정 (subprocess 실행 시에도 적용)
    import os
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    # locale 설정 (파일 I/O 기본 인코딩)
    try:
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    except Exception:
        try:
            locale.setlocale(locale.LC_ALL, 'ko_KR.UTF-8')
        except Exception:
            pass  # locale 설정 실패 시 무시 (Windows에서 자주 발생)


# 모듈 import 시 자동 실행
ensure_utf8()


# 파일 열기 헬퍼 (UTF-8 강제)
def open_utf8(filepath, mode='r', **kwargs):
    """
    UTF-8 인코딩으로 파일 열기
    
    Args:
        filepath: 파일 경로
        mode: 파일 모드 ('r', 'w', 'a' 등)
        **kwargs: open() 함수의 추가 인자
        
    Returns:
        파일 객체
        
    Example:
        with open_utf8('data.txt', 'w') as f:
            f.write('한글 테스트')
    """
    if 'encoding' not in kwargs:
        kwargs['encoding'] = 'utf-8'
    if 'errors' not in kwargs:
        kwargs['errors'] = 'replace'
    
    return open(filepath, mode, **kwargs)


# JSON 로드/덤프 헬퍼 (ensure_ascii=False)
def load_json_utf8(filepath):
    """UTF-8 JSON 파일 로드"""
    import json
    with open_utf8(filepath, 'r') as f:
        return json.load(f)


def save_json_utf8(data, filepath, indent=2):
    """UTF-8 JSON 파일 저장 (한글 깨짐 없음)"""
    import json
    with open_utf8(filepath, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)


# 안전한 print (fallback 포함)
def safe_print(*args, **kwargs):
    """
    인코딩 에러에 안전한 print 함수
    
    UnicodeEncodeError 발생 시 자동으로 에러 문자를 '?'로 대체
    """
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # 에러 발생 시 모든 문자열을 ASCII-safe하게 변환
        safe_args = []
        for arg in args:
            if isinstance(arg, str):
                safe_args.append(arg.encode('ascii', 'replace').decode('ascii'))
            else:
                safe_args.append(arg)
        print(*safe_args, **kwargs)


if __name__ == "__main__":
    # 테스트
    import os
    print("=" * 60)
    print("UTF-8 인코딩 설정 테스트")
    print("=" * 60)
    print(f"stdout encoding: {sys.stdout.encoding}")
    print(f"stderr encoding: {sys.stderr.encoding}")
    print(f"PYTHONIOENCODING: {os.environ.get('PYTHONIOENCODING', 'not set')}")
    print()
    print("한글 테스트: 가나다라마바사 ABC 123 !@#")
    print("이모지 테스트: ✅ ⚠️ ❌ 🎯 📊 🚀")
    print()
    
    # 파일 쓰기 테스트
    test_file = "test_utf8_encoding.txt"
    with open_utf8(test_file, 'w') as f:
        f.write("한글 파일 쓰기 테스트\n")
        f.write("UTF-8 인코딩이 올바르게 적용되었습니다.\n")
    
    with open_utf8(test_file, 'r') as f:
        content = f.read()
        print(f"파일 읽기 테스트:\n{content}")
    
    import os
    os.remove(test_file)
    print("✅ 모든 테스트 통과!")
