# Safe Copilot Context Loader
# 400 invalid_request_body 에러 방지를 위한 안전한 컨텍스트 로더

param(
    [ValidateSet('quick', 'rhythm', 'goals', 'full')]
    [string]$Level = 'quick',
    
    [switch]$ToClipboard,
    [switch]$ShowPreview
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot



$ErrorActionPreference = 'Stop'
$Workspace = "$WorkspaceRoot"
$SafeLimit = 3500  # Copilot 안전 제한

# 레벨별 파일 정의
$ContextFiles = @{
    quick  = @{
        File        = "$Workspace\outputs\.copilot_context_summary.md"
        MaxChars    = 1000
        Description = "초간단 요약 (663자)"
    }
    rhythm = @{
        File        = "$Workspace\outputs\RHYTHM_SYSTEM_STATUS_REPORT.md"
        MaxChars    = 2000
        Description = "리듬 상태 리포트"
    }
    goals  = @{
        File        = "$Workspace\fdo_agi_repo\memory\goal_tracker.json"
        MaxChars    = 1500
        Description = "자율 목표 트래커"
    }
    full   = @{
        File        = "$Workspace\outputs\session_continuity_latest.md"
        MaxChars    = 3500
        Description = "전체 세션 리포트 (요약 버전)"
    }
}

$selected = $ContextFiles[$Level]

if (-not (Test-Path $selected.File)) {
    Write-Host "❌ 파일을 찾을 수 없습니다: $($selected.File)" -ForegroundColor Red
    exit 1
}

$content = Get-Content $selected.File -Raw -Encoding UTF8

# 길이 체크 및 자동 요약
if ($content.Length -gt $SafeLimit) {
    Write-Host "⚠️  원본 길이 ($($content.Length)자)가 안전 제한($SafeLimit자)을 초과합니다" -ForegroundColor Yellow
    
    # 자동 요약: 섹션 헤더 + 첫 3줄만
    $lines = $content -split "`n"
    $summary = @()
    $inSection = $false
    $lineCount = 0
    
    foreach ($line in $lines) {
        if ($line -match '^#{1,3}\s+') {
            # 새 섹션 시작
            $summary += $line
            $inSection = $true
            $lineCount = 0
        }
        elseif ($inSection -and $lineCount -lt 3) {
            # 섹션 내 첫 3줄만
            $summary += $line
            $lineCount++
        }
    }
    
    $content = ($summary -join "`n") + "`n`n... (나머지 생략, 전체 보기: $($selected.File))"
    Write-Host "✂️  자동 요약 완료: $($content.Length)자" -ForegroundColor Green
}

if ($ShowPreview) {
    Write-Host "`n📄 미리보기 ($Level - $($selected.Description)):" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
    Write-Host $content
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
    Write-Host "`n📏 길이: $($content.Length)자 (안전 제한: $SafeLimit자)" -ForegroundColor Cyan
}

if ($ToClipboard) {
    $content | Set-Clipboard
    Write-Host "`n✅ 클립보드에 복사 완료!" -ForegroundColor Green
    Write-Host "📏 길이: $($content.Length)자" -ForegroundColor Cyan
    Write-Host "📋 이제 Copilot 채팅에 Ctrl+V로 붙여넣으세요!" -ForegroundColor Yellow
}
else {
    # 출력만
    Write-Output $content
}

# 사용 가이드
if (-not $ToClipboard -and -not $ShowPreview) {
    Write-Host "`n💡 사용법:" -ForegroundColor Yellow
    Write-Host "  quick   (기본): .\safe_copilot_context.ps1 -ToClipboard" -ForegroundColor Gray
    Write-Host "  rhythm 리포트: .\safe_copilot_context.ps1 -Level rhythm -ToClipboard" -ForegroundColor Gray
    Write-Host "  미리보기:      .\safe_copilot_context.ps1 -Level full -ShowPreview" -ForegroundColor Gray
}