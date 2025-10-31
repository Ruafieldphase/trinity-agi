#Requires -Version 5.1
<#
.SYNOPSIS
    Canary 서비스를 Main으로 승격시키는 스크립트

.DESCRIPTION
    검증된 Canary 버전을 Main 서비스에 배포합니다.
    - Canary의 현재 이미지를 가져옴
    - Main 서비스를 해당 이미지로 업데이트
    - 헬스체크 수행
    - 롤백 정보 저장

.PARAMETER ProjectId
    GCP 프로젝트 ID (기본값: naeda-genesis)

.PARAMETER Region
    Cloud Run 리전 (기본값: us-central1)

.PARAMETER DryRun
    실제 배포 없이 계획만 출력

.PARAMETER SkipHealthCheck
    배포 후 헬스체크 건너뛰기

.EXAMPLE
    .\promote_canary_to_main.ps1
    기본 설정으로 Canary를 Main으로 승격

.EXAMPLE
    .\promote_canary_to_main.ps1 -DryRun
    실행 계획만 출력
#>

param(
    [string]$ProjectId = "naeda-genesis",
    [string]$Region = "us-central1",
    [switch]$DryRun,
    [switch]$SkipHealthCheck
)

$ErrorActionPreference = "Stop"

# 색상 출력 함수
function Write-ColorHost {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Write-Header {
    param([string]$Title)
    Write-Host ""
    Write-ColorHost "==========================================" "Cyan"
    Write-ColorHost "  $Title" "Yellow"
    Write-ColorHost "==========================================" "Cyan"
    Write-Host ""
}

function Write-Step {
    param([string]$Message)
    Write-ColorHost "▶ $Message" "Green"
}

function Write-Info {
    param([string]$Message)
    Write-ColorHost "  $Message" "Gray"
}

function Write-Success {
    param([string]$Message)
    Write-ColorHost "[OK] $Message" "Green"
}

function Write-Warning {
    param([string]$Message)
    Write-ColorHost "[WARN]  $Message" "Yellow"
}

function Write-Error {
    param([string]$Message)
    Write-ColorHost "[ERROR] $Message" "Red"
}

# 시작
Write-Header "Canary → Main 승격 스크립트"

if ($DryRun) {
    Write-Warning "DRY RUN 모드 - 실제 배포는 수행되지 않습니다."
    Write-Host ""
}

# Step 1: gcloud 인증 확인
Write-Step "Step 1: gcloud 인증 확인"
try {
    $account = gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>$null
    if (-not $account) {
        Write-Error "gcloud 인증이 필요합니다."
        Write-Info "실행: gcloud auth login"
        exit 1
    }
    Write-Info "인증된 계정: $account"
    Write-Success "인증 확인 완료"
} catch {
    Write-Error "gcloud CLI를 찾을 수 없습니다."
    exit 1
}

# Step 2: Canary 서비스 정보 가져오기
Write-Step "Step 2: Canary 서비스 정보 조회"
try {
    $canaryInfo = gcloud run services describe ion-api-canary `
        --region=$Region `
        --project=$ProjectId `
        --format=json 2>$null | ConvertFrom-Json

    $canaryImage = $canaryInfo.spec.template.spec.containers[0].image
    $canaryRevision = $canaryInfo.status.latestReadyRevisionName
    
    Write-Info "Canary 이미지: $canaryImage"
    Write-Info "Canary 리비전: $canaryRevision"
    Write-Success "Canary 정보 조회 완료"
} catch {
    Write-Error "Canary 서비스 정보를 가져올 수 없습니다."
    Write-Info $_.Exception.Message
    exit 1
}

# Step 3: Main 서비스 현재 상태 저장 (롤백용)
Write-Step "Step 3: Main 서비스 현재 상태 저장"
try {
    $mainInfo = gcloud run services describe ion-api `
        --region=$Region `
        --project=$ProjectId `
        --format=json 2>$null | ConvertFrom-Json

    $mainImage = $mainInfo.spec.template.spec.containers[0].image
    $mainRevision = $mainInfo.status.latestReadyRevisionName
    
    Write-Info "Main 현재 이미지: $mainImage"
    Write-Info "Main 현재 리비전: $mainRevision"
    
    # 롤백 정보 저장
    $rollbackInfo = @{
        timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        previous_image = $mainImage
        previous_revision = $mainRevision
        new_image = $canaryImage
        new_revision = "pending"
    }
    
    $rollbackFile = ".\outputs\rollback_info_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
    $rollbackInfo | ConvertTo-Json | Set-Content $rollbackFile
    Write-Info "롤백 정보 저장: $rollbackFile"
    Write-Success "현재 상태 저장 완료"
} catch {
    Write-Error "Main 서비스 정보를 가져올 수 없습니다."
    exit 1
}

# Step 4: Main 서비스 업데이트
Write-Step "Step 4: Main 서비스에 Canary 이미지 배포"

if ($DryRun) {
    Write-Warning "DRY RUN: 다음 명령어가 실행될 예정입니다:"
    Write-Info "gcloud run deploy ion-api \"
    Write-Info "  --image=$canaryImage \"
    Write-Info "  --region=$Region \"
    Write-Info "  --project=$ProjectId \"
    Write-Info "  --platform=managed \"
    Write-Info "  --allow-unauthenticated \"
    Write-Info "  --quiet"
} else {
    Write-Info "배포 시작..."
    try {
        $deployOutput = gcloud run deploy ion-api `
            --image=$canaryImage `
            --region=$Region `
            --project=$ProjectId `
            --platform=managed `
            --allow-unauthenticated `
            --quiet 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Main 서비스 배포 완료"
        } else {
            Write-Error "배포 실패"
            Write-Info $deployOutput
            exit 1
        }
    } catch {
        Write-Error "배포 중 오류 발생"
        Write-Info $_.Exception.Message
        exit 1
    }
}

# Step 5: 헬스체크
if (-not $SkipHealthCheck -and -not $DryRun) {
    Write-Step "Step 5: 헬스체크 수행"
    
    Start-Sleep -Seconds 5
    
    try {
        $healthUrl = "https://ion-api-64076350717.us-central1.run.app/health"
        $startTime = Get-Date
        $response = Invoke-RestMethod -Uri $healthUrl -Method GET -TimeoutSec 10
        $endTime = Get-Date
        $responseTime = ($endTime - $startTime).TotalMilliseconds
        
        Write-Info "응답시간: $([math]::Round($responseTime, 2))ms"
        Write-Info "상태: $($response.status)"
        Write-Info "버전: $($response.version)"
        
        if ($response.status -eq "healthy") {
            Write-Success "헬스체크 통과"
        } else {
            Write-Warning "헬스체크 경고: 상태가 healthy가 아닙니다."
        }
    } catch {
        Write-Error "헬스체크 실패"
        Write-Info $_.Exception.Message
        Write-Warning "롤백이 필요할 수 있습니다: $rollbackFile"
        exit 1
    }
}

# 완료
Write-Header "승격 완료"

Write-Success "Canary v2.1.0이 Main으로 승격되었습니다!"
Write-Host ""
Write-Info "Main URL: https://ion-api-64076350717.us-central1.run.app"
Write-Info "롤백 정보: $rollbackFile"
Write-Host ""

if (-not $DryRun) {
    Write-ColorHost "다음 단계:" "Cyan"
    Write-Info "1. 모니터링 대시보드에서 Main 서비스 확인"
    Write-Info "2. 필요시 Canary 서비스 리셋 (다음 배포 준비)"
    Write-Info "3. 롤백 필요시 롤백 정보 파일 참조"
}

Write-Host ""
