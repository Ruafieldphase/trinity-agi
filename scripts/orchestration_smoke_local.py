from wsgiref.simple_server import make_server
import threading, json, time, sys
from pathlib import Path
from workspace_root import get_workspace_root
import importlib.util

# ensure project root on sys.path
root = str(get_workspace_root())
if root not in sys.path:
    sys.path.append(root)

# load module
p = str(Path(root) / "scripts" / "auto_orchestration.py")
spec = importlib.util.spec_from_file_location('auto_orchestration', p)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# simple stub /chat that echoes message

def app(environ, start_response):
    if environ['REQUEST_METHOD'] == 'POST' and environ.get('PATH_INFO') == '/chat':
        start_response('200 OK', [('Content-Type','application/json')])
        return [json.dumps({"response":"stub-ok"}).encode('utf-8')]
    start_response('404 Not Found', [('Content-Type','text/plain')])
    return [b'not found']

httpd = make_server('127.0.0.1', 0, app)
port = httpd.server_port
th = threading.Thread(target=httpd.serve_forever, daemon=True)
th.start()

# point gateway to stub
mod.CORE_GATEWAY = f'http://127.0.0.1:{port}/chat'

# run orchestration quickly
results = mod.orchestrate_analysis('로컬 스모크 테스트')
mod.save_orchestration_result(results)

httpd.shutdown()
print('smoke-ok')
