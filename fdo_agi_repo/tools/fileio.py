import os
ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sandbox")
def _abspath(rel: str) -> str:
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), rel)
    # Sandbox escape 체크: path가 ROOT 디렉토리 내부인지 확인
    if not os.path.abspath(path).startswith(os.path.abspath(ROOT)):
        raise RuntimeError("sandbox escape blocked")
    return path
def read_text(path: str) -> str:
    ap = _abspath(path)
    with open(ap, "r", encoding="utf-8") as f:
        return f.read()
def write_text(path: str, text: str) -> None:
    ap = _abspath(path)
    os.makedirs(os.path.dirname(ap), exist_ok=True)
    with open(ap, "w", encoding="utf-8") as f:
        f.write(text)
