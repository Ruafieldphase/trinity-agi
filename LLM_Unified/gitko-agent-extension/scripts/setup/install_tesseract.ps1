# Tesseract OCR 자동 설치 스크립트
# 관리자 권한 필요

param(
    [switch]$SkipDownload = $false
)

$ErrorActionPreference = 'Stop'

Write-Host "[SEARCH] Tesseract OCR 설치 시작..." -ForegroundColor Cyan

# 1. 설치 경로
$installPath = "C:\Program Files\Tesseract-OCR"
$tesseractExe = Join-Path $installPath "tesseract.exe"

# 2. 이미 설치되어 있는지 확인
if (Test-Path $tesseractExe) {
    Write-Host "[OK] Tesseract OCR이 이미 설치되어 있습니다!" -ForegroundColor Green
    Write-Host "   경로: $tesseractExe" -ForegroundColor Gray
    & $tesseractExe --version
    exit 0
}

# 3. 다운로드 URL (최신 버전)
$downloadUrl = "https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.3.20231005.exe"
$installerPath = Join-Path $env:TEMP "tesseract-installer.exe"

if (-not $SkipDownload) {
    Write-Host "📥 Tesseract OCR 다운로드 중..." -ForegroundColor Yellow
    Write-Host "   URL: $downloadUrl" -ForegroundColor Gray
    
    try {
        Invoke-WebRequest -Uri $downloadUrl -OutFile $installerPath -UseBasicParsing
        Write-Host "[OK] 다운로드 완료: $installerPath" -ForegroundColor Green
    }
    catch {
        Write-Host "[ERROR] 다운로드 실패: $_" -ForegroundColor Red
        Write-Host "수동 다운로드: https://github.com/UB-Mannheim/tesseract/wiki" -ForegroundColor Yellow
        exit 1
    }
}

# 4. 관리자 권한 확인
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "[WARN]  관리자 권한이 필요합니다!" -ForegroundColor Yellow
    Write-Host "   PowerShell을 관리자 모드로 실행한 후 다시 시도해주세요." -ForegroundColor Gray
    Write-Host ""
    Write-Host "[LOG] 수동 설치 방법:" -ForegroundColor Cyan
    Write-Host "   1. 다운로드된 파일 실행: $installerPath" -ForegroundColor Gray
    Write-Host "   2. 설치 경로: $installPath" -ForegroundColor Gray
    Write-Host "   3. 'Additional language data' 옵션 선택 (한국어/일본어 포함)" -ForegroundColor Gray
    exit 1
}

# 5. 자동 설치 (무인 설치)
Write-Host "[DEPLOY] Tesseract OCR 자동 설치 중..." -ForegroundColor Cyan
Write-Host "   설치 경로: $installPath" -ForegroundColor Gray

try {
    # 무인 설치 옵션
    $installArgs = @(
        "/S",  # Silent install
        "/D=$installPath"
    )
    
    Start-Process -FilePath $installerPath -ArgumentList $installArgs -Wait -NoNewWindow
    
    # 설치 확인
    if (Test-Path $tesseractExe) {
        Write-Host "[OK] Tesseract OCR 설치 완료!" -ForegroundColor Green
        Write-Host "   경로: $tesseractExe" -ForegroundColor Gray
        & $tesseractExe --version
        
        # 환경 변수에 추가 (선택 사항)
        $currentPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
        if ($currentPath -notlike "*$installPath*") {
            Write-Host "[LOG] PATH 환경 변수에 추가 중..." -ForegroundColor Yellow
            [Environment]::SetEnvironmentVariable("Path", "$currentPath;$installPath", "Machine")
            Write-Host "[OK] PATH 추가 완료 (재부팅 후 적용)" -ForegroundColor Green
        }
        
        # Python 스크립트 업데이트
        $pythonScript = "D:\nas_backup\LLM_Unified\ion-mentoring\computer_use.py"
        if (Test-Path $pythonScript) {
            Write-Host "[LOG] computer_use.py 업데이트 중..." -ForegroundColor Yellow
            $content = Get-Content $pythonScript -Raw
            $content = $content -replace '#\s*pytesseract\.pytesseract\.tesseract_cmd', 'pytesseract.pytesseract.tesseract_cmd'
            $content | Set-Content $pythonScript -Encoding UTF8
            Write-Host "[OK] Python 스크립트 업데이트 완료" -ForegroundColor Green
        }
        
    }
    else {
        Write-Host "[ERROR] 설치 확인 실패" -ForegroundColor Red
        exit 1
    }
}
catch {
    Write-Host "[ERROR] 설치 실패: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[SUCCESS] 모든 설정 완료!" -ForegroundColor Green
Write-Host "   이제 Computer Use 기능을 사용할 수 있습니다." -ForegroundColor Gray
