<#
 Tesseract 설치 후 확인/진단 스크립트 (안전 모드)
 - 시스템 파일이나 Python 소스를 변경하지 않습니다.
 - 설치 경로 탐지 및 버전 확인만 수행합니다.
#>

[CmdletBinding()]
param(
    [switch]$English
)

$ErrorActionPreference = 'Stop'

# Ensure UTF-8 console to avoid mojibake in Hangul output
try { [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false) } catch {}
try { $script:OutputEncoding = [Console]::OutputEncoding } catch {}
try { chcp 65001 | Out-Null } catch {}

function Say {
    param(
        [string]$Ko,
        [string]$En,
        [ConsoleColor]$Color = [ConsoleColor]::White
    )
    $msg = if ($English) { $En } else { $Ko }
    Write-Host $msg -ForegroundColor $Color
}

Say "[CONFIG] Tesseract OCR 자동 설정(안전 모드)" "Configure Tesseract OCR (safe mode)" ([ConsoleColor]::Cyan)

# 1) Tesseract 경로 찾기
$possiblePaths = @(
    "C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
    "C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe",
    "$env:ProgramFiles\\Tesseract-OCR\\tesseract.exe",
    "${env:ProgramFiles(x86)}\\Tesseract-OCR\\tesseract.exe",
    "C:\\ProgramData\\chocolatey\\bin\\tesseract.exe"
)

$tesseractPath = $null
foreach ($path in $possiblePaths) {
    if (Test-Path $path) { $tesseractPath = $path; break }
}

if (-not $tesseractPath) {
    try { $cmd = Get-Command tesseract.exe -ErrorAction SilentlyContinue } catch {}
    if ($cmd) { $tesseractPath = $cmd.Source }
}

if (-not $tesseractPath) {
    Say "[ERROR] Tesseract OCR을 찾을 수 없습니다." "Tesseract OCR not found." ([ConsoleColor]::Red)
    Say "   ▶ 관리자 설치: .\\install_tesseract_admin.ps1" "   ▶ Run as Admin: .\\install_tesseract_admin.ps1" ([ConsoleColor]::Yellow)
    Say "   ▶ winget 설치(사용자/머신): .\\install_tesseract_winget.ps1 [-Admin]" "   ▶ winget alternative: .\\install_tesseract_winget.ps1 [-Admin]" ([ConsoleColor]::Yellow)
    exit 1
}

Say "[OK] Tesseract OCR 발견: $tesseractPath" "Found Tesseract OCR: $tesseractPath" ([ConsoleColor]::Green)

# 2) 버전 확인
try { & $tesseractPath --version } catch { Write-Warning $_ }

# 3) 안내
Write-Host ""
Say "[SUCCESS] 확인 완료" "Verification complete" ([ConsoleColor]::Green)
Say "   현재 Python 백엔드는 자동으로 Tesseract 경로를 탐지하며, 실패 시 RapidOCR로 폴백합니다." "   Python backend auto-detects Tesseract and falls back to RapidOCR if needed." ([ConsoleColor]::Gray)
Say "   추가 설정은 필요하지 않습니다. 시스템 PATH 변경도 수행하지 않습니다." "   No extra setup needed. System PATH is not modified." ([ConsoleColor]::Gray)

