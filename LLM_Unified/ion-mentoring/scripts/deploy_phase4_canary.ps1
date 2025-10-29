<#
.SYNOPSIS
    Phase 4 Canary Deployment Script for Ion Mentoring API

.DESCRIPTION
    5% 카나리 배포를 Google Cloud Run에 실행하는 배포 스크립트입니다.
    - Docker 이미지 빌드
    - Artifact Registry 푸시
    - Cloud Run 배포 (Legacy + Canary 서비스)
    - 환경 변수 및 Secret 설정
    - 배포 검증

.PARAMETER ProjectId
    Google Cloud 프로젝트 ID (기본값: 환경 변수 GCP_PROJECT_ID)

.PARAMETER Region
    Cloud Run 리전 (기본값: us-central1)

.PARAMETER ServiceAccountEmail
    Cloud Run 서비스 계정 이메일 (없으면 자동 생성)

.PARAMETER CanaryPercentage
    카나리 트래픽 비율 (기본값: 5)

.PARAMETER DryRun
    실제 배포 없이 설정만 확인 (기본값: $false)

.EXAMPLE
    .\deploy_phase4_canary.ps1 -ProjectId "ion-mentoring-prod" -DryRun $true
    
.EXAMPLE
    .\deploy_phase4_canary.ps1 -ProjectId "ion-mentoring-prod" -CanaryPercentage 5

.NOTES
    Author: GitHub Copilot
    Date: 2025-10-18
    Version: 1.0.0
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$ProjectId = $env:GCP_PROJECT_ID,

    [Parameter(Mandatory = $false)]
    [string]$Region = "us-central1",

    [Parameter(Mandatory = $false)]
    [string]$ServiceAccountEmail = "",

    [Parameter(Mandatory = $false)]
    [ValidateRange(1, 100)]
    [int]$CanaryPercentage = 5,

    [Parameter(Mandatory = $false)]
    [switch]$DryRun = $false
)

$ErrorActionPreference = "Stop"

# Force non-interactive mode for gcloud (auto-approve)
$env:CLOUDSDK_CORE_DISABLE_PROMPTS = '1'

# ============================================================================
# 설정 및 상수
# ============================================================================

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PROJECT_ROOT = Split-Path -Parent $SCRIPT_DIR
$TIMESTAMP = Get-Date -Format "yyyyMMdd-HHmmss"
$LOG_FILE = Join-Path $SCRIPT_DIR "logs\deploy_$TIMESTAMP.log"

# 서비스 이름
$SERVICE_LEGACY = "ion-api"
$SERVICE_CANARY = "ion-api-canary"

# Docker 이미지 설정
$ARTIFACT_REPO = "ion-api"
$IMAGE_TAG = "phase4-canary"
$MIN_INSTANCES = 1
# Cloud Run resource defaults (can be overridden if needed)
$MEMORY = "512Mi"
$CPU = "1"
$MAX_INSTANCES = 5

# ============================================================================
# 유틸리티 함수
# ============================================================================

function Invoke-ExternalSafe {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Command
    )
    # 외부 명령을 cmd.exe를 통해 실행하여 PowerShell NativeCommandError를 회피
    cmd /c $Command | Out-Null
    return $LASTEXITCODE
}

function Invoke-ExternalCapture {
    param(
        [Parameter(Mandatory = $true)][string]$Command
    )
    # 외부 명령을 안전하게 실행하고 표준 출력/에러를 파일로 캡처해 반환
    $tempFile = [System.IO.Path]::GetTempFileName()
    cmd /c "$Command 1> `"$tempFile`" 2>&1" | Out-Null
    $exit = $LASTEXITCODE
    $out = ""
    if (Test-Path $tempFile) {
        $out = Get-Content -Path $tempFile -Raw
        Remove-Item -Path $tempFile -Force -ErrorAction SilentlyContinue
    }
    return @{ ExitCode = $exit; Output = $out }
}

function Write-Log {
    param(
        [string]$Message,
        [ValidateSet("INFO", "WARN", "ERROR", "SUCCESS")]
        [string]$Level = "INFO"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    
    # 로그 파일에 기록
    if (-not (Test-Path (Split-Path $LOG_FILE))) {
        New-Item -ItemType Directory -Path (Split-Path $LOG_FILE) -Force | Out-Null
    }
    Add-Content -Path $LOG_FILE -Value $logMessage
    
    # 콘솔 출력 (색상)
    switch ($Level) {
        "INFO" { Write-Host $logMessage -ForegroundColor Cyan }
        "WARN" { Write-Host $logMessage -ForegroundColor Yellow }
        "ERROR" { Write-Host $logMessage -ForegroundColor Red }
        "SUCCESS" { Write-Host $logMessage -ForegroundColor Green }
    }
}

function Test-GcloudAuth {
    Write-Log "Checking gcloud authentication..." "INFO"
    
    try {
        $account = gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Log "Not authenticated. Please run: gcloud auth login" "ERROR"
            return $false
        }
        Write-Log "Authenticated as: $account" "SUCCESS"
        return $true
    }
    catch {
        Write-Log "gcloud command not found. Please install Google Cloud SDK." "ERROR"
        return $false
    }
}

function Test-ProjectExists {
    param([string]$ProjectId)
    
    Write-Log "Checking project: $ProjectId" "INFO"
    
    gcloud projects describe $ProjectId --format="value(projectId)" 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Log "Project $ProjectId not found or no access." "ERROR"
        return $false
    }
    
    Write-Log "Project verified: $ProjectId" "SUCCESS"
    return $true
}

function Enable-RequiredAPIs {
    param([string]$ProjectId)
    
    Write-Log "Enabling required APIs..." "INFO"
    
    $apis = @(
        "run.googleapis.com",
        "artifactregistry.googleapis.com",
        "secretmanager.googleapis.com",
        "aiplatform.googleapis.com",
        "cloudresourcemanager.googleapis.com",
        "iam.googleapis.com"
    )
    
    foreach ($api in $apis) {
        Write-Log "Enabling $api..." "INFO"
        gcloud services enable $api --project=$ProjectId --quiet 2>&1 | Out-Null
        
        if ($LASTEXITCODE -ne 0) {
            Write-Log "Failed to enable $api" "ERROR"
            return $false
        }
    }
    
    Write-Log "All APIs enabled successfully" "SUCCESS"
    return $true
}

function New-ServiceAccountIfNotExists {
    param(
        [string]$ProjectId,
        [string]$ServiceName
    )
    
    $saName = "$ServiceName-runner"
    $saEmail = "$saName@$ProjectId.iam.gserviceaccount.com"
    
    Write-Log "Checking service account: $saEmail" "INFO"

    $exit = Invoke-ExternalSafe "gcloud iam service-accounts describe $saEmail --project=$ProjectId --format=`"value(email)`""
    if ($exit -eq 0) {
        Write-Log "Service account already exists: $saEmail" "SUCCESS"
        return $saEmail
    }
    
    Write-Log "Creating service account: $saName" "INFO"
    $exit = Invoke-ExternalSafe "gcloud iam service-accounts create $saName --display-name=`"$ServiceName Cloud Run Service Account`" --project=$ProjectId --quiet"
    if ($exit -ne 0) {
        Write-Log "Failed to create service account" "ERROR"
        return $null
    }
    
    # 권한 부여
    Write-Log "Granting IAM roles..." "INFO"
    
    $roles = @(
        "roles/aiplatform.user",
        "roles/secretmanager.secretAccessor",
        "roles/logging.logWriter",
        "roles/cloudtrace.agent"
    )
    
    foreach ($role in $roles) {
        $exit = Invoke-ExternalSafe "gcloud projects add-iam-policy-binding $ProjectId --member=`"serviceAccount:$saEmail`" --role=$role --condition=None --quiet"
        if ($exit -ne 0) { Write-Log "Failed to grant role: $role" "ERROR" }
    }
    
    Write-Log "Service account created and configured: $saEmail" "SUCCESS"
    return $saEmail
}

function New-ArtifactRepositoryIfNotExists {
    param(
        [string]$ProjectId,
        [string]$Region,
        [string]$RepoName
    )
    
    Write-Log "Checking Artifact Registry repository: $RepoName" "INFO"

    $exit = Invoke-ExternalSafe "gcloud artifacts repositories describe $RepoName --location=$Region --project=$ProjectId --format=`"value(name)`""
    if ($exit -eq 0) {
        Write-Log "Repository already exists: $RepoName" "SUCCESS"
        return $true
    }
    
    Write-Log "Creating Artifact Registry repository: $RepoName" "INFO"
    $exit = Invoke-ExternalSafe "gcloud artifacts repositories create $RepoName --repository-format=docker --location=$Region --project=$ProjectId --description=`"Ion API Docker images for Phase 4 Canary Deployment`" --quiet"
    if ($exit -ne 0) {
        Write-Log "Failed to create repository" "ERROR"
        return $false
    }
    
    Write-Log "Repository created successfully: $RepoName" "SUCCESS"
    return $true
}

function New-DockerImage {
    param(
        [string]$ProjectId,
        [string]$Region,
        [string]$RepoName,
        [string]$ImageTag
    )
    
    $imageName = "$Region-docker.pkg.dev/$ProjectId/$RepoName/$SERVICE_CANARY`:$ImageTag"
    
    Write-Log "Building Docker image: $imageName" "INFO"
    Write-Log "Working directory: $PROJECT_ROOT" "INFO"
    
    # Dockerfile 확인
    $dockerfilePath = Join-Path $PROJECT_ROOT "Dockerfile"
    if (-not (Test-Path $dockerfilePath)) {
        Write-Log "Dockerfile not found: $dockerfilePath" "ERROR"
        return $null
    }
    
    # Docker 빌드 (안전 실행 + 로그 파일로 리디렉션)
    $buildCmd = "docker build -t `"$imageName`" -f `"$dockerfilePath`" `"$PROJECT_ROOT`" 1>> `"$LOG_FILE`" 2>>&1"
    $exit = Invoke-ExternalSafe $buildCmd
    if ($exit -ne 0) {
        Write-Log "Docker build failed" "ERROR"
        return $null
    }
    
    Write-Log "Docker image built successfully: $imageName" "SUCCESS"
    return $imageName
}

function Push-DockerImage {
    param([string]$ImageName)
    
    Write-Log "Pushing Docker image to Artifact Registry..." "INFO"
    
    # Docker 인증 설정
    $cfgCmd = "gcloud auth configure-docker `"$Region-docker.pkg.dev`" --quiet 1>> `"$LOG_FILE`" 2>>&1"
    $exit = Invoke-ExternalSafe $cfgCmd
    if ($exit -ne 0) {
        Write-Log "Failed to configure Docker auth for Artifact Registry" "ERROR"
        return $false
    }
    
    # 이미지 푸시
    $pushCmd = "docker push `"$ImageName`" 1>> `"$LOG_FILE`" 2>>&1"
    $exit = Invoke-ExternalSafe $pushCmd
    if ($exit -ne 0) {
        Write-Log "Docker push failed" "ERROR"
        return $false
    }
    
    Write-Log "Docker image pushed successfully" "SUCCESS"
    return $true
}

function Publish-CloudRunService {
    param(
        [string]$ProjectId,
        [string]$Region,
        [string]$ServiceName,
        [string]$ImageName,
        [string]$ServiceAccountEmail,
        [bool]$IsCanary = $false
    )
    
    Write-Log "Deploying Cloud Run service: $ServiceName" "INFO"

    # Vertex/GCP 환경변수 구성 (우선순위: 외부 ENV > 스크립트 인자/기본값)
    $vertexProjectId = $ProjectId
    if ($env:VERTEX_PROJECT_ID -and $env:VERTEX_PROJECT_ID.Trim()) { $vertexProjectId = $env:VERTEX_PROJECT_ID.Trim() }

    $vertexLocation = $Region
    if ($env:VERTEX_LOCATION -and $env:VERTEX_LOCATION.Trim()) { $vertexLocation = $env:VERTEX_LOCATION.Trim() }

    $vertexModel = "gemini-1.5-flash-002"
    if ($env:VERTEX_MODEL -and $env:VERTEX_MODEL.Trim()) { $vertexModel = $env:VERTEX_MODEL.Trim() }
    
    # 환경 변수 설정
    $envVars = @(
        "ENVIRONMENT=production",
        "PHASE4_ENABLED=true",
        "VERTEX_PROJECT_ID=$vertexProjectId",
        "VERTEX_LOCATION=$vertexLocation",
        "VERTEX_MODEL=$vertexModel",
        # 코드 경로 호환용 추가 키
        "GOOGLE_CLOUD_PROJECT=$ProjectId",
        "GCP_PROJECT_ID=$ProjectId",
        "GCP_LOCATION=$vertexLocation",
        "GOOGLE_CLOUD_LOCATION=$vertexLocation",
        "GEMINI_MODEL=$vertexModel"
    )
    
    if ($IsCanary) {
        $envVars += "DEPLOYMENT_VERSION=CANARY"
        $envVars += "CANARY_TRAFFIC_PERCENTAGE=$CanaryPercentage"
    }
    else {
        $envVars += "DEPLOYMENT_VERSION=LEGACY"
    }
    
    $envVarString = $envVars -join ","
    
    # Cloud Run 배포 (안전 실행 + 로그 파일 리디렉션)
    $deployCmd = "gcloud run deploy `"$ServiceName`" --image=`"$ImageName`" --region=`"$Region`" --platform=managed --allow-unauthenticated --set-env-vars=`"$envVarString`" --memory=`"$MEMORY`" --cpu=`"$CPU`" --max-instances=`"$MAX_INSTANCES`" --min-instances=`"$MIN_INSTANCES`" --service-account=`"$ServiceAccountEmail`" --project=`"$ProjectId`" --quiet 1>> `"$LOG_FILE`" 2>>&1"
    $exit = Invoke-ExternalSafe $deployCmd
    if ($exit -ne 0) {
        Write-Log "Cloud Run deployment failed: $ServiceName" "ERROR"
        return $null
    }
    
    # 서비스 URL 가져오기
    $descCmd = "gcloud run services describe `"$ServiceName`" --region=`"$Region`" --project=`"$ProjectId`" --format=`"value(status.url)`""
    $res = Invoke-ExternalCapture $descCmd
    if ($res.ExitCode -ne 0) {
        Write-Log "Failed to fetch service URL for $ServiceName" "ERROR"
        return $null
    }
    $serviceUrl = ($res.Output).Trim()
    
    Write-Log "Service deployed successfully: $serviceUrl" "SUCCESS"
    return $serviceUrl
}

function Test-ServiceHealth {
    param([string]$ServiceUrl)
    
    Write-Log "Testing service health: $ServiceUrl/health" "INFO"
    
    try {
        $response = Invoke-WebRequest -Uri "$ServiceUrl/health" -Method Get -TimeoutSec 30
        
        if ($response.StatusCode -eq 200) {
            Write-Log "Health check passed: $($response.Content)" "SUCCESS"
            return $true
        }
        else {
            Write-Log "Health check failed: Status $($response.StatusCode)" "ERROR"
            return $false
        }
    }
    catch {
        Write-Log "Health check failed: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Set-TrafficSplit {
    param(
        [string]$ProjectId,
        [string]$Region,
        [string]$LegacyService,
        [string]$CanaryService,
        [int]$CanaryPercent
    )
    
    $legacyPercent = 100 - $CanaryPercent
    
    Write-Log "Configuring traffic split: Legacy $legacyPercent% / Canary $CanaryPercent%" "INFO"
    
    # 참고: Cloud Run 자체는 단일 서비스 내 리비전 트래픽 분할을 지원합니다.
    # 멀티 서비스 트래픽 분할은 Load Balancer를 사용해야 합니다.
    # 현재는 카나리 서비스를 독립적으로 배포하고, 애플리케이션 레벨 라우팅을 사용합니다.
    
    Write-Log "NOTE: Traffic routing is managed by CanaryRouter in the application code." "WARN"
    Write-Log "Canary service deployed independently. Use Load Balancer for infrastructure-level routing." "WARN"
    
    return $true
}

# ============================================================================
# 메인 배포 로직
# ============================================================================

function Main {
    Write-Log "==================== Phase 4 Canary Deployment ====================" "INFO"
    Write-Log "Project ID: $ProjectId" "INFO"
    Write-Log "Region: $Region" "INFO"
    Write-Log "Canary Percentage: $CanaryPercentage%" "INFO"
    Write-Log "Dry Run: $DryRun" "INFO"
    Write-Log "====================================================================" "INFO"
    Write-Log "" "INFO"
    
    # 1. 사전 검사
    Write-Log "Step 1: Pre-deployment checks" "INFO"
    
    if (-not $ProjectId) {
        Write-Log "Project ID is required. Set GCP_PROJECT_ID environment variable or use -ProjectId parameter." "ERROR"
        exit 1
    }
    
    if (-not (Test-GcloudAuth)) {
        exit 1
    }
    
    if (-not (Test-ProjectExists -ProjectId $ProjectId)) {
        exit 1
    }
    
    # 2. API 활성화
    Write-Log "Step 2: Enable required APIs" "INFO"
    if (-not $DryRun) {
        if (-not (Enable-RequiredAPIs -ProjectId $ProjectId)) {
            exit 1
        }
    }
    else {
        Write-Log "[DRY RUN] Skipping API enablement" "WARN"
    }
    
    # 3. Service Account 생성
    Write-Log "Step 3: Setup Service Account" "INFO"
    if (-not $ServiceAccountEmail) {
        if ($DryRun) {
            $ServiceAccountEmail = "$SERVICE_CANARY-runner@$ProjectId.iam.gserviceaccount.com"
            Write-Log "[DRY RUN] Would ensure service account exists: $ServiceAccountEmail" "WARN"
            Write-Log "[DRY RUN] Would grant IAM roles: roles/aiplatform.user, roles/secretmanager.secretAccessor, roles/logging.logWriter, roles/cloudtrace.agent" "WARN"
        }
        else {
            $ServiceAccountEmail = New-ServiceAccountIfNotExists -ProjectId $ProjectId -ServiceName $SERVICE_CANARY
            if (-not $ServiceAccountEmail) {
                exit 1
            }
        }
    }
    else {
        Write-Log "Using provided service account: $ServiceAccountEmail" "INFO"
    }
    
    # 4. Artifact Registry 준비
    Write-Log "Step 4: Setup Artifact Registry" "INFO"
    if (-not $DryRun) {
        if (-not (New-ArtifactRepositoryIfNotExists -ProjectId $ProjectId -Region $Region -RepoName $ARTIFACT_REPO)) {
            exit 1
        }
    }
    else {
        Write-Log "[DRY RUN] Skipping Artifact Registry setup" "WARN"
    }
    
    # 5. Docker 이미지 빌드
    Write-Log "Step 5: Build Docker image" "INFO"
    if (-not $DryRun) {
        $imageName = New-DockerImage -ProjectId $ProjectId -Region $Region -RepoName $ARTIFACT_REPO -ImageTag $IMAGE_TAG
        if (-not $imageName) {
            exit 1
        }
    }
    else {
        $imageName = "$Region-docker.pkg.dev/$ProjectId/$ARTIFACT_REPO/$SERVICE_CANARY`:$IMAGE_TAG"
        Write-Log "[DRY RUN] Would build image: $imageName" "WARN"
    }
    
    # 6. Docker 이미지 푸시
    Write-Log "Step 6: Push Docker image" "INFO"
    if (-not $DryRun) {
        if (-not (Push-DockerImage -ImageName $imageName)) {
            exit 1
        }
    }
    else {
        Write-Log "[DRY RUN] Skipping Docker push" "WARN"
    }
    
    # 7. Canary 서비스 배포
    Write-Log "Step 7: Deploy Canary service" "INFO"
    if (-not $DryRun) {
        $canaryUrl = Publish-CloudRunService `
            -ProjectId $ProjectId `
            -Region $Region `
            -ServiceName $SERVICE_CANARY `
            -ImageName $imageName `
            -ServiceAccountEmail $ServiceAccountEmail `
            -IsCanary $true
        
        if (-not $canaryUrl) {
            exit 1
        }
    }
    else {
        $canaryUrl = "https://$SERVICE_CANARY-x4qvsargwa-uc.a.run.app"
        Write-Log "[DRY RUN] Would deploy to: $canaryUrl" "WARN"
    }
    
    # 8. 헬스 체크
    Write-Log "Step 8: Health check" "INFO"
    if (-not $DryRun) {
        Start-Sleep -Seconds 10  # 서비스 시작 대기
        
        if (-not (Test-ServiceHealth -ServiceUrl $canaryUrl)) {
            Write-Log "Canary service health check failed. Consider rollback." "ERROR"
            exit 1
        }
    }
    else {
        Write-Log "[DRY RUN] Skipping health check" "WARN"
    }
    
    # 9. 트래픽 분할 설정
    Write-Log "Step 9: Configure traffic split" "INFO"
    if (-not $DryRun) {
        Set-TrafficSplit `
            -ProjectId $ProjectId `
            -Region $Region `
            -LegacyService $SERVICE_LEGACY `
            -CanaryService $SERVICE_CANARY `
            -CanaryPercent $CanaryPercentage | Out-Null
    }
    else {
        Write-Log "[DRY RUN] Would set traffic: Legacy $(100 - $CanaryPercentage)% / Canary $CanaryPercentage%" "WARN"
    }
    
    # 10. 배포 완료
    Write-Log "" "INFO"
    Write-Log "====================================================================" "SUCCESS"
    Write-Log "Phase 4 Canary Deployment Completed Successfully!" "SUCCESS"
    Write-Log "====================================================================" "SUCCESS"
    Write-Log "" "INFO"
    Write-Log "Canary Service URL: $canaryUrl" "INFO"
    Write-Log "Traffic Split: Legacy $(100 - $CanaryPercentage)% / Canary $CanaryPercentage%" "INFO"
    Write-Log "Log File: $LOG_FILE" "INFO"
    Write-Log "" "INFO"
    Write-Log "Next Steps:" "INFO"
    Write-Log "1. Monitor metrics for 1 hour (error rate, latency)" "INFO"
    Write-Log "2. Check Sentry/Cloud Monitoring for alerts" "INFO"
    Write-Log "3. Validate SLO compliance (error rate < 0.5%, P95 < 10%)" "INFO"
    Write-Log "4. If successful, gradually increase canary percentage" "INFO"
    Write-Log "" "INFO"
    Write-Log "Rollback Command:" "INFO"
    Write-Log "  gcloud run services delete $SERVICE_CANARY --region=$Region --project=$ProjectId" "WARN"
    Write-Log "" "INFO"
}

# 스크립트 실행
Main
