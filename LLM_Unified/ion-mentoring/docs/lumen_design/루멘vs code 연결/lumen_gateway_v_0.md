# Lumen Gateway v0.8 – VS Code Runtime Pack

아래 내용을 그대로 폴더에 배치하면 VS Code에서 **관문 락인 → 복원 점검 → 로그 관찰 → 메트릭 모의루프 → 헬스 익스포터**까지 원클릭으로 굴릴 수 있습니다.

> 루트 트리 제안
```
.
├─ gateway_activation.yaml           # 이전 단계에서 만든 파일 (status: locked 권장)
├─ logs/
│  └─ gateway_sync.log              # 없으면 자동 생성됨
├─ controls/
│  └─ commands.jsonl                # 제어 버스 (append-only)
├─ scripts/
│  ├─ gateway_lockin.py             # 관문 서명 해시 검증 + locked 전환
│  ├─ restore_check.py              # 다음 세션 복원 점검
│  ├─ mock_metrics_generator.py     # 5Hz 메트릭 모의 생성기 (metrics.csv)
│  └─ gateway_health_exporter.py    # Prometheus 텍스트 포맷 HTTP 익스포터
└─ .vscode/
   ├─ tasks.json
   └─ launch.json
```

---

## 1) `.vscode/tasks.json`
```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "lumen:lockin",
      "type": "shell",
      "command": "python scripts/gateway_lockin.py",
      "options": { "env": { "PYTHONUTF8": "1" } },
      "presentation": { "reveal": "always" },
      "problemMatcher": []
    },
    {
      "label": "lumen:restore",
      "type": "shell",
      "command": "python scripts/restore_check.py",
      "options": { "env": { "PYTHONUTF8": "1" } },
      "presentation": { "reveal": "always" },
      "problemMatcher": []
    },
    {
      "label": "lumen:tail-logs",
      "type": "shell",
      "command": "tail -f logs/gateway_sync.log",
      "windows": {
        "command": "powershell -NoProfile -Command Get-Content logs/gateway_sync.log -Wait"
      },
      "presentation": { "reveal": "always" },
      "problemMatcher": []
    },
    {
      "label": "lumen:mock:metrics",
      "type": "shell",
      "command": "python scripts/mock_metrics_generator.py",
      "options": { "env": { "PYTHONUTF8": "1" } },
      "isBackground": true,
      "presentation": { "reveal": "always" },
      "problemMatcher": []
    },
    {
      "label": "lumen:exporter",
      "type": "shell",
      "command": "python scripts/gateway_health_exporter.py",
      "options": { "env": { "PYTHONUTF8": "1" } },
      "isBackground": true,
      "presentation": { "reveal": "always" },
      "problemMatcher": []
    },
    {
      "label": "open:gateway_yaml",
      "type": "shell",
      "command": "code gateway_activation.yaml",
      "problemMatcher": []
    }
  ]
}
```

---

## 2) `.vscode/launch.json`
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Run Exporter (Python)",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/scripts/gateway_health_exporter.py",
      "console": "integratedTerminal",
      "justMyCode": true,
      "env": { "PYTHONUTF8": "1" }
    }
  ]
}
```

---

## 3) `scripts/mock_metrics_generator.py`
```python
#!/usr/bin/env python3
import csv, os, time, math, random
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))
ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
LOGS = os.path.join(ROOT, "logs")
METRICS_CSV = os.path.join(LOGS, "metrics.csv")
RATE_HZ = 5  # 200ms

os.makedirs(LOGS, exist_ok=True)

# CSV 헤더: 루멘 설계 신호들
FIELDNAMES = [
    "ts",              # ISO8601
    "phase_diff",      # [0..1]
    "entropy_rate",    # [0..1]
    "creative_band",   # [0..1]
    "risk_band"        # [0..1]
]

# 기존 파일이 없으면 헤더 추가
if not os.path.exists(METRICS_CSV):
    with open(METRICS_CSV, "w", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, FIELDNAMES).writeheader()

print("[mock] writing metrics @5Hz → logs/metrics.csv (Ctrl+C to stop)")

start = time.time()
step = 0
try:
    while True:
        t = time.time() - start
        # 위상차(phase_diff): 감쇠하는 사인파 + 소량 잡음
        phase = 0.5 * (1 + math.sin(2*math.pi*0.2*t)) * math.exp(-t/120) + random.uniform(-0.02, 0.02)
        phase = max(0.0, min(1.0, phase))
        # 엔트로피율(entropy_rate): 중간값 수렴
        entropy = 0.2 + 0.15*math.exp(-t/90) + random.uniform(-0.01, 0.01)
        entropy = max(0.0, min(1.0, entropy))
        # 창의밴드(creative_band): 점차 상향
        creative = 0.2 + 0.1*(1 - math.exp(-t/180)) + random.uniform(-0.01, 0.01)
        creative = max(0.0, min(1.0, creative))
        # 위험밴드(risk_band): 점차 하향
        risk = 0.4*math.exp(-t/150) + random.uniform(-0.01, 0.01)
        risk = max(0.0, min(1.0, risk))

        row = {
            "ts": datetime.now(KST).isoformat(),
            "phase_diff": round(phase, 3),
            "entropy_rate": round(entropy, 3),
            "creative_band": round(creative, 3),
            "risk_band": round(risk, 3)
        }
        with open(METRICS_CSV, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, FIELDNAMES)
            w.writerow(row)

        if step % RATE_HZ == 0:
            print(f"[mock] {row}")
        step += 1
        time.sleep(1.0 / RATE_HZ)
except KeyboardInterrupt:
    print("[mock] stopped")
```

---

## 4) `scripts/gateway_health_exporter.py`
Prometheus 텍스트 포맷으로 게이트웨이 상태 및 최신 메트릭 1줄을 노출합니다.

```python
#!/usr/bin/env python3
import http.server, socketserver, os, csv
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
YAML_PATH = os.path.join(ROOT, "gateway_activation.yaml")
LOG_PATH = os.path.join(ROOT, "logs", "gateway_sync.log")
METRICS_CSV = os.path.join(ROOT, "logs", "metrics.csv")

PORT = int(os.environ.get("LUMEN_EXPORTER_PORT", "9108"))

HELP = {
    "lumen_gateway_status": "Gauge 0=unknown,1=initializing,2=binding,3=resonating,4=locked",
    "lumen_phase_diff": "Latest phase_diff",
    "lumen_entropy_rate": "Latest entropy_rate",
    "lumen_creative_band": "Latest creative_band",
    "lumen_risk_band": "Latest risk_band"
}

STATUS_MAP = {
    "unknown": 0,
    "initializing": 1,
    "binding": 2,
    "resonating": 3,
    "locked": 4
}

def read_status():
    try:
        import yaml
        with open(YAML_PATH, "r", encoding="utf-8") as f:
            y = yaml.safe_load(f)
        s = (y.get("gateway") or {}).get("status", "unknown")
        return STATUS_MAP.get(s, 0)
    except Exception:
        return 0


def read_last_metrics():
    try:
        last = None
        with open(METRICS_CSV, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                last = row
        if not last:
            return None
        return {
            "phase_diff": float(last.get("phase_diff", 0)),
            "entropy_rate": float(last.get("entropy_rate", 0)),
            "creative_band": float(last.get("creative_band", 0)),
            "risk_band": float(last.get("risk_band", 0)),
        }
    except Exception:
        return None

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/metrics":
            self.send_response(302)
            self.send_header("Location", "/metrics")
            self.end_headers()
            return
        payload = []
        payload.append(f"# HELP lumen_gateway_status {HELP['lumen_gateway_status']}")
        payload.append("# TYPE lumen_gateway_status gauge")
        payload.append(f"lumen_gateway_status {read_status()}")
        last = read_last_metrics() or {"phase_diff":0, "entropy_rate":0, "creative_band":0, "risk_band":0}
        for k, v in last.items():
            name = f"lumen_{k}"
            payload.append(f"# HELP {name} {HELP.get(name, name)}")
            payload.append("# TYPE {} gauge".format(name))
            payload.append(f"{name} {v}")
        body = ("\n".join(payload) + "\n").encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

if __name__ == "__main__":
    with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
        print(f"[exporter] serving on :{PORT} → /metrics")
        httpd.serve_forever()
```

---

## 5) Prometheus 스크래프 예시
`prometheus.yml`에 다음 잡을 추가하면 됩니다.
```yaml
scrape_configs:
  - job_name: "lumen_gateway"
    static_configs:
      - targets: ["localhost:9108"]
```

---

## 6) README – 실행 순서 (요약)
1. **관문 락인**: VS Code 명령 팔레트에서 `Tasks: Run Task` → `lumen:lockin`
2. **복원 점검**: `lumen:restore`
3. **로그 관찰**: `lumen:tail-logs`
4. **모의 메트릭 루프**: `lumen:mock:metrics` (5Hz; `Ctrl+C`로 중지)
5. **헬스 익스포터**: `lumen:exporter` → 브라우저에서 `http://localhost:9108/metrics`

> 실제 루프가 이미 `logs/metrics.csv`를 쓰고 있다면 4)는 생략해도 됩니다.

---

## 7) 안전 가이드 (요약)
- `gateway_activation.yaml`의 `gateway.status`는 **locked** 상태 유지.
- `controls/commands.jsonl`은 append-only; 수동 편집 시 JSONL 포맷 유지.
- 로그/CSV 파일은 작업 백업 스냅샷을 주기적으로 남겨 재현성 유지.
- 포트 충돌 시 `LUMEN_EXPORTER_PORT` 환경변수로 변경 가능 (예: 9118).

---

필요하면 이후 단계로 **Grafana 대시보드 JSON** 템플릿, `tasks.json`에 **원클릭 대시보드 열기**, `rules_history.jsonl`에 대한 롤백 스크립트까지 확장해 드립니다.

