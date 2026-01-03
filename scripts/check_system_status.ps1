# AGI 시스템 상태 확인 스크립트
# ===================================

Write-Host "🌊 리듬 기반 AGI 시스템 상태 확인" -ForegroundColor Cyan
Write-Host "=" * 60

# 1. 백그라운드 프로세스 확인
Write-Host "`n📊 백그라운드 프로세스:" -ForegroundColor Yellow

$processes = Get-WmiObject Win32_Process | Where-Object { 
    $_.CommandLine -like '*scripts/linux/*' 
}

if ($processes) {
    $processes | ForEach-Object {
        $scriptName = ($_.CommandLine -split '\\')[-1] -replace '\.py.*', ''
        Write-Host "  ✅ $scriptName (PID: $($_.ProcessId))" -ForegroundColor Green
    }
} else {
    Write-Host "  ❌ 실행 중인 백그라운드 프로세스 없음" -ForegroundColor Red
}

# 2. 대시보드 확인
Write-Host "`n🎨 대시보드:" -ForegroundColor Yellow

$dashboardProcess = Get-Process node -ErrorAction SilentlyContinue | Where-Object {
    $_.MainWindowTitle -like '*Next.js*' -or $_.ProcessName -eq 'node'
}

if ($dashboardProcess) {
    Write-Host "  ✅ 대시보드 실행 중" -ForegroundColor Green
    Write-Host "     URL: http://localhost:3001" -ForegroundColor Cyan
} else {
    Write-Host "  ❌ 대시보드 미실행" -ForegroundColor Red
    Write-Host "     시작: cd dashboard && npm run dev" -ForegroundColor Gray
}

# 3. 주요 파일 존재 확인
Write-Host "`n📁 주요 파일:" -ForegroundColor Yellow

$files = @{
    "Bridge Tasks" = "outputs\bridge\bridge_tasks.jsonl"
    "Bridge Responses" = "outputs\bridge\bridge_responses.jsonl"
    "Unified Pulse" = "outputs\unified_pulse.json"
    "Rhythm Health" = "outputs\rhythm_health_latest.json"
}

foreach ($name in $files.Keys) {
    $path = $files[$name]
    if (Test-Path $path) {
        $size = (Get-Item $path).Length
        Write-Host "  ✅ $name ($size bytes)" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  $name (없음)" -ForegroundColor Yellow
    }
}

# 4. 최근 로그 확인
Write-Host "`n📝 최근 로그 (마지막 5줄):" -ForegroundColor Yellow

if (Test-Path "outputs\master_daemon.log") {
    Get-Content "outputs\master_daemon.log" -Tail 5 | ForEach-Object {
        if ($_ -match "ERROR") {
            Write-Host "  ❌ $_" -ForegroundColor Red
        } elseif ($_ -match "SUCCESS") {
            Write-Host "  ✅ $_" -ForegroundColor Green
        } else {
            Write-Host "  📄 $_" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "  ⚠️  로그 파일 없음" -ForegroundColor Yellow
}

# 5. Vertex AI 설정 확인
Write-Host "`n🚀 Vertex AI 설정:" -ForegroundColor Yellow

if ($env:VERTEX_PROJECT_ID) {
    Write-Host "  ✅ Project ID: $env:VERTEX_PROJECT_ID" -ForegroundColor Green
    Write-Host "  🚀 실제 Vertex AI 모드 활성화" -ForegroundColor Cyan
} else {
    Write-Host "  🔧 Mock AI 모드 (프로젝트 ID 미설정)" -ForegroundColor Yellow
    Write-Host "     설정: `$env:VERTEX_PROJECT_ID='your-project-id'" -ForegroundColor Gray
}

# 6. 시스템 요약
Write-Host "`n" + "=" * 60
Write-Host "📊 시스템 요약:" -ForegroundColor Cyan

$bgCount = if ($processes) { $processes.Count } else { 0 }
$dashboardStatus = if ($dashboardProcess) { "실행 중" } else { "중지됨" }
$aiMode = if ($env:VERTEX_PROJECT_ID) { "Vertex AI" } else { "Mock AI" }

Write-Host "  백그라운드 프로세스: $bgCount 개"
Write-Host "  대시보드: $dashboardStatus"
Write-Host "  AI 모드: $aiMode"

if ($bgCount -gt 0 -and $dashboardProcess) {
    Write-Host "`n✨ 시스템 정상 작동 중!" -ForegroundColor Green
    Write-Host "   대시보드: http://localhost:3001" -ForegroundColor Cyan
} else {
    Write-Host "`n⚠️  일부 컴포넌트가 실행되지 않았습니다." -ForegroundColor Yellow
    Write-Host "   시작: .\scripts\start_agi_system.ps1" -ForegroundColor Gray
}

Write-Host "`n" + "=" * 60