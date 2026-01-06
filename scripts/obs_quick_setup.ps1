# OBS Studio 빠른 설정 및 시작 스크립트
# VS Code 화면 유튜브 라이브 스트리밍용

param(
    [switch]$CheckOnly,  # 설정만 확인하고 시작 안 함
    [switch]$StopStream, # 스트리밍 중지
    [switch]$AutoStartStreaming, # OBS 실행 시 즉시 방송 시작 (주의: 스트림 키 필수)
    [string]$OBSProfile = "Default",  # OBS 프로필 이름
    [string]$Scene = "VS Code Stream"  # OBS 씬 이름
)

$ErrorActionPreference = "Stop"

# OBS Studio 경로 확인
$obsPaths = @(
    "C:\Program Files\obs-studio\bin\64bit\obs64.exe",
    "C:\Program Files (x86)\obs-studio\bin\64bit\obs64.exe",
    "$env:ProgramFiles\obs-studio\bin\64bit\obs64.exe"
)

$obsPath = $obsPaths | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $obsPath) {
    Write-Host "[ERROR] OBS Studio를 찾을 수 없습니다." -ForegroundColor Red
    Write-Host "   다운로드: https://obsproject.com/download" -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] OBS Studio 발견: $obsPath" -ForegroundColor Green

# VS Code 실행 확인
$vscodeProcess = Get-Process -Name "Code" -ErrorAction SilentlyContinue

if ($vscodeProcess) {
    Write-Host "[OK] VS Code 실행 중 (PID: $($vscodeProcess.Id))" -ForegroundColor Green
}
else {
    Write-Host "[WARN]  VS Code가 실행되지 않았습니다." -ForegroundColor Yellow
    Write-Host "   먼저 VS Code를 실행하세요." -ForegroundColor Yellow
}

# 시스템 리소스 체크
$cpu = Get-WmiObject Win32_Processor | Select-Object -ExpandProperty LoadPercentage
$mem = Get-WmiObject Win32_OperatingSystem
$memUsage = [math]::Round(($mem.TotalVisibleMemorySize - $mem.FreePhysicalMemory) / $mem.TotalVisibleMemorySize * 100, 1)

Write-Host "`n[INFO] 시스템 상태:" -ForegroundColor Cyan
Write-Host "   CPU 사용률: $cpu%" -ForegroundColor $(if ($cpu -gt 80) { "Red" } elseif ($cpu -gt 60) { "Yellow" } else { "Green" })
Write-Host "   메모리 사용률: $memUsage%" -ForegroundColor $(if ($memUsage -gt 85) { "Red" } elseif ($memUsage -gt 70) { "Yellow" } else { "Green" })

if ($cpu -gt 80 -or $memUsage -gt 85) {
    Write-Host "[WARN]  시스템 부하가 높습니다. 스트리밍 품질이 저하될 수 있습니다." -ForegroundColor Yellow
}

# 인터넷 속도 체크 (간단한 방법)
Write-Host "`n[WEB] 인터넷 연결 확인 중..." -ForegroundColor Cyan
try {
    $ping = Test-Connection -ComputerName youtube.com -Count 1 -ErrorAction Stop
    Write-Host "[OK] YouTube 연결 정상 (지연: $($ping.ResponseTime)ms)" -ForegroundColor Green
}
catch {
    Write-Host "[ERROR] 인터넷 연결 문제 감지" -ForegroundColor Red
    Write-Host "   스트리밍 전에 네트워크를 확인하세요." -ForegroundColor Yellow
}

# VS Code 설정 추천
Write-Host "`n[SETTINGS]  VS Code 최적화 권장사항:" -ForegroundColor Cyan
Write-Host "   1. 폰트 크기 증가: Ctrl+= 또는 Ctrl+Shift+P → 'Zoom In'" -ForegroundColor White
Write-Host "   2. 테마 변경: Ctrl+K Ctrl+T → Light+ (시청자 가독성)" -ForegroundColor White
Write-Host "   3. Zen Mode: Ctrl+K Z (방해 요소 제거)" -ForegroundColor White
Write-Host "   4. 터미널 히스토리 클리어: clear 명령" -ForegroundColor White

# 체크 모드면 여기서 종료
if ($CheckOnly) {
    Write-Host "`n[OK] 사전 점검 완료. OBS를 수동으로 시작하세요." -ForegroundColor Green
    exit 0
}

# OBS 스트리밍 중지
if ($StopStream) {
    $obsProcess = Get-Process -Name "obs64" -ErrorAction SilentlyContinue
    if ($obsProcess) {
        Write-Host "`n[END]  OBS 스트리밍 중지 중..." -ForegroundColor Yellow
        # obs-websocket 사용하려면 추가 설정 필요
        Write-Host "   OBS에서 수동으로 '방송 중지'를 클릭하세요." -ForegroundColor Yellow
    }
    else {
        Write-Host "[ERROR] OBS가 실행되지 않았습니다." -ForegroundColor Red
    }
    exit 0
}

# OBS 시작
Write-Host "`n[START] OBS Studio 시작 중..." -ForegroundColor Cyan
$obsArgs = @()

# 프로필 지정
if ($OBSProfile -ne "Default") {
    $obsArgs += "--profile"
    $obsArgs += $OBSProfile
}

# 씬 지정
if ($Scene) {
    $obsArgs += "--scene"
    $obsArgs += $Scene
}

# 자동 스트리밍 시작 (주의: 스트림 키 설정 필요)
if ($AutoStartStreaming) {
    $obsArgs += "--startstreaming"
}

Write-Host "   명령어: $obsPath $($obsArgs -join ' ')" -ForegroundColor Gray

Start-Process -FilePath $obsPath -ArgumentList $obsArgs

Write-Host "`n[OK] OBS Studio 시작됨!" -ForegroundColor Green
Write-Host "`n📋 다음 단계:" -ForegroundColor Cyan
Write-Host "   1. OBS에서 '창 캡처' 소스 추가 → VS Code 선택" -ForegroundColor White
Write-Host "   2. 설정 → 방송 → 스트림 키 입력 (YouTube Studio에서 복사)" -ForegroundColor White
Write-Host "   3. '방송 시작' 버튼 클릭" -ForegroundColor White
Write-Host "   4. YouTube Studio에서 라이브 상태 확인" -ForegroundColor White

Write-Host "`n📖 자세한 가이드: guides\VSCode_유튜브_라이브_스트리밍_가이드.md" -ForegroundColor Cyan