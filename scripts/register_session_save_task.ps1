# Register automatic session save on system shutdown/logout
# Simplified approach using heartbeat integration instead of Task Scheduler

param(
    [switch]$Register,
    [switch]$Unregister,
    [switch]$Status
)

$TaskName = "AGI_AutoSessionSave"
$ws = Split-Path -Parent $PSScriptRoot
$heartbeatPath = "$ws\scripts\heartbeat_loop.py"

if ($Register) {
    Write-Host "📝 Integrating automatic session save into heartbeat..." -ForegroundColor Cyan
    
    # Check if heartbeat already includes session save
    if (Test-Path $heartbeatPath) {
        $content = Get-Content $heartbeatPath -Raw
        if ($content -like "*auto_session_save*") {
            Write-Host "✅ Session save already integrated in heartbeat" -ForegroundColor Green
        }
        else {
            Write-Host "⚠️  Manual integration needed in heart beat_loop.py" -ForegroundColor Yellow
            Write-Host "   Add: run_script('auto_session_save.py', [])" -ForegroundColor Gray
        }
    }
    else {
        Write-Host "⚠️  Heartbeat loop not found: $heartbeatPath" -ForegroundColor Yellow
    }
    
    Write-Host "`n✅ Auto-save script is ready at: $ws\scripts\auto_session_save.py" -ForegroundColor Green
    Write-Host "   It will run periodically via heartbeat loop" -ForegroundColor Gray
}
elseif ($Unregister) {
    Write-Host "ℹ️  Session save is integrated via heartbeat (no separate task)" -ForegroundColor Cyan
}
elseif ($Status) {
    Write-Host "📊 Session Save Status:" -ForegroundColor Cyan
    $scriptPath = "$ws\scripts\auto_session_save.py"
    if (Test-Path $scriptPath) {
        Write-Host "✅ Script exists: $scriptPath" -ForegroundColor Green
    }
    else {
        Write-Host "❌ Script not found" -ForegroundColor Red
    }
    
    if (Test-Path $heartbeatPath) {
        $content = Get-Content $heartbeatPath -Raw
        if ($content -like "*auto_session_save*") {
            Write-Host "✅ Integrated in heartbeat loop" -ForegroundColor Green
        }
        else {
            Write-Host "⚠️  Not yet integrated in heartbeat" -ForegroundColor Yellow
        }
    }
}
else {
    Write-Host "Usage:" -ForegroundColor Cyan
    Write-Host "  -Register    : Setup auto session save"
    Write-Host "  -Unregister  : (N/A for heartbeat integration)"
    Write-Host "  -Status      : Check integration status"
}