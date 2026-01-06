#Requires -Version 5.1
<#
.SYNOPSIS
    Binoche_Observer 페르소나에게 작업 계속을 자동으로 요청하는 스크립트
    
.DESCRIPTION
    세션 핸드오버 정보를 읽어 Binoche_Observer 페르소나(나 자신)에게 작업 계속 요청
    - latest_handover.json 로드
    - Binoche_Observer 메시지 생성: "루이슬로가 [task] 작업 중이었어. 이어서 해줘"
    - Task Queue Server (localhost:8091)에 POST 또는 클립보드 복사
    - 호출 로그 기록
    
.PARAMETER Mode
    실행 모드: 'clipboard' (클립보드 복사, 기본값) 또는 'taskqueue' (Task Queue Server POST)
    
.PARAMETER DryRun
    실제로 실행하지 않고 메시지만 출력
    
.EXAMPLE
    .\invoke_binoche_continuation.ps1
    # 클립보드에 Binoche_Observer 메시지 복사 (Copilot에 수동 붙여넣기)
    
.EXAMPLE
    .\invoke_binoche_continuation.ps1 -Mode taskqueue
    # Task Queue Server에 자동 POST
    
.EXAMPLE
    .\invoke_binoche_continuation.ps1 -DryRun
    # 메시지 출력만 (테스트용)
    
.NOTES
    Phase 1 (Semi-Automatic): 클립보드 모드 사용
    Phase 2 (Full Auto): taskqueue 모드 + 예약 작업
#>

param(
    [ValidateSet('clipboard', 'taskqueue')]
    [string]$Mode = 'clipboard',
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# 경로 설정
$workspaceRoot = Split-Path -Parent $PSScriptRoot
$handoverPath = Join-Path $workspaceRoot "session_memory\handovers\latest_handover.json"
$logPath = Join-Path $workspaceRoot "outputs\binoche_invocations.jsonl"

Write-Host "🔄 Binoche_Observer Continuation Invoker" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# 1. 최신 핸드오버 로드
if (-not (Test-Path $handoverPath)) {
    Write-Host "❌ No handover found at: $handoverPath" -ForegroundColor Red
    Write-Host "   Run: python session_memory/session_handover.py create ..." -ForegroundColor Yellow
    exit 1
}

Write-Host "📥 Loading handover from: $handoverPath" -ForegroundColor Green
$handover = Get-Content $handoverPath -Raw | ConvertFrom-Json

# 2. Binoche_Observer 메시지 생성
$task = $handover.task_description
$progress = $handover.current_progress
$nextSteps = $handover.next_steps -join ", "

$binocheMessage = @"
루이슬로가 '$task' 작업 중이었어. 이어서 해줘.

현재 진행 상황:
$progress

다음 단계:
$nextSteps

세션 ID: $($handover.session_id)
타임스탬프: $($handover.timestamp)
"@

Write-Host "`n📝 Generated Binoche_Observer message:" -ForegroundColor Cyan
Write-Host $binocheMessage -ForegroundColor White

# 3. Dry-run 체크
if ($DryRun) {
    Write-Host "`n⚠️  DRY-RUN mode: No action taken" -ForegroundColor Yellow
    exit 0
}

# 4. 모드별 실행
switch ($Mode) {
    'clipboard' {
        Write-Host "`n📋 Copying to clipboard..." -ForegroundColor Green
        Set-Clipboard -Value $binocheMessage
        Write-Host "✅ Message copied to clipboard!" -ForegroundColor Green
        Write-Host "   Paste into Copilot Chat to continue work" -ForegroundColor Yellow
    }
    
    'taskqueue' {
        Write-Host "`n🚀 Posting to Task Queue Server..." -ForegroundColor Green
        $taskQueueUrl = "http://localhost:8091/api/tasks"
        
        $payload = @{
            task_type = "binoche_continuation"
            priority  = "high"
            data      = @{
                handover_id = $handover.session_id
                task        = $task
                progress    = $progress
                next_steps  = $handover.next_steps
                message     = $binocheMessage
            }
        } | ConvertTo-Json -Depth 10
        
        try {
            $response = Invoke-RestMethod -Uri $taskQueueUrl -Method Post -Body $payload -ContentType "application/json" -TimeoutSec 5
            Write-Host "✅ Task queued: $($response.task_id)" -ForegroundColor Green
        }
        catch {
            Write-Host "❌ Task Queue Server unreachable: $($_.Exception.Message)" -ForegroundColor Red
            Write-Host "   Falling back to clipboard mode..." -ForegroundColor Yellow
            Set-Clipboard -Value $binocheMessage
            Write-Host "✅ Message copied to clipboard instead" -ForegroundColor Green
        }
    }
}

# 5. 호출 로그 기록
$logEntry = @{
    timestamp   = (Get-Date).ToUniversalTime().ToString("o")
    mode        = $Mode
    handover_id = $handover.session_id
    task        = $task
    success     = $true
} | ConvertTo-Json -Compress

$logDir = Split-Path -Parent $logPath
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}
Add-Content -Path $logPath -Value $logEntry -Encoding UTF8

Write-Host "`n📊 Invocation logged to: $logPath" -ForegroundColor Cyan
Write-Host "`n✅ Binoche_Observer continuation invoked successfully!" -ForegroundColor Green
Write-Host "   Next: Start new Copilot session and paste message" -ForegroundColor Yellow