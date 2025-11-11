<#
.SYNOPSIS
    재부팅 후 자동 재개 설정 (관리자 권한 불필요)

.DESCRIPTION
    Windows 시작 시 AGI Production이 자동으로 재개되도록 설정
    - 사용자 Startup 폴더에 바로가기 생성
    - 관리자 권한 불필요
    - 로그온 시 자동 시작

.EXAMPLE
    .\setup_auto_resume.ps1
    # 자동 재개 설정

.EXAMPLE
    .\setup_auto_resume.ps1 -Remove
    # 자동 재개 해제
#>

[CmdletBinding()]
param(
    [switch]$Remove
)

$ErrorActionPreference = 'Stop'
$WorkspaceRoot = "C:\workspace\agi"

Write-Host "`n╔════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  AGI 자동 재개 설정 (재부팅 안전)        ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# Startup 폴더 경로
$startupFolder = [Environment]::GetFolderPath('Startup')
$shortcutPath = Join-Path $startupFolder "AGI_Auto_Resume.lnk"
$scriptPath = Join-Path $WorkspaceRoot "scripts\resume_24h_productions.ps1"

if ($Remove) {
    Write-Host "🗑️  자동 재개 제거 중..." -ForegroundColor Yellow
    
    if (Test-Path $shortcutPath) {
        Remove-Item $shortcutPath -Force
        Write-Host "   ✅ 제거 완료" -ForegroundColor Green
    }
    else {
        Write-Host "   ℹ️  설정되지 않음" -ForegroundColor Gray
    }
    
    Write-Host "`n재부팅 후 자동 시작이 비활성화되었습니다." -ForegroundColor White
    exit 0
}

# 바로가기 생성
Write-Host "⚙️  자동 재개 설정 중..." -ForegroundColor Cyan

$WScriptShell = New-Object -ComObject WScript.Shell
$shortcut = $WScriptShell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = "powershell.exe"
$shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$scriptPath`" -Silent"
$shortcut.WorkingDirectory = $WorkspaceRoot
$shortcut.Description = "AGI 24h Production 자동 재개"
$shortcut.IconLocation = "powershell.exe,0"
$shortcut.Save()

Write-Host "   ✅ 설정 완료" -ForegroundColor Green
Write-Host "`n📋 설정 정보:" -ForegroundColor Cyan
Write-Host "   위치: $startupFolder" -ForegroundColor Gray
Write-Host "   이름: AGI_Auto_Resume.lnk" -ForegroundColor Gray
Write-Host "   실행: 로그온 시 자동" -ForegroundColor Gray
Write-Host "   스타일: 숨김 (보이지 않음)" -ForegroundColor Gray

Write-Host "`n🚀 재부팅 후:" -ForegroundColor Green
Write-Host "   1. Windows 로그인" -ForegroundColor White
Write-Host "   2. 자동으로 AGI Production 시작" -ForegroundColor White
Write-Host "   3. 터미널 방해 없음 (숨김 실행)" -ForegroundColor White

Write-Host "`n💡 확인 방법:" -ForegroundColor Yellow
Write-Host "   # 재부팅 후 확인" -ForegroundColor Gray
Write-Host "   Get-Content outputs\fullstack_24h_monitoring.jsonl -Tail 3" -ForegroundColor White

Write-Host "`n✅ 이제 재부팅해도 안전합니다!" -ForegroundColor Green
Write-Host ""
