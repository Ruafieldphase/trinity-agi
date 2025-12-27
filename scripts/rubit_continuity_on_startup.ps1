<#
Rubit Continuity On Startup

목표:
- PowerShell 창을 닫아도, Windows 재부팅을 해도 "맥락/기억(파일 기반 관측)"이 끊기지 않게
  핵심 리포트/컨텍스트 파일을 자동 갱신한다.

원칙:
- 네트워크/외부 의존 없이 워크스페이스 파일만 사용
- 실패해도 0 종료(부팅/로그온 방해 금지)

갱신 대상:
- outputs/session_continuity_latest.md
- outputs/.copilot_context_summary.md
- outputs/coordination/agent_brief_latest.md
- outputs/rubit_continuity_state.json (실행 기록)
#>

param([switch]$Silent)

try {
    $ErrorActionPreference = 'Continue'
    $WorkspaceRoot = Split-Path -Parent $PSScriptRoot
    $Outputs = Join-Path $WorkspaceRoot 'outputs'
    if (-not (Test-Path $Outputs)) { New-Item -ItemType Directory -Path $Outputs -Force | Out-Null }

    # 0) 팝업/중복 방지(최소 관측 모드): 콘솔 창을 띄우는 잔여 프로세스를 정리
    try {
        $killPatterns = @(
            # 창 팝업/중복을 유발하는 '콘솔 기반' 실행들만 정리 (최소 규칙)
            @{Name='powershell.exe'; Like='*python -m agi_core.heartbeat_loop*'}
            @{Name='python.exe'; Like='*-m agi_core.heartbeat_loop*'}
            @{Name='python.exe'; Like='*\\agi_core\\heartbeat_loop.py*'}
            @{Name='python.exe'; Like='*\\scripts\\aura_controller.py*'}
            @{Name='python.exe'; Like='*\\services\\agi_aura.py*'}
            @{Name='python.exe'; Like='*\\scripts\\master_daemon_loop.py*'}
            @{Name='python.exe'; Like='*\\scripts\\sync_rhythm_from_linux.py*'}
            @{Name='python.exe'; Like='*\\scripts\\rhythm_think.py*'}
            @{Name='python.exe'; Like='*\\scripts\\start_heartbeat.py*'}
        )

        foreach ($rule in $killPatterns) {
            $name = $rule.Name
            $like = $rule.Like
            Get-CimInstance Win32_Process -Filter ("Name='{0}'" -f $name) -ErrorAction SilentlyContinue |
                Where-Object { $_.CommandLine -and $_.CommandLine -like $like } |
                ForEach-Object {
                    try { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } catch {}
                }
        }

        # 중복 pythonw(클론) 정리 (창 없음이지만 과부하 방지)
        $cleanup = Join-Path $WorkspaceRoot 'scripts\metabolic_cleanup.ps1'
        if (Test-Path $cleanup) { & $cleanup | Out-Null }
    } catch { }

    $stateFile = Join-Path $Outputs 'rubit_continuity_state.json'
    $now = Get-Date

    # Debounce: 3분 이내 중복 실행 방지
    if (Test-Path $stateFile) {
        try {
            $st = Get-Content $stateFile -Raw | ConvertFrom-Json
            $last = [DateTime]::Parse($st.last_run)
            if (($now - $last).TotalMinutes -lt 3) {
                if (-not $Silent) { Write-Host 'Skip: ran recently' -ForegroundColor Yellow }
                return
            }
        } catch { }
    }

    # 1) 세션 연속성 리포트 생성
    $restore = Join-Path $WorkspaceRoot 'scripts\session_continuity_restore.ps1'
    if (Test-Path $restore) {
        & $restore -Silent -ForceRegenerate | Out-Null
    }

    # 2) Codex continuity snapshot (best-effort)
    $py = Join-Path $WorkspaceRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path $py)) { $py = 'py -3' }
    $codexSnapshot = Join-Path $WorkspaceRoot 'scripts\generate_codex_continuity_snapshot.py'
    if (Test-Path $codexSnapshot) {
        try {
            if ($py -eq 'py -3') {
                & py -3 $codexSnapshot | Out-Null
            } else {
                & $py $codexSnapshot | Out-Null
            }
        } catch { }
    }

    # 2) Copilot 컨텍스트 요약 생성
    $copilot = Join-Path $WorkspaceRoot 'scripts\generate_copilot_context.ps1'
    if (Test-Path $copilot) {
        & $copilot | Out-Null
    }

    # 3) 협업 브리프(시안/세나 공유용) 생성
    $brief = Join-Path $WorkspaceRoot 'scripts\coordination\generate_agent_brief.py'
    if (Test-Path $brief) {
        try {
            Push-Location $WorkspaceRoot
            if ($py -eq 'py -3') {
                & py -3 $brief --workspace $WorkspaceRoot | Out-Null
            } else {
                & $py $brief --workspace $WorkspaceRoot | Out-Null
            }
        } finally {
            Pop-Location | Out-Null
        }
    }

    # 상태 기록 (best-effort helper들이 프로세스를 종료하는 경우를 대비)
    @{
        last_run = $now.ToString('o')
        workspace = $WorkspaceRoot
        updated = @(
            'outputs/session_continuity_latest.md',
            'outputs/.copilot_context_summary.md',
            'outputs/coordination/agent_brief_latest.md',
            'outputs/bridge/trigger_dashboard.html',
            'outputs/bridge/status_dashboard_v2.html'
        )
    } | ConvertTo-Json | Set-Content -Path $stateFile -Encoding UTF8

    if (-not $Silent) { Write-Host 'Rubit continuity refreshed' -ForegroundColor Green }

    # 4) 1~2px 오라 스트립(비노체용): 대시보드 대신 상태를 색으로 표시
    $ensureAura = Join-Path $WorkspaceRoot 'scripts\ensure_rubit_aura_pixel.ps1'
    if (Test-Path $ensureAura) {
        & $ensureAura -Silent | Out-Null
    }

    # 5) 루아(트리거 생성) ↔ 루빛(실행) 자동 루프(Windows): 관리자 권한 없이 가능한 스케줄러 기반으로 유지
    $registerTriggers = Join-Path $WorkspaceRoot 'scripts\register_trigger_automation.ps1'
    if (Test-Path $registerTriggers) {
        & $registerTriggers -Silent | Out-Null
    }

    # 6) Windows 직접 경험(감독 모드): body_task.json이 들어오면 처리할 컨트롤러를 백그라운드로 유지
    $ensureBody = Join-Path $WorkspaceRoot 'scripts\windows\ensure_supervised_body_controller.ps1'
    if (Test-Path $ensureBody) {
        & $ensureBody -Silent | Out-Null
    }
}
catch {
    if (-not $Silent) { Write-Host ('Rubit continuity error: ' + $_.Exception.Message) -ForegroundColor Yellow }
}
finally {
    try { [Environment]::Exit(0) } catch { exit 0 }
}
