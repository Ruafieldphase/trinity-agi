# Chocolatey를 이용한 Tesseract OCR 자동 설치
# 관리자 권한 필요

$ErrorActionPreference = 'Stop'

Write-Host "[SEARCH] Tesseract OCR 설치 (Chocolatey 방식)" -ForegroundColor Cyan

# 1. Chocolatey 설치 확인
if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
    Write-Host "[PACKAGE] Chocolatey 설치 중..." -ForegroundColor Yellow
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    Write-Host "[OK] Chocolatey 설치 완료" -ForegroundColor Green
}

# 2. Tesseract 설치
Write-Host "📥 Tesseract OCR 설치 중..." -ForegroundColor Yellow
choco install tesseract -y

# 3. 설치 확인
$tesseractPath = (Get-Command tesseract -ErrorAction SilentlyContinue).Source
if ($tesseractPath) {
    Write-Host "[OK] Tesseract OCR 설치 완료!" -ForegroundColor Green
    Write-Host "   경로: $tesseractPath" -ForegroundColor Gray
    tesseract --version
    
    # Python 스크립트 업데이트
    $pythonScript = "D:\nas_backup\LLM_Unified\ion-mentoring\computer_use.py"
    if (Test-Path $pythonScript) {
        Write-Host "[LOG] computer_use.py 업데이트 중..." -ForegroundColor Yellow
        $content = Get-Content $pythonScript -Raw
        $content = $content -replace '#\s*pytesseract\.pytesseract\.tesseract_cmd', "pytesseract.pytesseract.tesseract_cmd = r'$tesseractPath'"
        $content | Set-Content $pythonScript -Encoding UTF8
        Write-Host "[OK] Python 스크립트 업데이트 완료" -ForegroundColor Green
    }
}
else {
    Write-Host "[ERROR] 설치 확인 실패" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[SUCCESS] 모든 설정 완료!" -ForegroundColor Green
