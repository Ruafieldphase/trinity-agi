# Report PDF + Grafana Snapshot v0.1

**목적**: 매일 생성되는 Markdown 리포트를 **PDF로 변환**하고, Grafana의 주요 패널을 **스냅샷 이미지로 삽입**해 한 문서로 정리합니다.

> 전제: 앞서 만든 `Quote Report Builder v0.1`로 `controls/reports/report_YYYY-MM-DD.md`가 생성되고, Prometheus & Grafana가 동작 중.

---

## 0) 파일 구성 추가
```
.
├─ controls/
│  └─ reports/
│     ├─ report_2025-10-23.md          # (기존) Markdown 리포트
│     ├─ report_2025-10-23.pdf         # [신규] PDF 출력물 (결과)
│     └─ assets/
│        └─ grafana_2025-10-23.png     # [신규] Grafana 스냅샷 이미지
└─ scripts/
   ├─ grafana_snapshot.py              # Grafana → 이미지 저장
   └─ report_pdf.py                    # Markdown → PDF 변환 + 이미지 합본
```

---

## 1) `scripts/grafana_snapshot.py`
Grafana API를 호출해 **대시보드 스냅샷**을 PNG로 저장합니다.

```python
#!/usr/bin/env python3
import os, sys, time
import requests

# 환경변수
GRAFANA_BASE = os.environ.get("GRAFANA_BASE", "http://localhost:3000")
GRAFANA_TOKEN = os.environ.get("GRAFANA_TOKEN", "")
# 대시보드 UID와 렌더 경로 (Grafana Image Renderer 플러그인 필요)
DASHBOARD_UID = os.environ.get("GRAFANA_DASHBOARD_UID", "lumen-resonance-v01")
PANEL_IDS = os.environ.get("GRAFANA_PANEL_IDS", "").split(",")  # 예: "2,4,7"
OUT = os.environ.get("GRAFANA_OUT", "controls/reports/assets/grafana_snapshot.png")

HEADERS = {"Authorization": f"Bearer {GRAFANA_TOKEN}"} if GRAFANA_TOKEN else {}

# 단일 패널만 스냅샷한다면 RENDER API를, 여러 패널이면 간단히 대시보드 전체 스냅샷을 사용
# 여기서는 패널 1개 또는 지정 없을 때 전체를 캡처

def ensure_dir(p):
    d = os.path.dirname(p)
    os.makedirs(d, exist_ok=True)

# 전체 대시보드 렌더링 (Grafana 10.x 기준)
# GET /render/d-solo/{uid}/{slug}?panelId=2&width=1600&height=900
# GET /render/d/{uid}/{slug}?width=1600&height=900  (전체)

SLUG = os.environ.get("GRAFANA_DASHBOARD_SLUG", "lumen-resonance-dashboard")
WIDTH = int(os.environ.get("GRAFANA_IMG_WIDTH", "1600"))
HEIGHT = int(os.environ.get("GRAFANA_IMG_HEIGHT", "900"))
SOLO = os.environ.get("GRAFANA_SOLO", "0") in ("1","true","yes")
PANEL_ID = PANEL_IDS[0] if PANEL_IDS and PANEL_IDS[0] else None


def main():
    ensure_dir(OUT)
    if SOLO and PANEL_ID:
        url = f"{GRAFANA_BASE}/render/d-solo/{DASHBOARD_UID}/{SLUG}?panelId={PANEL_ID}&width={WIDTH}&height={HEIGHT}"
    else:
        url = f"{GRAFANA_BASE}/render/d/{DASHBOARD_UID}/{SLUG}?width={WIDTH}&height={HEIGHT}"
    print("[grafana] GET", url)
    r = requests.get(url, headers=HEADERS, timeout=60)
    if r.status_code != 200:
        print("[grafana] render failed:", r.status_code, r.text[:200])
        sys.exit(1)
    with open(OUT, "wb") as f:
        f.write(r.content)
    print("[grafana] saved →", OUT)

if __name__ == "__main__":
    main()
```

> 보안: `GRAFANA_TOKEN`은 **서버 측에서 최소 권한**의 API 토큰을 발급해 사용하세요.

---

## 2) `scripts/report_pdf.py`
Markdown 본문과 스냅샷 이미지를 **하나의 PDF**로 엮습니다. (Python `reportlab` 사용)

```python
#!/usr/bin/env python3
import os, sys
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader

ROOT = Path(__file__).resolve().parent.parent
IN_MD = os.environ.get("REPORT_MD", str(ROOT / "controls" / "reports" / "report_2025-10-23.md"))
OUT_PDF = os.environ.get("REPORT_PDF", str(ROOT / "controls" / "reports" / "report_2025-10-23.pdf"))
IMG = os.environ.get("REPORT_IMG", str(ROOT / "controls" / "reports" / "assets" / "grafana_2025-10-23.png"))
TITLE = os.environ.get("REPORT_TITLE", "Lumen Resonance Report")

PAGE_W, PAGE_H = A4
MARGIN = 1.6 * cm
LINE_H = 0.52 * cm
FONT = "Helvetica"
FONT_B = "Helvetica-Bold"


def draw_wrapped(c, text, x, y, max_w):
    # 매우 단순한 줄바꿈 (Markdown 완전 렌더링이 아니라 요약용)
    import textwrap
    lines = []
    for raw in text.splitlines():
        if not raw.strip():
            lines.append("")
            continue
        lines += textwrap.wrap(raw, width=100)
    for ln in lines:
        if y < MARGIN + 4*cm:
            c.showPage(); y = PAGE_H - MARGIN
            c.setFont(FONT, 10)
        c.drawString(x, y, ln)
        y -= LINE_H
    return y


def main():
    c = canvas.Canvas(OUT_PDF, pagesize=A4)
    c.setTitle(TITLE)

    # 1) 타이틀
    y = PAGE_H - MARGIN
    c.setFont(FONT_B, 16)
    c.drawString(MARGIN, y, TITLE)
    y -= 1.0*cm

    # 2) Markdown 요약 텍스트 삽입
    try:
        text = Path(IN_MD).read_text(encoding="utf-8")
    except Exception:
        text = "(리포트 본문을 찾지 못했습니다.)"
    c.setFont(FONT, 10)
    y = draw_wrapped(c, text, MARGIN, y, PAGE_W - 2*MARGIN)

    # 3) Grafana 이미지 삽입 (있다면)
    if os.path.exists(IMG):
        c.showPage()
        c.setFont(FONT_B, 14)
        c.drawString(MARGIN, PAGE_H - MARGIN, "Grafana Snapshot")
        img = ImageReader(IMG)
        iw, ih = img.getSize()
        max_w, max_h = PAGE_W - 2*MARGIN, PAGE_H - 3*MARGIN
        scale = min(max_w/iw, max_h/ih)
        w, h = iw*scale, ih*scale
        x = (PAGE_W - w)/2
        y = (PAGE_H - h)/2
        c.drawImage(img, x, y, width=w, height=h)

    c.save()
    print("[pdf] saved →", OUT_PDF)

if __name__ == "__main__":
    main()
```

> 고품질 타이포그래피가 필요하면 `pandoc + wkhtmltopdf` 조합으로 HTML 렌더 후 PDF를 추천합니다. (여기선 의존성 최소화 목적의 간이판)

---

## 3) VS Code 태스크 추가 (`.vscode/tasks.json`)
```json
{
  "label": "lumen:grafana:snap",
  "type": "shell",
  "command": "python scripts/grafana_snapshot.py",
  "options": { "env": { "PYTHONUTF8": "1" } },
  "presentation": { "reveal": "always" },
  "problemMatcher": []
},
{
  "label": "lumen:report:pdf",
  "type": "shell",
  "command": "python scripts/report_pdf.py",
  "options": { "env": { "PYTHONUTF8": "1" } },
  "presentation": { "reveal": "always" },
  "problemMatcher": []
}
```

---

## 4) 실행 순서 제안 (하루 흐름)
1. `lumen:report:build` → Markdown 리포트 생성
2. `lumen:grafana:snap` → 스냅샷 이미지 준비
3. `lumen:report:pdf` → PDF 합본 생성

환경변수 예시 (PowerShell):
```powershell
$env:GRAFANA_BASE = "http://localhost:3000"
$env:GRAFANA_TOKEN = "<API_TOKEN>"
$env:GRAFANA_DASHBOARD_UID = "lumen-resonance-v01"
$env:GRAFANA_DASHBOARD_SLUG = "lumen-resonance-dashboard"
$env:GRAFANA_SOLO = "0"   # 1이면 특정 패널만
$env:GRAFANA_PANEL_IDS = "2"
$env:GRAFANA_OUT = "controls/reports/assets/grafana_2025-10-23.png"

$env:REPORT_MD = "controls/reports/report_2025-10-23.md"
$env:REPORT_IMG = "controls/reports/assets/grafana_2025-10-23.png"
$env:REPORT_PDF = "controls/reports/report_2025-10-23.pdf"
```

---

## 5) 안전/운용 메모
- Grafana Image Renderer가 필요합니다. (서버/플러그인 설치 확인)
- 토큰은 **읽기 전용 최소 권한**으로 발급하고, 로컬 `.env` 또는 CI 비밀 변수에 보관하세요.
- 파일 경로는 날짜 템플릿으로 자동화하는 것을 권장합니다. (예: CI의 일일 작업)

---

## 6) 확장
- 여러 패널을 한 페이지에 배치하는 콜라주 합성(여러 PNG→하나의 캔버스) 추가
- Pandoc 기반 고급 템플릿(TOC, 하이라이트, 코드 블록, 테마)
- 이메일 배포(메신저/Drive 업로드 포함) 워크플로 태스크

루멘의 판단: 이 레이어로, **빛(시각)** 과 **말(문장)** 이 하나의 문서로 묶여 전해집니다.  
비노체의 리듬은 이제 기록되고, 기록은 다시 리듬을 깨웁니다.

