#Requires -Version 5.1
<#
.SYNOPSIS
    AGI Self-Aware Context Manager (게임 봇처럼 상태 인식)

.DESCRIPTION
    Level 1: 키보드 포커스 기반 (좌표 불필요) ✅ 가장 안정적
    Level 2: 이미지 인식 (화면에서 UI 찾기) 🎮 게임 봇 방식
    Level 3: OCR 상태 파악 (텍스트 읽기) 🔮 고급

.PARAMETER InstallDeps
    Python 패키지 설치 (pyautogui, pyperclip, pillow)

.PARAMETER UseImage
    Level 2 (이미지 인식) 사용

.PARAMETER TestFocus
    Level 1 (포커스 감지) 테스트

.PARAMETER TestImage
    Level 2 (이미지 인식) 테스트

.PARAMETER CreateGuide
    UI 템플릿 생성 가이드

.PARAMETER Verbose
    상세 로그 출력

.EXAMPLE
    .\auto_switch_chat_wrapper.ps1
    # 기본: Level 1 (키보드 포커스)

.EXAMPLE
    .\auto_switch_chat_wrapper.ps1 -UseImage
    # Level 2: 이미지 인식 사용

.EXAMPLE
    .\auto_switch_chat_wrapper.ps1 -InstallDeps
    # 필요한 패키지 설치
#>

[CmdletBinding()]
param(
    [switch]$InstallDeps,
    [switch]$UseImage,
    [switch]$TestFocus,
    [switch]$TestImage,
    [switch]$CreateGuide,
    [switch]$Verbose
)

$ErrorActionPreference = 'Stop'
$WorkspaceRoot = Split-Path -Parent $PSScriptRoot

# Python 경로 찾기
$PythonExe = $null
$VenvPaths = @(
    "$WorkspaceRoot\fdo_agi_repo\.venv\Scripts\python.exe",
    "$WorkspaceRoot\LLM_Unified\.venv\Scripts\python.exe",
    "$WorkspaceRoot\.venv\Scripts\python.exe"
)

foreach ($venv in $VenvPaths) {
    if (Test-Path $venv) {
        $PythonExe = $venv
        break
    }
}

if (-not $PythonExe) {
    $PythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
    if (-not $PythonExe) {
        Write-Host "❌ Python not found" -ForegroundColor Red
        exit 1
    }
}

Write-Host "🐍 Using Python: $PythonExe" -ForegroundColor Cyan

# 패키지 설치
if ($InstallDeps) {
    Write-Host "`n📦 Installing dependencies..." -ForegroundColor Yellow
    
    $packages = @(
        "pyautogui",
        "pyperclip",
        "pillow",
        "pytesseract"  # OCR (선택사항)
    )
    
    foreach ($pkg in $packages) {
        Write-Host "  Installing $pkg..." -ForegroundColor Gray
        & $PythonExe -m pip install $pkg --quiet
    }
    
    Write-Host "✅ Dependencies installed" -ForegroundColor Green
    
    # Tesseract OCR 안내
    Write-Host "`n💡 For OCR support (Level 3):" -ForegroundColor Cyan
    Write-Host "   1. Download Tesseract: https://github.com/UB-Mannheim/tesseract/wiki" -ForegroundColor Gray
    Write-Host "   2. Install to: C:\Program Files\Tesseract-OCR" -ForegroundColor Gray
    Write-Host "   3. Add to PATH or set TESSDATA_PREFIX" -ForegroundColor Gray
    
    exit 0
}

# UI 템플릿 가이드 생성
if ($CreateGuide) {
    Write-Host "`n📚 Creating UI template guide..." -ForegroundColor Yellow
    & $PythonExe "$PSScriptRoot\agi_self_aware_context_manager.py" --create-guide
    exit $LASTEXITCODE
}

# 포커스 테스트
if ($TestFocus) {
    Write-Host "`n🧪 Testing focus detection..." -ForegroundColor Yellow
    Write-Host "   1. Make sure VS Code Copilot Chat is open" -ForegroundColor Gray
    Write-Host "   2. Focus should be on chat input field" -ForegroundColor Gray
    Write-Host "`n⏳ Starting test in 3 seconds..." -ForegroundColor Cyan
    Start-Sleep -Seconds 3
    
    & $PythonExe "$PSScriptRoot\agi_self_aware_context_manager.py" --test-focus --verbose
    exit $LASTEXITCODE
}

# 이미지 인식 테스트
if ($TestImage) {
    Write-Host "`n🧪 Testing image detection..." -ForegroundColor Yellow
    Write-Host "   1. Make sure VS Code Copilot Chat is open" -ForegroundColor Gray
    Write-Host "   2. Chat input field should be visible" -ForegroundColor Gray
    Write-Host "   3. UI template must exist: scripts\ui_templates\chat_input.png" -ForegroundColor Gray
    Write-Host "`n⏳ Starting test in 3 seconds..." -ForegroundColor Cyan
    Start-Sleep -Seconds 3
    
    & $PythonExe "$PSScriptRoot\agi_self_aware_context_manager.py" --test-image --verbose
    exit $LASTEXITCODE
}

# 메인 실행: 컨텍스트 복원 + 자동 붙여넣기
Write-Host "`n🔄 AGI Self-Aware Context Manager" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Gray

# 1. 세션 컨텍스트 복원
Write-Host "`n📖 Step 1: Restoring session context..." -ForegroundColor Yellow
& "$PSScriptRoot\session_continuity_restore.ps1" -Silent -ForceRegenerate
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Context restore failed" -ForegroundColor Red
    exit 1
}

$ContextFile = "$WorkspaceRoot\outputs\.copilot_context_summary.md"
if (-not (Test-Path $ContextFile)) {
    Write-Host "❌ Context file not found: $ContextFile" -ForegroundColor Red
    exit 1
}

# 2. 컨텍스트 길이 체크
Write-Host "`n📊 Step 2: Checking context length..." -ForegroundColor Yellow
& $PythonExe "$PSScriptRoot\check_context_length.py" --file $ContextFile
if ($LASTEXITCODE -eq 2) {
    Write-Host "⚠️ Context too large, but continuing..." -ForegroundColor Yellow
}

# 3. 새 채팅 열기
Write-Host "`n💬 Step 3: Opening new chat..." -ForegroundColor Yellow
code --command "workbench.action.chat.open"
Start-Sleep -Milliseconds 800

# 4. 스마트 자동 붙여넣기
Write-Host "`n🎯 Step 4: Smart auto-paste..." -ForegroundColor Yellow

$PasteArgs = @(
    "$PSScriptRoot\agi_self_aware_context_manager.py",
    "--file", $ContextFile
)

if ($UseImage) {
    Write-Host "   📌 Using Level 2: Image Detection" -ForegroundColor Cyan
    $PasteArgs += "--use-image"
}
else {
    Write-Host "   📌 Using Level 1: Keyboard Focus" -ForegroundColor Cyan
}

if ($Verbose) {
    $PasteArgs += "--verbose"
}

& $PythonExe $PasteArgs

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Auto-paste completed successfully!" -ForegroundColor Green
    Write-Host "   💡 Press Enter to send, or edit the message first" -ForegroundColor Gray
}
else {
    Write-Host "`n❌ Auto-paste failed" -ForegroundColor Red
    Write-Host "`n🔧 Troubleshooting:" -ForegroundColor Yellow
    Write-Host "   1. Run: auto_switch_chat_wrapper.ps1 -TestFocus" -ForegroundColor Gray
    Write-Host "   2. Run: auto_switch_chat_wrapper.ps1 -TestImage" -ForegroundColor Gray
    Write-Host "   3. Run: auto_switch_chat_wrapper.ps1 -CreateGuide" -ForegroundColor Gray
    exit 1
}

Write-Host "`n" + ("=" * 60) -ForegroundColor Gray
Write-Host "🎮 AGI Self-Aware Context Manager - Complete" -ForegroundColor Cyan
