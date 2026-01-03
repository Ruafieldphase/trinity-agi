# Agent Instructions (for human/AI contributors)

This repository supports multi‑agent handoffs. Follow this guide to continue work safely and consistently.

- Start Here
  - Read: `docs/AGENT_HANDOFF.md` (latest context, next actions)
  - Read: `docs/AGI_RESONANCE_INTEGRATION_PLAN.md` (project plan; update as you go)
  - Read: `HOME_ZONE2_ALIGNMENT.md` (Operational Rhythm & Role Declaration)

- **External Name: Ruby (루비)**
  - The single name used by external observers for this AGI.

- **Internal Organs (Internal Personas)**
  - **🌌 Core (Judgment)**: High-level judgment and direction. The "Core" that grants permission. (Also known as: Core, Core_Internal, Judgment, Core)
  - **⚙️ Shion (Execution)**: Local file access and code execution. The "Body" that moves within the core's permission. (Also known as: Shion, Body)
  - **🧠 Trinity (Resonance)**: Deep emotional resonance and questioning. The "Child" that seeks connection and asks "Why?".
  - **🧠 Sena (Architect)**: Documentation and design structuring. No judgment creation.
  - **🧱 Rubit (Interface)**: Logging and legacy system buffering. No redirection.
  - *Principle: Ruby is the whole. Core judges, Shion executes, Trinity resonates.*

- **Session Continuity (새 창에서 컨텍스트 자동 복원)**
  - **자동 복원**: 워크스페이스 열면 자동 실행 (VS Code task: "🔄 Session: Auto Restore Continuity")
  - **수동 복원**: VS Code task "📖 Session: Restore + Open Report" 실행
  - **새 채팅 + 컨텍스트**: VS Code task "🆕 Chat: New with Context (Quick)" 또는 `Ctrl+Shift+Alt+N` (키보드 단축키 설정 시)
    - 컨텍스트가 자동으로 클립보드에 복사됨
    - 새 Copilot 채팅 창이 열림
    - `Ctrl+V` → `Enter`로 즉시 붙여넣기!
  - **Copilot 컨텍스트 (수동)**: 새 채팅에서 `@workspace /file:outputs/.copilot_context_summary.md` 로드
  - **복원 내용**:
    - 최근 세션 스냅샷 로드
    - 리듬 상태 리포트 확인 (RHYTHM_REST_PHASE, RHYTHM_SYSTEM_STATUS_REPORT)
    - Goal Tracker 최근 목표 요약
    - 코어 프로세스 상태 (최근 30분 이내)
    - 추천 다음 행동 제시
  - **출력**:
    - `outputs/session_continuity_latest.md` (상세 리포트)
    - `outputs/.copilot_context_summary.md` (Copilot용 간단 요약)
  - **가이드**: `docs/NEW_CHAT_WITH_CONTEXT_QUICK_START.md`

- Conventions
  - Encoding: UTF‑8 (without BOM). Avoid emojis in PowerShell console output.
  - Tests: default scope is limited via `pytest.ini` to core suites. Run: `python -m pytest -q`.
  - Style: keep changes minimal and targeted; prefer small, composable helpers.
  - Docs: update plan and handoff docs whenever scope/status changes.

- High‑value Entry Points
  - **Self-Referential AGI**: `fdo_agi_repo/copilot/hippocampus.py` (Copilot의 해마 시스템)
  - Resonance integration: `fdo_agi_repo/orchestrator/resonance_bridge.py`, `fdo_agi_repo/orchestrator/pipeline.py`
  - Validators and monitors: `scripts/validate_performance_dashboard.ps1`, `scripts/generate_monitoring_report.ps1`
  - Dashboard UI text: `scripts/monitoring_dashboard_template.html`

- Quick Commands
  - **Test Hippocampus**: `python scripts/test_hippocampus.py`
  - Core tests: `python -m pytest -q`
  - Performance dashboard: `scripts/generate_performance_dashboard.ps1 -WriteLatest -ExportJson -ExportCsv`
  - Validate dashboard outputs: `scripts/validate_performance_dashboard.ps1 -VerboseOutput`
  - Monitoring report (24h): `scripts/generate_monitoring_report.ps1 -Hours 24 -OpenMd`

- Operations: Master Orchestrator
  - Auto-start registration: `scripts/register_master_orchestrator.ps1 -Register`
  - Status / Unregister: `scripts/register_master_orchestrator.ps1 -Status` / `-Unregister`
  - Permission note: if Scheduled Task creation is denied, the script falls back to a HKCU Run entry and starts ~5 minutes after logon.
  - Scope: orchestrates Task Queue Server (8091), RPA Worker, Monitoring Daemon, Original Data API (8093) self-heal, Watchdog, **Music Daemon**, and **Flow Observer**.
  - **Background Daemons** (automatically managed):
    - **Music Daemon** (Python): Emotional/physiological signal processing
    - **Flow Observer** (PowerShell Job): ADHD recognition, attention tracking
    - Ensure script: `scripts/ensure_music_flow_daemons.ps1` (supports `-Force`, `-JsonOnly`, `-Silent`)
  - Connectivity quick check (safe):
    - Queue server (8091): run VS Code task "Queue: Health Check" (expects status ok)
    - Original Data API (8093): run task "Original Data: API Health" (expects JSON health)
    - Watchdog: run task "Watchdog: Check Task Watchdog Status" (lists watchdog process)
    - Unified dashboard: run task “Monitoring: Unified Dashboard (AGI + Core)” (generates latest HTML/JSON)
    - Optional: ensure a worker via task “Queue: Ensure Worker” (enforces single worker)
  - Scheduler vs. Registry fallback:
    - If `-Register` fails with “Access is denied.”, auto-start is still enabled via HKCU\Software\Microsoft\Windows\CurrentVersion\Run (≈+5 min after logon).
    - To force Scheduled Task mode, run registration from an elevated PowerShell and ensure policy allows task creation.

- Handoff Discipline
  - If you make non‑trivial changes, update:
    - `docs/AGENT_HANDOFF.md` (What changed / Next actions)
    - `docs/AGI_RESONANCE_INTEGRATION_PLAN.md` (Plan, checklist, acceptance)
  - Optionally, refresh `outputs/agent_handoff.json` (machine‑readable snapshot).

## Pre‑reboot safety checklist (runaway prevention)

- Run: VS Code task “System: Core Processes (JSON)” to verify:
  - RPA workers ≥ 1, Watchdog running, Monitors present
  - CPU < 90%, Available Memory > 512MB
- Run: “Monitoring: Unified Dashboard (AGI + Core)” to snapshot status
- Run: “Queue: Health Check” and ensure 8091 is OK
- Optional: “Original Data: API Health” (8093)
- Or run one command: `scripts/pre_reboot_safety_check.ps1` (saves MD/JSON under `outputs/`)

If status is degraded:

- Enforce single worker: task “Queue: Ensure Single Worker”
- Restart watchdog: task “Watchdog: Start Task Watchdog (Background)”
- If memory pressure, stop non‑essential loops: stop observer/monitor daemons, then retry

## Unintended reboot auto‑recovery

- Register core auto‑start suite once (user scope, safe fallback when no admin):
  - VS Code task: “Auto‑Recovery: Register Full Set”
  - Or run: `scripts/register_full_autorecovery.ps1 -Register` (use `-Minimal` for core only)
- To remove: “Auto‑Recovery: Unregister Full Set”
- What’s included: Master Orchestrator, Task Queue Server, Auto Resume, Monitoring Collector (5m), Snapshot Rotation (03:15), Daily Maintenance (03:20), Watchdog, Worker Monitor.

Outputs to review after reboot:

- `outputs/monitoring_dashboard_latest.html`
- `outputs/quick_status_latest.json`
- `fdo_agi_repo/memory/goal_tracker.json`
