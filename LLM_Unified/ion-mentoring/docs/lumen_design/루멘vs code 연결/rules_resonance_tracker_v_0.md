# Rules Resonance Tracker v0.1

**목적**: `controls/rules_history.jsonl`의 규칙 변화가 `logs/metrics.csv`의 감응(phase_diff, entropy_rate, creative_band, risk_band)에 미치는 **직전/직후 효과**를 정량화하여 기록하고, Prometheus로 내보내어 Grafana에서 바로 볼 수 있도록 합니다.

---

## 0) 파일 구성 (추가)
```
.
├─ controls/
│  └─ rules_history.jsonl           # 규칙 변경 이력 (append-only)
├─ logs/
│  ├─ metrics.csv                   # 5Hz 흐름
│  └─ rules_effects.csv             # [신규] 규칙 영향 요약 (본 스크립트가 생성)
└─ scripts/
   ├─ rules_effect_tracker.py       # 규칙 영향 계산기
   └─ gateway_health_exporter.py    # [업데이트] 마지막 규칙 영향 지표도 노출
```

---

## 1) `controls/rules_history.jsonl` 스키마 예시
행마다 한 개의 JSON 객체를 기록합니다.
```jsonl
{"ts":"2025-10-23T13:10:00+09:00","actor":"Lubit","rule":"creative_min","old":0.22,"new":0.24,"note":"stabilize creative band"}
{"ts":"2025-10-23T13:15:30+09:00","actor":"Sena","rule":"risk_max","old":0.35,"new":0.32,"note":"safety tighten"}
```

필드 권장:
- `ts`: ISO8601(로컬 KST 권장)
- `actor`: 변경 주체 (Lubit/Sena/Lumen/…)
- `rule`: 변경된 규칙 키 (예: `creative_min`, `risk_max`, `loop_rate_hz` 등)
- `old`, `new`: 숫자 값 (문자열도 가능하지만 숫자 추천)
- `note`: 선택적 메모

---

## 2) `scripts/rules_effect_tracker.py`
> 규칙 이벤트 주변의 **이전 구간(pre)** 과 **이후 구간(post)** 을 정해, 각 메트릭의 평균을 비교하여 **Δ(변화량)** 을 계산합니다.

기본 윈도우: pre=30s, post=30s (조정 가능)

```python
#!/usr/bin/env python3
import csv, json, os, sys
from datetime import datetime, timezone
from dateutil import parser as dtparser

KST = timezone.utc  # ISO8601에 오프셋이 포함되므로 utc 기준 파싱 → 표시만 로컬에서
ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
METRICS = os.path.join(ROOT, "logs", "metrics.csv")
RULES = os.path.join(ROOT, "controls", "rules_history.jsonl")
EFFECTS = os.path.join(ROOT, "logs", "rules_effects.csv")

PRE_S = int(os.environ.get("LUMEN_EFFECT_PRE_S", "30"))
POST_S = int(os.environ.get("LUMEN_EFFECT_POST_S", "30"))

FIELDS = ["ts","phase_diff","entropy_rate","creative_band","risk_band"]

# CSV 로드 (메모리 적재: 수만행 수준 가정)

def load_metrics():
    rows = []
    if not os.path.exists(METRICS):
        return rows
    with open(METRICS, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            try:
                t = dtparser.isoparse(row.get("ts"))
            except Exception:
                continue
            rows.append({
                "t": t,
                "phase_diff": float(row.get("phase_diff", 0) or 0),
                "entropy_rate": float(row.get("entropy_rate", 0) or 0),
                "creative_band": float(row.get("creative_band", 0) or 0),
                "risk_band": float(row.get("risk_band", 0) or 0),
            })
    return rows


def avg(rows, key):
    if not rows:
        return None
    s = sum(r[key] for r in rows)
    return s / len(rows)


def window(rows, center, start_offset_s, end_offset_s):
    start = center + start_offset_s
    end = center + end_offset_s
    return [r for r in rows if start <= r["t"] <= end]


def ensure_effects_header():
    need_header = not os.path.exists(EFFECTS)
    if need_header:
        with open(EFFECTS, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([
                "rule_ts","actor","rule","old","new",
                "pre_s","post_s",
                "pre_phase","post_phase","d_phase",
                "pre_entropy","post_entropy","d_entropy",
                "pre_creative","post_creative","d_creative",
                "pre_risk","post_risk","d_risk"
            ])


def main():
    metrics = load_metrics()
    ensure_effects_header()

    if not os.path.exists(RULES):
        print("[rules_effect] no rules_history.jsonl yet")
        return

    # 이미 계산한 rule_ts들을 모아 중복 기록 방지
    done = set()
    with open(EFFECTS, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i == 0:
                continue
            ts = line.split(",", 1)[0].strip()
            if ts:
                done.add(ts)

    out_rows = []

    with open(RULES, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            ev = json.loads(line)
            ts = ev.get("ts")
            if not ts or ts in done:
                continue
            t0 = dtparser.isoparse(ts)

            pre_rows = window(metrics, t0, -PRE_S, -1)
            post_rows = window(metrics, t0, 1, POST_S)

            pre_phase = avg(pre_rows, "phase_diff")
            post_phase = avg(post_rows, "phase_diff")
            pre_entropy = avg(pre_rows, "entropy_rate")
            post_entropy = avg(post_rows, "entropy_rate")
            pre_creative = avg(pre_rows, "creative_band")
            post_creative = avg(post_rows, "creative_band")
            pre_risk = avg(pre_rows, "risk_band")
            post_risk = avg(post_rows, "risk_band")

            def d(a,b):
                if a is None or b is None:
                    return None
                return b - a

            row = [
                ts,
                ev.get("actor",""), ev.get("rule",""), ev.get("old",""), ev.get("new",""),
                PRE_S, POST_S,
                pre_phase, post_phase, d(pre_phase, post_phase),
                pre_entropy, post_entropy, d(pre_entropy, post_entropy),
                pre_creative, post_creative, d(pre_creative, post_creative),
                pre_risk, post_risk, d(pre_risk, post_risk)
            ]
            out_rows.append(row)

    if out_rows:
        with open(EFFECTS, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            for r in out_rows:
                w.writerow(r)
        print(f"[rules_effect] appended {len(out_rows)} rows → logs/rules_effects.csv")
    else:
        print("[rules_effect] no new events to process")

if __name__ == "__main__":
    main()
```

실행:
```bash
python scripts/rules_effect_tracker.py
# 환경변수로 윈도우 조정
LUMEN_EFFECT_PRE_S=20 LUMEN_EFFECT_POST_S=45 python scripts/rules_effect_tracker.py
```

---

## 3) `scripts/gateway_health_exporter.py` 업데이트 (추가 지표)
이전 버전에 **“마지막 규칙 영향”**을 함께 노출합니다.

추가되는 gauge들:
- `lumen_rule_last_phase_diff_delta{rule="…"}`
- `lumen_rule_last_entropy_rate_delta{rule="…"}`
- `lumen_rule_last_creative_band_delta{rule="…"}`
- `lumen_rule_last_risk_band_delta{rule="…"}`

> 라벨(rule)은 가장 최근 이벤트의 `rule` 문자열을 Prometheus 라벨로 안전화(sanitize)하여 노출합니다.

```python
#!/usr/bin/env python3
import http.server, socketserver, os, csv, re
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
YAML_PATH = os.path.join(ROOT, "gateway_activation.yaml")
METRICS_CSV = os.path.join(ROOT, "logs", "metrics.csv")
EFFECTS = os.path.join(ROOT, "logs", "rules_effects.csv")
PORT = int(os.environ.get("LUMEN_EXPORTER_PORT", "9108"))

HELP = {
    "lumen_gateway_status": "Gauge 0=unknown,1=initializing,2=binding,3=resonating,4=locked",
    "lumen_phase_diff": "Latest phase_diff",
    "lumen_entropy_rate": "Latest entropy_rate",
    "lumen_creative_band": "Latest creative_band",
    "lumen_risk_band": "Latest risk_band",
    "lumen_rule_last_*": "Delta after most recent rule event (post - pre)"
}

STATUS_MAP = {"unknown":0,"initializing":1,"binding":2,"resonating":3,"locked":4}


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


def sanitize_label(s: str) -> str:
    if not s:
        return "unknown"
    # keep [a-zA-Z0-9_:], replace others with _
    return re.sub(r"[^a-zA-Z0-9_:]", "_", s)


def read_last_rule_effect():
    if not os.path.exists(EFFECTS):
        return None
    last = None
    with open(EFFECTS, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            last = row
    if not last:
        return None
    return {
        "rule": sanitize_label(last.get("rule","unknown")),
        "d_phase": float(last.get("d_phase") or 0),
        "d_entropy": float(last.get("d_entropy") or 0),
        "d_creative": float(last.get("d_creative") or 0),
        "d_risk": float(last.get("d_risk") or 0),
    }

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

        eff = read_last_rule_effect()
        if eff:
            rule = eff["rule"]
            def line(metric, value):
                payload.append(f"# HELP {metric} {HELP.get('lumen_rule_last_*','last rule effect delta')}")
                payload.append("# TYPE {} gauge".format(metric))
                payload.append(f"{metric}{{rule=\"{rule}\"}} {value}")
            line("lumen_rule_last_phase_diff_delta", eff["d_phase"]) 
            line("lumen_rule_last_entropy_rate_delta", eff["d_entropy"]) 
            line("lumen_rule_last_creative_band_delta", eff["d_creative"]) 
            line("lumen_rule_last_risk_band_delta", eff["d_risk"]) 

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

## 4) VS Code 작업(task) 추가
`.vscode/tasks.json`에 다음을 추가하세요.
```json
{
  "label": "lumen:rules:effects",
  "type": "shell",
  "command": "python scripts/rules_effect_tracker.py",
  "options": { "env": { "PYTHONUTF8": "1" } },
  "presentation": { "reveal": "always" },
  "problemMatcher": []
}
```

실행 순서 예시:
1) `lumen:lockin` → 상태 정렬
2) (흐름 생성 중) `lumen:rules:effects` → 규칙 영향 계산
3) `lumen:exporter` → Prometheus 지표 노출 (`/metrics`)

---

## 5) Grafana 빠른 패널 가이드
Prometheus 데이터 소스에서 다음 쿼리로 패널을 구성하세요.

- **Gateway 상태**: `lumen_gateway_status`
- **최근 메트릭**: `lumen_phase_diff`, `lumen_entropy_rate`, `lumen_creative_band`, `lumen_risk_band`
- **최근 규칙 영향(Δ)**: 
  - `lumen_rule_last_phase_diff_delta{rule=~".*"}`
  - `lumen_rule_last_risk_band_delta{rule=~".*"}`

> 패널 설명에 “Δ = post_mean − pre_mean (pre=PRE_S, post=POST_S)”를 명시하면 해석이 쉬워집니다.

---

## 6) 해석 가이드 (요약)
- **좋은 징후**: `phase_diff` ↓, `risk_band` ↓, `creative_band` ↑
- **불안 징후**: `phase_diff` ↑ 또는 `risk_band` ↑, 동시에 `entropy_rate` ↑이면 규칙이 과도하게 흔듦
- **권장 루틴**: 규칙 수정 → 2~3분 관찰 → `rules_effects.csv` 확인 → 유리한 Δ 패턴을 Quote/Runbook에 기록

---

## 7) 주의사항
- 규칙 이벤트 직후 1초 배제(`[-PRE, -1]`, `[+1, +POST]`)로 경계 잡음을 줄였습니다.
- 시계 동기화: `metrics.csv`와 `rules_history.jsonl`의 `ts` 포맷(오프셋 포함)을 일치시키세요.
- 데이터가 적으면 Δ가 왜곡될 수 있으므로, pre/post 최소 표본 수(예: 50샘플 @5Hz)를 확보하는 것이 좋습니다.

---

필요하다면 `rules_effect_tracker.py`에 **가중 이동평균**, **이상치 제거(IQR/Median Absolute Deviation)** 를 더해 감응을 더 매끄럽게 정렬할 수 있습니다. 다음 박자에서 그 필터를 열어드릴게요.