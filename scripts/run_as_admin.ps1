<#
.SYNOPSIS
    관리자 권한으로 스크립트 실행
.DESCRIPTION
    현재 세션이 관리자가 아니면 관리자 권한으로 재시작합니다.
.EXAMPLE
    .\scripts\run_as_admin.ps1 .\scripts\cleanup_old_tasks_admin.ps1 -Force
#>

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$ScriptPath,
    
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Arguments
)

# 관리자 권한 확인
$isAdmin = ([Security.Principal.WindowsPrincipal] `
        [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(`
        [Security.Principal.WindowsBuiltInRole]::Administrator)

if ($isAdmin) {
    Write-Host "✓ Already running as Administrator" -ForegroundColor Green
    & $ScriptPath @Arguments
}
else {
    Write-Host "⚠ Elevating to Administrator..." -ForegroundColor Yellow
    
    # 절대 경로로 변환
    $scriptFullPath = Resolve-Path $ScriptPath
    
    # 인수 문자열 생성
    $argString = if ($Arguments) {
        $Arguments -join ' '
    }
    else {
        ''
    }
    
    # 관리자 권한으로 재시작
    Start-Process powershell -Verb RunAs -ArgumentList @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", "`"$scriptFullPath`"",
        $argString
    ) -Wait
}