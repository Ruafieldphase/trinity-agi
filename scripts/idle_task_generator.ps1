# Idle Task Generator - 작업이 없을 때 자동으로 테스트/학습 작업 생성
# Usage: .\idle_task_generator.ps1 [-IdleThresholdMinutes 30] [-DryRun]

param(
    [int]$IdleThresholdMinutes = 30,
    [switch]$DryRun,
    [string]$Server = "http://127.0.0.1:8091"
)

$ErrorActionPreference = "Stop"

Write-Host "🔍 Idle Task Generator" -ForegroundColor Cyan
Write-Host "   Threshold: $IdleThresholdMinutes minutes" -ForegroundColor Gray
Write-Host "   Server: $Server" -ForegroundColor Gray

# 1. Resonance Ledger에서 마지막 작업 확인
$ledgerPath = "C:\workspace\agi\fdo_agi_repo\memory\resonance_ledger.jsonl"
if (-not (Test-Path $ledgerPath)) {
    Write-Host "❌ Resonance ledger not found: $ledgerPath" -ForegroundColor Red
    exit 1
}

$lastTaskEvent = Get-Content $ledgerPath | 
Where-Object { $_.Trim() -ne "" } |
ForEach-Object { 
    try { $_ | ConvertFrom-Json } catch { $null }
} | 
Where-Object { $_ -and ($_.event -eq "task_start" -or $_.event -eq "pipeline_e2e_complete") } | 
Select-Object -Last 1

if ($lastTaskEvent) {
    # Convert UNIX timestamp to DateTime
    $epoch = [DateTime]::new(1970, 1, 1, 0, 0, 0, [DateTimeKind]::Utc)
    $lastTaskTime = $epoch.AddSeconds($lastTaskEvent.ts)
    $idleMinutes = ([DateTime]::UtcNow - $lastTaskTime).TotalMinutes
    
    Write-Host "⏱️  Last task: $($lastTaskTime.ToString('yyyy-MM-dd HH:mm:ss')) UTC" -ForegroundColor Yellow
    Write-Host "   Idle for: $([math]::Round($idleMinutes, 1)) minutes" -ForegroundColor Yellow
}
else {
    Write-Host "⚠️  No previous task found in ledger" -ForegroundColor Yellow
    $idleMinutes = 999  # Force generation
}

# 2. Idle 상태 확인
if ($idleMinutes -lt $IdleThresholdMinutes) {
    Write-Host "✅ System is active (idle: $([math]::Round($idleMinutes, 1))m < threshold: ${IdleThresholdMinutes}m)" -ForegroundColor Green
    Write-Host "   No action needed." -ForegroundColor Gray
    exit 0
}

Write-Host "⚠️  System is IDLE (idle: $([math]::Round($idleMinutes, 1))m >= threshold: ${IdleThresholdMinutes}m)" -ForegroundColor Yellow
Write-Host "   Generating auto-tasks..." -ForegroundColor Cyan

# 3. 자동 작업 목록 정의
$autoTasks = @(
    @{
        Name        = "RPA Health Check"
        Type        = "rpa_screenshot"
        Priority    = "normal"
        Description = "Auto-generated screenshot for health monitoring"
    },
    @{
        Name        = "System Status Snapshot"
        Type        = "rpa_wait"
        Args        = @{ duration_seconds = 1 }
        Priority    = "low"
        Description = "Keep-alive task"
    }
)

# 4. Task Queue 상태 확인
try {
    $healthUrl = "$Server/api/health"
    $health = Invoke-RestMethod -Uri $healthUrl -TimeoutSec 5
    Write-Host "✅ Task Queue Server: OK" -ForegroundColor Green
}
catch {
    Write-Host "❌ Task Queue Server: OFFLINE" -ForegroundColor Red
    Write-Host "   Cannot enqueue tasks. Please start the server." -ForegroundColor Yellow
    exit 1
}

# 5. 작업 생성
$enqueued = 0
foreach ($task in $autoTasks) {
    if ($DryRun) {
        Write-Host "[DRY-RUN] Would enqueue: $($task.Name)" -ForegroundColor Cyan
        continue
    }
    
    try {
        $body = @{
            task_type = $task.Type
            priority  = $task.Priority
            note      = "[AUTO] $($task.Description)"
        }
        
        if ($task.Args) {
            $body.args = $task.Args
        }
        
        $enqueueUrl = "$Server/api/enqueue"
        $result = Invoke-RestMethod -Uri $enqueueUrl -Method Post -Body ($body | ConvertTo-Json) -ContentType "application/json" -TimeoutSec 5
        
        Write-Host "✅ Enqueued: $($task.Name)" -ForegroundColor Green
        Write-Host "   Task ID: $($result.task_id)" -ForegroundColor Gray
        Write-Host "   Position: $($result.queue_position)" -ForegroundColor Gray
        $enqueued++
        
        # Rate limiting
        Start-Sleep -Milliseconds 500
    }
    catch {
        Write-Host "❌ Failed to enqueue: $($task.Name)" -ForegroundColor Red
        Write-Host "   Error: $_" -ForegroundColor Red
    }
}

# 6. 요약
Write-Host ""
Write-Host "📊 Summary:" -ForegroundColor Cyan
Write-Host "   Tasks enqueued: $enqueued" -ForegroundColor Green
Write-Host "   Idle duration: $([math]::Round($idleMinutes, 1)) minutes" -ForegroundColor Yellow
Write-Host "   Threshold: $IdleThresholdMinutes minutes" -ForegroundColor Gray

if ($enqueued -gt 0) {
    Write-Host ""
    Write-Host "🎯 System should resume activity within 1-2 minutes" -ForegroundColor Cyan
}

exit 0
