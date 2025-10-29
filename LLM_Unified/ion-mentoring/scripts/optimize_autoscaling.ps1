<#
.SYNOPSIS
    Cloud Run Auto-scaling Optimizer

.DESCRIPTION
    Cloud Run 서비스의 자동 스케일링 설정을 최적화합니다.
    - Min/Max instances
    - Concurrency
    - CPU/Memory limits

.PARAMETER ServiceName
    서비스 이름 (ion-api 또는 ion-api-canary)

.PARAMETER ProjectId
    GCP 프로젝트 ID

.PARAMETER Region
    리전 (기본값: us-central1)

.PARAMETER DryRun
    실제 적용하지 않고 시뮬레이션만 수행

.EXAMPLE
    .\optimize_autoscaling.ps1 -ServiceName "ion-api" -ProjectId "naeda-genesis" -DryRun
    .\optimize_autoscaling.ps1 -ServiceName "ion-api-canary" -ProjectId "naeda-genesis"
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("ion-api", "ion-api-canary")]
    [string]$ServiceName,

    [Parameter(Mandatory = $true)]
    [string]$ProjectId,

    [string]$Region = "us-central1",

    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

Write-Host "⚙️  Cloud Run Auto-scaling Optimizer" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

# 현재 설정 조회
Write-Host "🔍 1단계: 현재 설정 조회..." -ForegroundColor Yellow
Write-Host ""

try {
    $describeOutput = gcloud run services describe $ServiceName `
        --region=$Region `
        --project=$ProjectId `
        --format=json 2>&1

    if ($LASTEXITCODE -ne 0) {
        throw "서비스 조회 실패: $describeOutput"
    }

    $service = $describeOutput | ConvertFrom-Json

    # 현재 설정 추출
    $currentMinInstances = $service.spec.template.metadata.annotations.'autoscaling.knative.dev/minScale'
    $currentMaxInstances = $service.spec.template.metadata.annotations.'autoscaling.knative.dev/maxScale'
    $currentConcurrency = $service.spec.template.spec.containerConcurrency
    $currentCpu = $service.spec.template.spec.containers[0].resources.limits.cpu
    $currentMemory = $service.spec.template.spec.containers[0].resources.limits.memory

    Write-Host "📊 현재 설정" -ForegroundColor Cyan
    Write-Host "  - Min Instances: $currentMinInstances" -ForegroundColor Gray
    Write-Host "  - Max Instances: $currentMaxInstances" -ForegroundColor Gray
    Write-Host "  - Concurrency: $currentConcurrency" -ForegroundColor Gray
    Write-Host "  - CPU: $currentCpu" -ForegroundColor Gray
    Write-Host "  - Memory: $currentMemory" -ForegroundColor Gray
    Write-Host ""
}
catch {
    Write-Host "❌ 현재 설정 조회 실패: $_" -ForegroundColor Red
    exit 1
}

# 최적 설정 계산
Write-Host "🧮 2단계: 최적 설정 계산..." -ForegroundColor Yellow
Write-Host ""

# 서비스 타입별 권장 설정
$recommendations = @{}

if ($ServiceName -eq "ion-api") {
    # Main 서비스: 안정성 우선
    $recommendations = @{
        MinInstances = 2           # 콜드 스타트 방지
        MaxInstances = 20          # 트래픽 폭증 대응
        Concurrency  = 80           # 적절한 동시 요청 수
        Cpu          = "2"                  # 2 vCPU
        Memory       = "1Gi"             # 1GB RAM
        Reason       = @(
            "Main 서비스는 안정성이 중요",
            "최소 2개 인스턴스로 가용성 보장",
            "concurrency 80으로 응답성과 처리량 균형"
        )
    }
}
else {
    # Canary 서비스: 비용 효율 우선
    $recommendations = @{
        MinInstances = 0           # 비용 절감 (트래픽 없을 때 0으로)
        MaxInstances = 10          # 제한된 트래픽
        Concurrency  = 100          # 높은 동시성 허용
        Cpu          = "1"                  # 1 vCPU
        Memory       = "512Mi"           # 512MB RAM
        Reason       = @(
            "Canary는 테스트 목적으로 비용 최소화",
            "Min 0 으로 유휴 시 비용 절감",
            "Max 10 으로 폭주 방지"
        )
    }
}

Write-Host "💡 권장 설정" -ForegroundColor Cyan
Write-Host "  - Min Instances: $($recommendations.MinInstances)" -ForegroundColor Green
Write-Host "  - Max Instances: $($recommendations.MaxInstances)" -ForegroundColor Green
Write-Host "  - Concurrency: $($recommendations.Concurrency)" -ForegroundColor Green
Write-Host "  - CPU: $($recommendations.Cpu)" -ForegroundColor Green
Write-Host "  - Memory: $($recommendations.Memory)" -ForegroundColor Green
Write-Host ""

Write-Host "📝 근거" -ForegroundColor Yellow
foreach ($reason in $recommendations.Reason) {
    Write-Host "  - $reason" -ForegroundColor Gray
}
Write-Host ""

# 변경 사항 계산
$changes = @()

if ($currentMinInstances -ne $recommendations.MinInstances) {
    $changes += "Min Instances: $currentMinInstances → $($recommendations.MinInstances)"
}

if ($currentMaxInstances -ne $recommendations.MaxInstances) {
    $changes += "Max Instances: $currentMaxInstances → $($recommendations.MaxInstances)"
}

if ($currentConcurrency -ne $recommendations.Concurrency) {
    $changes += "Concurrency: $currentConcurrency → $($recommendations.Concurrency)"
}

if ($currentCpu -ne $recommendations.Cpu) {
    $changes += "CPU: $currentCpu → $($recommendations.Cpu)"
}

if ($currentMemory -ne $recommendations.Memory) {
    $changes += "Memory: $currentMemory → $($recommendations.Memory)"
}

if ($changes.Count -eq 0) {
    Write-Host "✅ 현재 설정이 이미 최적입니다!" -ForegroundColor Green
    exit 0
}

Write-Host "🔄 변경 사항" -ForegroundColor Yellow
foreach ($change in $changes) {
    Write-Host "  - $change" -ForegroundColor Cyan
}
Write-Host ""

# DryRun 모드
if ($DryRun) {
    Write-Host "🔍 DryRun 모드: 실제 적용하지 않음" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "실제 적용하려면 -DryRun 플래그를 제거하고 다시 실행하세요:" -ForegroundColor Gray
    Write-Host "  .\optimize_autoscaling.ps1 -ServiceName $ServiceName -ProjectId $ProjectId" -ForegroundColor Gray
    Write-Host ""
    exit 0
}

# 실제 적용
Write-Host "⚙️  3단계: 설정 적용 중..." -ForegroundColor Yellow
Write-Host ""

try {
    # gcloud 명령어 구성
    $updateArgs = @(
        "run", "services", "update", $ServiceName,
        "--region=$Region",
        "--project=$ProjectId",
        "--min-instances=$($recommendations.MinInstances)",
        "--max-instances=$($recommendations.MaxInstances)",
        "--concurrency=$($recommendations.Concurrency)",
        "--cpu=$($recommendations.Cpu)",
        "--memory=$($recommendations.Memory)",
        "--quiet"
    )

    Write-Host "실행 명령:" -ForegroundColor Gray
    Write-Host "  gcloud $($updateArgs -join ' ')" -ForegroundColor DarkGray
    Write-Host ""

    $updateOutput = & gcloud $updateArgs 2>&1

    if ($LASTEXITCODE -ne 0) {
        throw "설정 업데이트 실패: $updateOutput"
    }

    Write-Host "✅ 설정 업데이트 완료!" -ForegroundColor Green
    Write-Host ""

    # 업데이트 후 상태 확인
    Write-Host "🔍 업데이트 후 상태 확인..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5

    $newDescribe = gcloud run services describe $ServiceName `
        --region=$Region `
        --project=$ProjectId `
        --format=json 2>&1 | ConvertFrom-Json

    $newMinInstances = $newDescribe.spec.template.metadata.annotations.'autoscaling.knative.dev/minScale'
    $newMaxInstances = $newDescribe.spec.template.metadata.annotations.'autoscaling.knative.dev/maxScale'
    $newConcurrency = $newDescribe.spec.template.spec.containerConcurrency

    Write-Host ""
    Write-Host "✅ 적용 확인" -ForegroundColor Cyan
    Write-Host "  - Min Instances: $newMinInstances" -ForegroundColor Green
    Write-Host "  - Max Instances: $newMaxInstances" -ForegroundColor Green
    Write-Host "  - Concurrency: $newConcurrency" -ForegroundColor Green
    Write-Host ""
}
catch {
    Write-Host "❌ 설정 적용 실패: $_" -ForegroundColor Red
    exit 1
}

# 예상 비용 영향
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "💰 예상 비용 영향" -ForegroundColor Yellow
Write-Host ""

if ($ServiceName -eq "ion-api") {
    Write-Host "  Main 서비스 (Min 2 instances):" -ForegroundColor Cyan
    Write-Host "    - 월 예상 비용: ~$50-100" -ForegroundColor Gray
    Write-Host "    - 항상 2개 인스턴스 유지로 즉시 응답" -ForegroundColor Gray
    Write-Host "    - 콜드 스타트 없음 → 사용자 경험 향상" -ForegroundColor Green
}
else {
    Write-Host "  Canary 서비스 (Min 0 instances):" -ForegroundColor Cyan
    Write-Host "    - 월 예상 비용: ~$10-20" -ForegroundColor Gray
    Write-Host "    - 유휴 시 비용 0원" -ForegroundColor Green
    Write-Host "    - 테스트 시에만 비용 발생" -ForegroundColor Gray
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "✅ 자동 스케일링 최적화 완료!" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
