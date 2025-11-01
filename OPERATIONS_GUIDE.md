# Operations Guide (Phase 5)

Last Updated: 2025-10-31  
Version: Phase 5 Complete

---

Note: For a concise, ASCII-safe checklist, see scripts/OPERATIONS_QUICK_GUIDE.md

## Quick Start

### All-in-one startup

```powershell
# Start all Phase 5 services
.\scripts\start_phase5_system.ps1

# Verify endpoints
# Task Queue Server: http://127.0.0.1:8091
# Web Dashboard:      http://127.0.0.1:8000
```

### Start components individually

```powershell
# 1) Task Queue Server
cd LLM_Unified\ion-mentoring
.\.venv\Scripts\python.exe task_queue_server.py --port 8091

# 2) Web Dashboard
cd fdo_agi_repo
python monitoring\web_server.py

# 3) RPA Worker
cd fdo_agi_repo
.venv\Scripts\python.exe integrations\rpa_worker.py --server http://127.0.0.1:8091
```

## Health Checks

```powershell
# Service health
curl http://127.0.0.1:8091/api/health
curl http://127.0.0.1:8000/api/health

# Quick system status
.\scripts\quick_status.ps1

# Ports in use
netstat -ano | findstr ":8091"
netstat -ano | findstr ":8000"
```

## PowerShell Jobs

```powershell
Get-Job | Format-Table Id, Name, State
Receive-Job -Id 1 -Keep
Stop-Job -Id 1
Remove-Job -Id 1
```

---

The following sections may contain legacy content with encoding artifacts. They remain for reference and will be cleaned up incrementally.

## Autostart (ASCII)

- Register Phase 5 services to start on login:
  - scripts/register_phase5_autostart.ps1 -Install

- Optional: schedule a daily briefing artifact (runs at user logon):
  - scripts/register_daily_briefing.ps1 -Install

Notes:
- Uses Windows Task Scheduler; run PowerShell as Administrator for install.
- To remove: run the same scripts with -Uninstall.

```powershell
# ?ㅽ뻾 以묒씤 Job ?뺤씤
Get-Job | Format-Table Id, Name, State

# Job 濡쒓렇 ?뺤씤
Receive-Job -Id 1 -Keep

# Job 醫낅즺
Stop-Job -Id 1
Remove-Job -Id 1
```

---

## ?뵩 ?쇱긽 ?댁쁺

### YouTube ?숈뒿 ?ㅽ뻾

```powershell
# ?섎룞 ?ㅽ뻾
.\scripts\run_youtube_learner.ps1 -Url "https://youtube.com/watch?v=..." -MaxFrames 3

# 寃곌낵 ?뺤씤
.\scripts\youtube_learner_index.ps1 -Open
```

### RPA ?묒뾽 ?ㅽ뻾

```powershell
# ?ㅻえ???뚯뒪??
.\scripts\run_smoke_e2e_ocr.ps1

# 寃곌낵 ?뺤씤
Invoke-RestMethod -Uri 'http://127.0.0.1:8091/api/results' | ConvertTo-Json
```

### 紐⑤땲?곕쭅 由ы룷???앹꽦

```powershell
# 24?쒓컙 由ы룷??
.\scripts\generate_monitoring_report.ps1 -Hours 24

# 7??由ы룷??
.\scripts\generate_monitoring_report.ps1 -Hours 168

# 寃곌낵 ?닿린
code .\outputs\monitoring_report_latest.md
```

---

## ?뵇 ?몃윭釉붿뒋??

### ?쒕쾭媛 ?쒖옉?섏? ?딅뒗 寃쎌슦

**利앹긽**: `curl` 紐낅졊???ㅽ뙣?섍굅???곌껐 嫄곕?

**?닿껐 諛⑸쾿**:

```powershell
# 1. ?ы듃媛 ?대? ?ъ슜 以묒씤吏 ?뺤씤
netstat -ano | findstr ":8091"
netstat -ano | findstr ":8000"

# 2. ?꾨줈?몄뒪 醫낅즺 (PID????紐낅졊 寃곌낵?먯꽌 ?뺤씤)
taskkill /PID <PID> /F

# 3. ?ъ떆??
.\scripts\start_phase5_system.ps1
```

### Web Dashboard媛 ?곗씠?곕? ?쒖떆?섏? ?딅뒗 寃쎌슦

**利앹긽**: 李⑦듃??硫뷀듃由?씠 "--" ?먮뒗 鍮꾩뼱?덉쓬

**?닿껐 諛⑸쾿**:

```powershell
# 1. 硫뷀듃由??뚯씪 議댁옱 ?뺤씤
Test-Path .\fdo_agi_repo\outputs\monitoring_metrics.jsonl

# 2. ?뚯씪???놁쑝硫??앹꽦
New-Item -ItemType File -Path .\fdo_agi_repo\outputs\monitoring_metrics.jsonl -Force

# 3. ?뚯뒪???곗씠???앹꽦
.\scripts\test_monitoring_success_path.ps1 -TaskCount 5 -Duration 0.3
```

### Job???묐떟?섏? ?딅뒗 寃쎌슦

**利앹긽**: `Get-Job`?먯꽌 Running ?곹깭吏留??묐룞?섏? ?딆쓬

**?닿껐 諛⑸쾿**:

```powershell
# 1. Job 媛뺤젣 醫낅즺
Get-Job | Stop-Job
Get-Job | Remove-Job

# 2. ?꾨줈?몄뒪 吏곸젒 醫낅즺
Get-Process python* | Stop-Process -Force

# 3. ?ъ떆??
.\scripts\start_phase5_system.ps1
```

### Python ?섏〈???먮윭

**利앹긽**: `ModuleNotFoundError: No module named 'fastapi'`

**?닿껐 諛⑸쾿**:

```powershell
# 1. 媛?곹솚寃??쒖꽦???뺤씤
cd fdo_agi_repo
.\.venv\Scripts\Activate.ps1

# 2. 以묐났 ?먮━ 移댄뀒怨좊━ ?앹꽦
python -m pip install -U pip
pip install -r requirements.txt
pip install -r requirements_rpa.txt
```

---

## ?뮶 諛깆뾽 諛?蹂듦뎄

### 以묒슂 ?뚯씪 諛깆뾽

```powershell
# 諛깆뾽 ?붾젆?좊━ ?앹꽦
$backupDir = ".\backups\$(Get-Date -Format 'yyyy-MM-dd_HHmmss')"
New-Item -ItemType Directory -Path $backupDir -Force

# 1. 硫붾え由??뚯씪
Copy-Item .\fdo_agi_repo\memory\* -Destination $backupDir\memory -Recurse

# 2. 異쒕젰 ?뚯씪
Copy-Item .\fdo_agi_repo\outputs\* -Destination $backupDir\outputs -Recurse

# 3. ?ㅼ젙 ?뚯씪
Copy-Item .\configs\* -Destination $backupDir\configs -Recurse
```

### 蹂듦뎄

```powershell
# 諛깆뾽?먯꽌 蹂듦뎄
$backupDir = ".\backups\2025-10-31_205500"  # 諛깆뾽 ?붾젆?좊━

Copy-Item $backupDir\memory\* -Destination .\fdo_agi_repo\memory\ -Force -Recurse
Copy-Item $backupDir\outputs\* -Destination .\fdo_agi_repo\outputs\ -Force -Recurse
Copy-Item $backupDir\configs\* -Destination .\configs\ -Force -Recurse
```

---

## ?뱤 紐⑤땲?곕쭅 硫뷀듃由?

### 二쇱슂 吏??

| 硫뷀듃由?| ?뺤긽 踰붿쐞 | 寃쎄퀬 ?꾧퀎媛?|
|--------|----------|-----------|
| ?깃났瑜?| > 90% | < 80% |
| ?됯퇏 ?묐떟 ?쒓컙 | < 5珥?| > 10珥?|
| ???ш린 | < 10 | > 50 |
| ?뚯빱 ??| ??1 | = 0 |

### 硫뷀듃由??뚯씪 ?꾩튂

```
fdo_agi_repo/outputs/
?쒋?? monitoring_metrics.jsonl       # ?먯떆 硫뷀듃由??곗씠??
?쒋?? monitoring_events.jsonl        # ?대깽??濡쒓렇
?쒋?? monitoring_report_latest.md    # 由ы룷??(Markdown)
?쒋?? monitoring_metrics_latest.json # 由ы룷??(JSON)
?붴?? monitoring_dashboard_latest.html # ??쒕낫??(HTML)
```

---

## ?뵍 蹂댁븞 怨좊젮?ы빆

### 湲곕낯 ?ㅼ젙 (媛쒕컻 ?섍꼍)

?꾩옱 ?쒖뒪?쒖? **localhost?먯꽌留??묎렐 媛??*?⑸땲??

- Task Queue Server: `127.0.0.1:8091`
- Web Dashboard: `127.0.0.1:8000`

### ?꾨줈?뺤뀡 諛고룷 ??異붽? ?꾩슂

```powershell
# 1. HTTPS ?ㅼ젙
# 2. ?몄쬆/?멸? (JWT, OAuth)
# 3. CORS ?뺤콉 媛뺥솕
# 4. Rate Limiting
# 5. 濡쒓렇 ?뷀샇??
```

---

## ?뱸 吏??諛?臾몄쓽

### 臾몄꽌

- [Phase 5 ?꾨즺 ?붿빟](PHASE_5_FINAL_SUMMARY.md)
- [Phase 5 ?꾨즺 由ы룷??(PHASE_5_COMPLETION_REPORT.md)
- [?꾨줈?앺듃 README](README.md)

### 鍮좊Ⅸ 李몄“

```powershell
# ?쒖뒪???쒖옉
.\scripts\start_phase5_system.ps1

# ?곹깭 ?뺤씤
.\scripts\quick_status.ps1

# 由ы룷???앹꽦
.\scripts\generate_monitoring_report.ps1 -Hours 24

# 釉뚮씪?곗? ?묒냽
Start-Process http://127.0.0.1:8000
```

---

## ??泥댄겕由ъ뒪??

### 留ㅼ씪

- [ ] Web Dashboard ?묒냽 ?뺤씤 (<http://127.0.0.1:8000>)
- [ ] ?깃났瑜?> 90% ?뺤씤
- [ ] ?뚯빱 ?곹깭 ?뺤씤

### 留ㅼ＜

- [ ] 7??紐⑤땲?곕쭅 由ы룷???앹꽦
- [ ] 硫붾え由??뚯씪 諛깆뾽
- [ ] ?ㅻ옒??濡쒓렇 ?뺣━ (14???댁긽)

### 留ㅼ썡

- [ ] ?꾩껜 ?쒖뒪??諛깆뾽
- [ ] ?깅뒫 硫뷀듃由?遺꾩꽍
- [ ] ?섏〈???낅뜲?댄듃 寃??

---

**?묒꽦**: GitHub Copilot  
**理쒖쥌 ?낅뜲?댄듃**: 2025-10-31  
**踰꾩쟾**: Phase 5 ?꾨즺

