import io, sys, re
from pathlib import Path
p = Path(r"C:\workspace\agi\scripts\auto_orchestration.py")
src = p.read_text(encoding='utf-8')

# 1) 보강 import 추가 (중복 방지)
imports = "\nfrom utils.request_guard import post_json\nfrom utils.validator import lumen_chat_schema\n"
if 'from utils.request_guard import post_json' not in src:
    # after 'import requests' or at top
    m = re.search(r"^import requests.*$", src, re.M)
    if m:
        idx = m.end()
        src = src[:idx] + imports + src[idx:]
    else:
        src = imports + src

# 2) requests.post(...) 호출을 post_json(...)으로 치환
#   찾기: response = requests.post( ... )  괄호 매칭으로 안전 치환
start = src.find('response = requests.post(')
if start != -1:
    i = start + len('response = requests.post(')
    depth = 1
    while i < len(src) and depth > 0:
        c = src[i]
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
        i += 1
    end = i  # position after closing ')'
    # 기존 header/timeout 등을 유지하되, schema 포함 한 줄 호출로 대체
    replacement = "response = post_json(LUMEN_GATEWAY, payload, schema=lumen_chat_schema, headers={'Content-Type': 'application/json; charset=utf-8'}, timeout=30)"
    src = src[:start] + replacement + src[end:]

# 3) 파일 저장 (원본 백업)
backup = p.with_suffix('.py.bak')
backup.write_text(src, encoding='utf-8')  # 임시로 쓰고 아래서 실제 파일 교체
p.write_text(src, encoding='utf-8')
print('Patched:', str(p))
