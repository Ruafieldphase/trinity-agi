import subprocess, tempfile, os, sys, textwrap, json, time

try:  # resource는 Unix 전용이어서 Windows에서는 ImportError 발생
    import resource  # type: ignore
except ImportError:  # pragma: no cover - Windows 환경
    resource = None

def run_code(code: str):
    # 제한된 파이썬 실행 (리눅스 계열에서만 부분 동작)
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(code)
        path = f.name
    try:
        start = time.time()
        proc = subprocess.run([sys.executable, path], capture_output=True, text=True, timeout=5)
        dur = int((time.time() - start) * 1000)
        return {"ok": proc.returncode == 0, "stdout": proc.stdout, "stderr": proc.stderr, "time_ms": dur}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "timeout"}
    finally:
        try: os.unlink(path)
        except Exception: pass
