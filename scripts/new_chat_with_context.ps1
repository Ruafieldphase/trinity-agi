#Requires -Version 5.1
<#
.SYNOPSIS
    새 Copilot 채팅을 열고 컨텍스트를 클립보드에 복사합니다.

.DESCRIPTION
    1. 세션 컨텍스트 요약을 클립보드에 복사
    2. 새 Copilot 채팅 창 열기
    3. 사용자에게 Ctrl+V로 붙여넣기 안내

.PARAMETER ContextFile
    컨텍스트 파일 경로 (기본: .copilot_context_summary.md)

.PARAMETER NoClipboard
    클립보드 복사 건너뛰기

.PARAMETER AutoPaste
    자동으로 붙여넣기 + 전송 (게임 봇처럼!)

.EXAMPLE
    .\new_chat_with_context.ps1
    # 기본 동작: 컨텍스트 복사 + 새 채팅 열기

.EXAMPLE
    .\new_chat_with_context.ps1 -AutoPaste
    # 완전 자동: 복사 + 열기 + 붙여넣기 + 전송!

.EXAMPLE
    .\new_chat_with_context.ps1 -ContextFile "outputs\session_continuity_latest.md"
    # 상세 리포트로 새 채팅 시작
#>

[CmdletBinding()]
param(
    [Parameter()]
    [string]$ContextFile = "outputs\.copilot_context_summary.md",
    
    [Parameter()]
    [switch]$NoClipboard,
    
    [Parameter()]
    [switch]$AutoPaste
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = 'Stop'
$WorkspaceRoot = Split-Path -Parent $PSScriptRoot

try {
    Write-Host "🚀 새 Copilot 채팅 준비 중..." -ForegroundColor Cyan
    Write-Host ""

    # 1. 컨텍스트 파일 확인
    $contextPath = Join-Path $WorkspaceRoot $ContextFile
    if (-not (Test-Path -LiteralPath $contextPath)) {
        Write-Host "❌ 컨텍스트 파일 없음: $ContextFile" -ForegroundColor Red
        Write-Host "   세션 복원을 먼저 실행하세요:" -ForegroundColor Yellow
        Write-Host "   .\scripts\session_continuity_restore.ps1" -ForegroundColor White
        exit 1
    }

    # 2. 클립보드에 복사
    if (-not $NoClipboard) {
        $contextContent = Get-Content -LiteralPath $contextPath -Raw -Encoding UTF8
        Set-Clipboard -Value $contextContent
        
        Write-Host "✅ 컨텍스트 복사 완료" -ForegroundColor Green
        Write-Host "   파일: $ContextFile" -ForegroundColor Gray
        Write-Host "   크기: $($contextContent.Length) 문자" -ForegroundColor Gray
        Write-Host ""
    }

    # 3. 새 채팅 열기 시도
    Write-Host "📝 새 Copilot 채팅 열기..." -ForegroundColor Cyan
    
    # VS Code 명령어 실행 (여러 방법 시도)
    $chatCommands = @(
        "workbench.panel.chat.view.copilot.focus",  # Copilot Chat 패널
        "workbench.action.chat.open",               # 일반 채팅 열기
        "github.copilot.chat.open"                  # GitHub Copilot Chat
    )
    
    $opened = $false
    foreach ($cmd in $chatCommands) {
        try {
            & code --command $cmd 2>$null
            if ($LASTEXITCODE -eq 0) {
                $opened = $true
                Write-Host "✅ 채팅 창 열기 성공" -ForegroundColor Green
                break
            }
        }
        catch {
            # 다음 명령어 시도
            continue
        }
    }
    
    if (-not $opened) {
        Write-Host "⚠️ 자동으로 채팅 창을 열 수 없습니다" -ForegroundColor Yellow
        Write-Host "   수동으로 Copilot 채팅을 열어주세요:" -ForegroundColor White
        Write-Host "   - Ctrl+Shift+I (Copilot Chat)" -ForegroundColor Cyan
        Write-Host "   - View > Command Palette > 'Chat: Focus on Chat View'" -ForegroundColor Cyan
    }
    
    # 4. 자동 붙여넣기 (선택적)
    if ($AutoPaste -and $opened) {
        Write-Host ""
        Write-Host "🤖 자동 붙여넣기 시작..." -ForegroundColor Magenta
        
        try {
            # WScript.Shell로 키 입력 자동화
            $wshell = New-Object -ComObject wscript.shell
            
            # 채팅 창이 활성화될 때까지 대기
            Start-Sleep -Milliseconds 800
            
            # Ctrl+V (붙여넣기)
            Write-Host "   → Ctrl+V (붙여넣기)" -ForegroundColor Gray
            $wshell.SendKeys("^v")
            Start-Sleep -Milliseconds 300
            
            # Enter (전송)
            Write-Host "   → Enter (전송)" -ForegroundColor Gray
            $wshell.SendKeys("{ENTER}")
            
            Write-Host "✅ 자동 붙여넣기 완료!" -ForegroundColor Green
            Write-Host ""
            Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
            Write-Host "🎉 완전 자동 완료!" -ForegroundColor Green
            Write-Host "   새 채팅창에서 컨텍스트가 로드되고 있습니다..." -ForegroundColor White
            Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
            
            exit 0
        }
        catch {
            Write-Host "⚠️ 자동 붙여넣기 실패: $($_.Exception.Message)" -ForegroundColor Yellow
            Write-Host "   수동으로 Ctrl+V + Enter 해주세요" -ForegroundColor White
        }
    }
    
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    Write-Host "💡 다음 단계:" -ForegroundColor Yellow
    Write-Host "   1. Copilot 채팅 창에서" -ForegroundColor White
    Write-Host "   2. Ctrl+V로 컨텍스트 붙여넣기" -ForegroundColor Cyan
    Write-Host "   3. Enter 키로 전송" -ForegroundColor White
    Write-Host ""
    Write-Host "또는 간단하게:" -ForegroundColor Yellow
    Write-Host "   '복원' 또는 '컨텍스트' 입력" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    
    exit 0

}
catch {
    Write-Host "❌ 오류 발생: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}