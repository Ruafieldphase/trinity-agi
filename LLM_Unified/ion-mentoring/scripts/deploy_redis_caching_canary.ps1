# Redis 캐싱 배포 스크립트
# Phase 14 Task 3: Canary 환경 Redis 통합 배포

Write-Host "🚀 Canary 환경 Redis 캐싱 배포 시작..." -ForegroundColor Cyan

$project = "naeda-genesis"
$region = "us-central1"
$service = "ion-api-canary"

# Redis 환경 변수
$redisEnv = @(
    "REDIS_ENABLED=true",
    "REDIS_HOST=10.234.163.115",
    "REDIS_PORT=6379",
    "REDIS_DB=0"
)

Write-Host "`n📦 빌드 및 배포 중..." -ForegroundColor Yellow
gcloud run deploy $service `
    --source . `
    --region=$region `
    --project=$project `
    --set-env-vars ($redisEnv -join ",") `
    --allow-unauthenticated `
    --min-instances=0 `
    --max-instances=5 `
    --memory=512Mi `
    --cpu=1 `
    --timeout=60

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ 배포 실패" -ForegroundColor Red
    exit 1
}

Write-Host "`n✅ 배포 완료!" -ForegroundColor Green

# 배포된 리비전 확인
Write-Host "`n📊 배포된 리비전 확인..." -ForegroundColor Cyan
gcloud run revisions list `
    --service=$service `
    --region=$region `
    --project=$project `
    --limit=1 `
    --format="table(metadata.name,status.conditions[0].status,metadata.creationTimestamp)"

Write-Host "`n🔍 서비스 URL 확인..." -ForegroundColor Cyan
$url = gcloud run services describe $service `
    --region=$region `
    --project=$project `
    --format="value(status.url)"

Write-Host "URL: $url" -ForegroundColor Green

Write-Host "`n🧪 헬스 체크 테스트..." -ForegroundColor Cyan
$response = Invoke-RestMethod -Uri "$url/api/v2/health" -Method GET -ErrorAction SilentlyContinue

if ($response) {
    Write-Host "✅ 헬스 체크 성공" -ForegroundColor Green
    Write-Host "Redis 상태: $($response.dependencies.redis)" -ForegroundColor Yellow
    $response | ConvertTo-Json -Depth 3
}
else {
    Write-Host "⚠️ 헬스 체크 응답 없음" -ForegroundColor Yellow
}

Write-Host "`n✨ 배포 및 검증 완료!" -ForegroundColor Green
