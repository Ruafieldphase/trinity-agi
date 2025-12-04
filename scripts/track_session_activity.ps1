<#
.SYNOPSIS
세션 활동 추적 래퍼 - 명령 실행 시 자동으로 세션 메타데이터 업데이트

.DESCRIPTION
다른 스크립트를 실행하면서 자동으로 세션 통계 업데이트

.PARAMETER ScriptPath
실행할 스크립트 경로

.PARAMETER Arguments
스크립트 인자

.EXAMPLE
.\track_session_activity.ps1 -ScriptPath ".\autonomous_loop.ps1" -Arguments "-MaxIterations 2"
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$ScriptPath,
    
    [string]$Arguments = "",
    [string]$WorkspaceFolder = "C:\workspace\agi"
)

$sessionMetaPath = Join-Path $WorkspaceFolder "outputs\session_memory\current_session_meta.json"

# 세션 메타 업데이트
function Update-SessionActivity {
    param([string]$Type)
    
    if (Test-Path $sessionMetaPath) {
        $meta = Get-Content $sessionMetaPath -Raw | ConvertFrom-Json
        
        switch ($Type) {
            "command" { $meta.commands_executed++ }
            "file" { $meta.files_created++ }
        }
        
        $meta.last_activity = (Get-Date).ToString("o")
        $meta | ConvertTo-Json -Depth 5 | Set-Content $sessionMetaPath -Encoding UTF8
    }
}

# 명령 실행 전 업데이트
Update-SessionActivity -Type "command"

# 용량 체크
$checkResult = & (Join-Path $WorkspaceFolder "scripts\session_capacity_monitor.ps1") -CheckOnly
$capacity = $LASTEXITCODE

# 실제 명령 실행
Write-Host "`n▶️  Executing: $ScriptPath $Arguments`n" -ForegroundColor Cyan

if ($Arguments) {
    & $ScriptPath $Arguments
}
else {
    & $ScriptPath
}

$exitCode = $LASTEXITCODE

# 실행 후 용량 재확인
& (Join-Path $WorkspaceFolder "scripts\session_capacity_monitor.ps1") -CheckOnly | Out-Null

exit $exitCode
