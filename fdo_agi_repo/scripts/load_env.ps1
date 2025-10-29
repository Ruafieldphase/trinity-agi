# 환경 변수 로드
if (Test-Path .env) {
    Get-Content .env | ForEach-Object {
        if ($_ -match '^([^=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
            Write-Host "✓ $key 설정됨" -ForegroundColor Green
        }
    }
}
else {
    Write-Host "⚠ .env 파일이 없습니다" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "환경 변수 확인:" -ForegroundColor Cyan
Write-Host "GEMINI_API_KEY: $($env:GEMINI_API_KEY.Substring(0, 20))..." -ForegroundColor Gray
