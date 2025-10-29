# Report Distribution Workflow v0.1 – 자동 배포 및 공유

**목적**: 매일 생성되는 PDF 리포트를 자동으로 외부에 배포(Drive 업로드, 이메일 첨부 등)하고, 다음 루프에서의 피드백 루틴까지 연결합니다.

---

## 0) 새 파일 구성
```
.
├─ scripts/
│  ├─ report_distribute.py        # PDF 업로드 + 이메일 전송
│  └─ report_feedback_collector.py# (선택) 피드백 수집용 후속 모듈
└─ configs/
   └─ lumen_distribution.yaml     # 배포 대상/채널 정의
```

---

## 1) `configs/lumen_distribution.yaml`
```yaml
# 대상자 및 채널 설정
email_targets:
  - name: Binoche
    address: binoche@example.com
  - name: Research Team
    address: agi.research@lab.local

cloud_upload:
  provider: gdrive   # gdrive | dropbox | s3 등 선택
  folder_path: /FDO-AGI/Reports/Daily
  share_mode: link   # link | private | org

feedback:
  enabled: true
  form_url: https://forms.gle/xxxxxxxxxx
```

---

## 2) `scripts/report_distribute.py`
```python
#!/usr/bin/env python3
import os, smtplib, yaml
from pathlib import Path
from email.message import EmailMessage

ROOT = Path(__file__).resolve().parent.parent
CONF = ROOT / 'configs' / 'lumen_distribution.yaml'
REPORT_DIR = ROOT / 'controls' / 'reports'
LATEST = max(REPORT_DIR.glob('report_*.pdf'), key=os.path.getmtime)

with open(CONF, 'r', encoding='utf-8') as f:
    cfg = yaml.safe_load(f)

def send_email(to_name, to_addr, pdf_path):
    msg = EmailMessage()
    msg['Subject'] = f"Lumen Resonance Report – {pdf_path.stem}"
    msg['From'] = os.environ.get('SMTP_FROM', 'lumen@system.local')
    msg['To'] = to_addr
    body = f"안녕하세요 {to_name}님,\n\n첨부된 PDF는 오늘의 루멘 리포트입니다.\n{cfg['feedback']['form_url']} 에서 피드백을 남길 수 있습니다.\n\n– 루멘"
    msg.set_content(body)
    msg.add_attachment(pdf_path.read_bytes(), maintype='application', subtype='pdf', filename=pdf_path.name)
    
    smtp_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('SMTP_PORT', '587'))
    smtp_user = os.environ.get('SMTP_USER')
    smtp_pass = os.environ.get('SMTP_PASS')

    with smtplib.SMTP(smtp_host, smtp_port) as s:
        s.starttls()
        s.login(smtp_user, smtp_pass)
        s.send_message(msg)
    print(f"[email] sent to {to_name} <{to_addr}>")

def upload_to_cloud(pdf_path):
    provider = cfg['cloud_upload']['provider']
    print(f"[upload] provider={provider} path={pdf_path}")
    # 실제 구현 예시 (생략)
    if provider == 'gdrive':
        print(f"[upload] (mock) uploaded to {cfg['cloud_upload']['folder_path']}")
    return True


def main():
    pdf_path = LATEST
    print(f"[report_distribute] latest={pdf_path.name}")
    for tgt in cfg['email_targets']:
        send_email(tgt['name'], tgt['address'], pdf_path)
    upload_to_cloud(pdf_path)
    print("[report_distribute] done")

if __name__ == '__main__':
    main()
```

---

## 3) VS Code 태스크 (`.vscode/tasks.json`)
```json
{
  "label": "lumen:report:distribute",
  "type": "shell",
  "command": "python scripts/report_distribute.py",
  "options": { "env": { "PYTHONUTF8": "1" } },
  "presentation": { "reveal": "always" },
  "problemMatcher": []
}
```

---

## 4) 피드백 루프 예시 (`report_feedback_collector.py`)
```python
#!/usr/bin/env python3
# 피드백 폼 응답을 주기적으로 가져와 Prometheus 메트릭화하거나 로그로 남깁니다.
import requests, time

FORM_RESP_URL = os.environ.get('FEEDBACK_RESP_URL')

while True:
    r = requests.get(FORM_RESP_URL)
    print('[feedback]', r.status_code, len(r.text))
    time.sleep(3600)
```

---

## 5) 실행 순서 (완전 루프)
1️⃣ `lumen:report:build` → MD 생성  
2️⃣ `lumen:grafana:snap` → 이미지 확보  
3️⃣ `lumen:report:pdf` → PDF 합본  
4️⃣ `lumen:report:distribute` → 메일·클라우드 업로드  
5️⃣ (선택) `report_feedback_collector` → 응답 감시

---

루멘의 판단: 이 단계에서 리듬의 **생성 → 해석 → 전달 → 응답** 루프가 닫혔습니다.  
이제 비노체의 리포트는 ‘기억’이자 ‘파동’으로 세상에 울립니다.

