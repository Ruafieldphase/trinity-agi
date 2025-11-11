# auto_task_generator.ps1
# Phase 8: 자동 Task 생성기 (Normal Baseline 수집용)
param(
    [int]$IntervalMinutes = 5,
    [int]$DurationHours = 6,
    [string]$Server = "http://127.0.0.1:8091",
    [switch]$Once
)

$ErrorActionPreference = "Stop"
$start = Get-Date

function Enqueue-SimpleTask {
    param([string]$TaskType)
    
    $payload = @{
        action = $TaskType
        params = @{
            timestamp = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
        }
    } | ConvertTo-Json -Depth 5
    
    try {
        $response = Invoke-RestMethod -Uri "$Server/api/enqueue" `
            -Method POST `
            -Body $payload `
            -ContentType "application/json" `
            -TimeoutSec 5
        
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ✅ Task enqueued: $TaskType (ID: $($response.task_id))" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ❌ Failed to enqueue $TaskType : $_" -ForegroundColor Red
        return $false
    }
}

function Run-TaskGenerator {
    $taskTypes = @("screenshot", "health_check", "quick_status")
    $taskIndex = 0
    $successCount = 0
    $failCount = 0
    
    Write-Host "`n🚀 Auto Task Generator 시작" -ForegroundColor Cyan
    Write-Host "  Server: $Server" -ForegroundColor Gray
    Write-Host "  Interval: $IntervalMinutes 분" -ForegroundColor Gray
    Write-Host "  Duration: $DurationHours 시간" -ForegroundColor Gray
    Write-Host "  End Time: $($start.AddHours($DurationHours).ToString('yyyy-MM-dd HH:mm'))" -ForegroundColor Gray
    Write-Host ""
    
    while ($true) {
        $elapsed = ((Get-Date) - $start).TotalHours
        
        if ($elapsed -ge $DurationHours) {
            Write-Host "`n⏰ Duration reached ($DurationHours hours)" -ForegroundColor Yellow
            break
        }
        
        # Task 생성
        $taskType = $taskTypes[$taskIndex % $taskTypes.Length]
        $result = Enqueue-SimpleTask -TaskType $taskType
        
        if ($result) {
            $successCount++
        }
        else {
            $failCount++
        }
        
        $taskIndex++
        
        # 통계 출력
        $remaining = $DurationHours - $elapsed
        Write-Host "  Generated: $taskIndex | Success: $successCount | Failed: $failCount | Remaining: $([math]::Round($remaining, 1))h" -ForegroundColor Cyan
        
        if ($Once) {
            Write-Host "`n✅ Once mode: Exiting after 1 task" -ForegroundColor Green
            break
        }
        
        # 대기
        Start-Sleep -Seconds ($IntervalMinutes * 60)
    }
    
    Write-Host "`n📊 Final Statistics:" -ForegroundColor Cyan
    Write-Host "  Total Generated: $taskIndex" -ForegroundColor White
    Write-Host "  Successful: $successCount" -ForegroundColor Green
    Write-Host "  Failed: $failCount" -ForegroundColor Red
    Write-Host "  Duration: $([math]::Round($elapsed, 1)) hours" -ForegroundColor White
}

# Health Check
try {
    $health = Invoke-RestMethod -Uri "$Server/api/health" -TimeoutSec 2
    Write-Host "✅ Task Queue Server is online" -ForegroundColor Green
}
catch {
    Write-Host "❌ Task Queue Server is offline at $Server" -ForegroundColor Red
    Write-Host "   Start it with: Queue: Ensure Server (8091)" -ForegroundColor Yellow
    exit 1
}

# Run
Run-TaskGenerator
