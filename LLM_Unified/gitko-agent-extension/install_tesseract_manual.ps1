# Tesseract OCR 수동 설치 가이드

Write-Host "📖 Tesseract OCR 수동 설치 가이드" -ForegroundColor Cyan
Write-Host ""

Write-Host "1️⃣  다운로드 링크 (브라우저에서 열기):" -ForegroundColor Yellow
Write-Host "   https://github.com/UB-Mannheim/tesseract/releases/latest" -ForegroundColor Green
Write-Host "   또는" -ForegroundColor Gray
Write-Host "   https://github.com/tesseract-ocr/tesseract/releases" -ForegroundColor Green
Write-Host ""

Write-Host "2️⃣  설치 파일 선택:" -ForegroundColor Yellow
Write-Host "   - tesseract-ocr-w64-setup-5.x.x.xxxxxxxx.exe (64비트 Windows)" -ForegroundColor Gray
Write-Host "   - 가장 최신 버전 다운로드" -ForegroundColor Gray
Write-Host ""

Write-Host "3️⃣  설치 옵션:" -ForegroundColor Yellow
Write-Host "   - 설치 경로: C:\Program Files\Tesseract-OCR (기본값)" -ForegroundColor Gray
Write-Host "   - Additional language data: 체크 (한국어/영어 포함)" -ForegroundColor Gray
Write-Host ""

Write-Host "4️⃣  설치 후 확인:" -ForegroundColor Yellow
Write-Host "   tesseract --version" -ForegroundColor Gray
Write-Host ""

Write-Host "5️⃣  설치 완료 후 이 스크립트 실행:" -ForegroundColor Yellow
Write-Host "   .\configure_tesseract.ps1" -ForegroundColor Gray
Write-Host ""

Write-Host "💡 대체 방법 (Chocolatey):" -ForegroundColor Cyan
Write-Host "   관리자 PowerShell에서 실행:" -ForegroundColor Gray
Write-Host "   .\install_tesseract_choco.ps1" -ForegroundColor Green
Write-Host ""

# 브라우저로 다운로드 페이지 열기
$openBrowser = Read-Host "브라우저로 다운로드 페이지를 여시겠습니까? (y/n)"
if ($openBrowser -eq 'y') {
    Start-Process "https://github.com/UB-Mannheim/tesseract/releases/latest"
    Write-Host "✅ 브라우저 열림" -ForegroundColor Green
}
