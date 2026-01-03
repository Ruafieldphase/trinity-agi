# 🆕 New Chat with Context (Quick Start) - 게임 봇 모드!
# 세션 복원 → 컨텍스트 복사 → 새 채팅 → 자동 붙여넣기

param(
    [switch]$DryRun,
    [switch]$SkipPaste,
    [int]$DelayMs = 2000
)

$ErrorActionPreference = "Stop"
$ws = Split-Path -Parent $PSScriptRoot

# 1️⃣ 세션 복원
Write-Host "🔄 세션 컨텍스트 복원 중..." -ForegroundColor Cyan
& "$ws\scripts\session_continuity_restore.ps1" -Silent
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️ 세션 복원 실패 (무시하고 진행)" -ForegroundColor Yellow
}

# 2️⃣ 컨텍스트 길이 체크
$summary = Join-Path $ws "outputs\.copilot_context_summary.md"
if (Test-Path $summary) {
    Write-Host "📊 컨텍스트 길이 체크..." -ForegroundColor Cyan
    
    try {
        $py = Join-Path $ws "LLM_Unified\.venv\Scripts\python.exe"
        if (!(Test-Path $py)) { $py = "python" }
        
        $checkResult = & $py "$ws\scripts\check_context_length.py" --file $summary --json 2>&1 | Out-String
        
        if ($checkResult -match '"exceeds_threshold":\s*true') {
            Write-Host "⚠️ 경고: 컨텍스트 길이가 임계값 초과!" -ForegroundColor Yellow
            Write-Host "   계속 진행하려면 Enter, 중단하려면 Ctrl+C" -ForegroundColor Yellow
            if (!$DryRun) {
                Read-Host "Press Enter to continue"
            }
        }
        else {
            Write-Host "✅ 컨텍스트 길이 안전" -ForegroundColor Green
        }
    }
    catch {
        Write-Host "⚠️ 길이 체크 실패 (무시하고 진행): $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# 3️⃣ 클립보드에 컨텍스트 복사
Write-Host "📋 클립보드에 컨텍스트 복사..." -ForegroundColor Cyan
if (Test-Path $summary) {
    Get-Content $summary -Raw | Set-Clipboard
    Write-Host "✅ 클립보드 복사 완료" -ForegroundColor Green
}
else {
    Write-Host "⚠️ 컨텍스트 파일 없음 (빈 클립보드)" -ForegroundColor Yellow
    "" | Set-Clipboard
}

if ($DryRun) {
    Write-Host "`n🔍 DRY-RUN 모드: 실제 작업 없이 종료" -ForegroundColor Magenta
    exit 0
}

# 4️⃣ 새 Copilot 채팅 열기
Write-Host "🆕 새 Copilot 채팅 열기..." -ForegroundColor Cyan
& code --command "workbench.action.chat.open"
Start-Sleep -Milliseconds 500

if ($SkipPaste) {
    Write-Host "⏭️ 자동 붙여넣기 스킵 (수동으로 Ctrl+V)" -ForegroundColor Yellow
    exit 0
}

# 5️⃣ 자동 붙여넣기
Write-Host "⏳ ${DelayMs}ms 대기 후 자동 붙여넣기..." -ForegroundColor Cyan
Start-Sleep -Milliseconds $DelayMs

try {
    $py = Join-Path $ws "LLM_Unified\.venv\Scripts\python.exe"
    if (!(Test-Path $py)) { $py = "python" }
    
    & $py "$ws\scripts\auto_paste_to_chat.py" --delay-ms $DelayMs
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 자동 붙여넣기 완료!" -ForegroundColor Green
        Write-Host "🎮 게임 봇 모드 활성화! 이제 Enter만 누르면 됩니다!" -ForegroundColor Magenta
    }
    else {
        Write-Host "⚠️ 자동 붙여넣기 실패 (수동으로 Ctrl+V)" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "⚠️ 자동 붙여넣기 오류: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "   수동으로 Ctrl+V로 붙여넣으세요" -ForegroundColor Yellow
}