"""
UTF-8 강제 설정 유틸리티
모든 Python 스크립트에서 import하여 사용
"""

import io
import os
import sys


def _reconfigure_stream(stream: io.TextIOBase | None) -> None:
    try:
        if not stream:
            return
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        else:
            buf = getattr(stream, "buffer", None)
            if buf is not None:
                wrapped = io.TextIOWrapper(buf, encoding="utf-8", errors="replace")
                if stream is sys.stdout:
                    sys.stdout = wrapped  # type: ignore[assignment]
                elif stream is sys.stderr:
                    sys.stderr = wrapped  # type: ignore[assignment]
    except Exception:
        # encoding 세팅은 절대 앱을 크래시 시키지 않도록
        pass


def force_utf8() -> None:
    """
    UTF-8 출력을 강제하는 함수.
    - 환경변수 설정 (자식 프로세스 포함)
    - Python stdout/stderr를 UTF-8로 재구성
    """
    try:
        os.environ.setdefault("PYTHONIOENCODING", "utf-8")
        os.environ.setdefault("PYTHONUTF8", "1")
        os.environ.setdefault("LANG", "en_US.UTF-8")
    except Exception:
        pass

    _reconfigure_stream(getattr(sys, "stdout", None))
    _reconfigure_stream(getattr(sys, "stderr", None))


def print_safe(text: str) -> None:
    """
    안전한 출력 함수
    이모지와 한글을 포함한 모든 유니코드를 처리
    """
    try:
        print(text)
    except UnicodeEncodeError:
        # 출력 불가능한 문자는 ?로 대체
        safe_text = text.encode('ascii', errors='replace').decode('ascii')
        print(safe_text)
