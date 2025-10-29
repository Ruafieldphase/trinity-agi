#Requires -Version 5.1
<#
.SYNOPSIS
    Slack 알림 시스템을 테스트합니다.

.DESCRIPTION
    SlackNotifications.ps1 모듈의 모든 알림 함수를 테스트하여
    Slack 연동이 올바르게 작동하는지 확인합니다.

.PARAMETER TestType
    테스트할 알림 타입: all, deployment, dashboard, monitoring
    기본값: all

.PARAMETER Channel
    테스트 메시지를 보낼 채널 (기본값: SLACK_ALERT_CHANNEL)

.EXAMPLE
    .\test_slack_notifications.ps1
    모든 알림 타입 테스트

.EXAMPLE
    .\test_slack_notifications.ps1 -TestType deployment
    배포 알림만 테스트

.EXAMPLE
    .\test_slack_notifications.ps1 -Channel "#test-channel"
    특정 채널로 테스트
#>

[CmdletBinding()]
param(
    [ValidateSet("all", "deployment", "dashboard", "monitoring")]
    [string]$TestType = "all",
    
    [string]$Channel,
    
    [switch]$AllowSkip = $true
)

$ErrorActionPreference = "Stop"

# 색상 출력 함수
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

# Slack 모듈 로드
$SlackModulePath = Join-Path $PSScriptRoot "SlackNotifications.ps1"
if (-not (Test-Path $SlackModulePath)) {
    Write-ColorOutput "❌ Slack 알림 모듈을 찾을 수 없습니다: $SlackModulePath" "Red"
    exit 1
}

Write-ColorOutput "📦 Slack 알림 모듈 로딩..." "Cyan"
. $SlackModulePath

# 대시보드 스크립트 경로
$DashboardScriptPath = Join-Path $PSScriptRoot "send_deployment_dashboard.ps1"

# 배너
Write-Host ""
Write-ColorOutput "╔════════════════════════════════════════════════════════════╗" "Cyan"
Write-ColorOutput "║     Slack 알림 시스템 테스트                               ║" "Cyan"
Write-ColorOutput "╚════════════════════════════════════════════════════════════╝" "Cyan"
Write-Host ""

# 환경 변수 확인
Write-ColorOutput "🔍 환경 변수 확인 중..." "Cyan"
$slackConfig = Get-SlackConfig

if (-not $slackConfig.Token) {
    Write-ColorOutput "❌ SLACK_BOT_TOKEN이 설정되지 않았습니다." "Red"
    Write-Host ""
    Write-Host "실행하세요:"
    Write-Host "  .\setup_slack_env.ps1"
    Write-Host ""
    if ($AllowSkip) {
        Write-ColorOutput "ℹ️  토큰 미설정 환경에서는 테스트를 건너뜁니다 (AllowSkip)." "Yellow"
        exit 0
    }
    else {
        exit 1
    }
}

# 비대화형 환경에서의 안전한 기본값 처리: 채널 미설정 시 프롬프트 대신 합리적 기본값 사용
if (-not $slackConfig.Channel -and -not $Channel) {
    $Channel = if ($env:SLACK_FALLBACK_CHANNEL) { $env:SLACK_FALLBACK_CHANNEL } else { "#deployments" }
    Write-ColorOutput "⚠️  SLACK_ALERT_CHANNEL이 설정되지 않아 기본 채널을 사용합니다: $Channel" "Yellow"
}

$targetChannel = if ($Channel) { $Channel } else { $slackConfig.Channel }

Write-ColorOutput "  ✅ Bot Token: $(($slackConfig.Token).Substring(0, 10))..." "Green"
Write-ColorOutput "  ✅ 대상 채널: $targetChannel" "Green"
Write-Host ""

# 테스트 카운터
$script:testCount = 0
$script:successCount = 0
$script:failCount = 0

function Test-Notification {
    param(
        [string]$Name,
        [scriptblock]$TestBlock
    )
    
    $script:testCount++
    Write-ColorOutput "[$script:testCount] 테스트: $Name" "Cyan"
    
    try {
        & $TestBlock
        $script:successCount++
        Write-ColorOutput "  ✅ 성공" "Green"
        Start-Sleep -Seconds 2
    }
    catch {
        $script:failCount++
        Write-ColorOutput "  ❌ 실패: $_" "Red"
    }
    
    Write-Host ""
}

# 테스트 시작
$startTime = Get-Date
Write-ColorOutput "🚀 테스트 시작: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" "Yellow"
Write-Host ""

# 1. 배포 알림 테스트
if ($TestType -eq "all" -or $TestType -eq "deployment") {
    Write-ColorOutput "═══ 배포 알림 테스트 ═══" "Magenta"
    Write-Host ""
    
    Test-Notification "배포 시작 알림 (5%)" {
        Send-DeploymentStartAlert -Percentage 5 -Version "test-v1.0.0" -Channel $targetChannel
    }
    
    Test-Notification "배포 진행 알림 (deploying)" {
        Send-DeploymentProgressAlert -Percentage 25 -Stage "deploying" -Details "Docker 이미지 빌드 중..." -Channel $targetChannel
    }
    
    Test-Notification "배포 진행 알림 (validating)" {
        Send-DeploymentProgressAlert -Percentage 50 -Stage "validating" -Details "헬스 체크 진행 중..." -Channel $targetChannel
    }
    
    Test-Notification "배포 진행 알림 (monitoring)" {
        Send-DeploymentProgressAlert -Percentage 50 -Stage "monitoring" -Details "트래픽 모니터링 중..." -Channel $targetChannel
    }
    
    Test-Notification "배포 완료 알림" {
        Send-DeploymentCompleteAlert -Percentage 100 -Duration "15분 30초" -Channel $targetChannel
    }
    
    Test-Notification "배포 실패 알림" {
        Send-DeploymentFailureAlert -Percentage 50 -Error "헬스 체크 실패 - 타임아웃 (30초)" -Channel $targetChannel
    }
}

# 2. 대시보드 테스트
if ($TestType -eq "all" -or $TestType -eq "dashboard") {
    Write-ColorOutput "═══ 대시보드 테스트 ═══" "Magenta"
    Write-Host ""
    
    if (-not (Test-Path $DashboardScriptPath)) {
        Write-ColorOutput "⚠️  대시보드 스크립트를 찾을 수 없습니다: $DashboardScriptPath" "Yellow"
    }
    else {
        Test-Notification "대시보드 - 배포 중 (25%)" {
            & $DashboardScriptPath `
                -Phase 25 `
                -Status deploying `
                -DeploymentStartTime (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') `
                -Channel $targetChannel
        }
        
        Test-Notification "대시보드 - 검증 중 (50%)" {
            & $DashboardScriptPath `
                -Phase 50 `
                -Status validating `
                -DeploymentStartTime ((Get-Date).AddMinutes(-5) | Get-Date -Format 'yyyy-MM-dd HH:mm:ss') `
                -Metrics @{
                "응답 시간" = "45ms"
                "상태 코드" = "200"
            } `
                -Channel $targetChannel
        }
        
        Test-Notification "대시보드 - 모니터링 중 (75%)" {
            & $DashboardScriptPath `
                -Phase 75 `
                -Status monitoring `
                -DeploymentStartTime ((Get-Date).AddMinutes(-10) | Get-Date -Format 'yyyy-MM-dd HH:mm:ss') `
                -MonitoringEndTime ((Get-Date).AddMinutes(50) | Get-Date -Format 'yyyy-MM-dd HH:mm:ss') `
                -Metrics @{
                "응답 시간"  = "42ms"
                "에러율"    = "0.1%"
                "성공률"    = "99.9%"
                "활성 사용자" = "1,234"
            } `
                -Channel $targetChannel
        }
        
        Test-Notification "대시보드 - 완료 (100%)" {
            & $DashboardScriptPath `
                -Phase 100 `
                -Status completed `
                -DeploymentStartTime ((Get-Date).AddMinutes(-15) | Get-Date -Format 'yyyy-MM-dd HH:mm:ss') `
                -Metrics @{
                "배포 시간"       = "15분 30초"
                "Gateway URL" = "https://ion-gateway.run.app"
                "트래픽 분할"      = "Legacy 0% / Canary 100%"
            } `
                -Channel $targetChannel
        }
        
        Test-Notification "대시보드 - 실패" {
            & $DashboardScriptPath `
                -Phase 50 `
                -Status failed `
                -DeploymentStartTime ((Get-Date).AddMinutes(-5) | Get-Date -Format 'yyyy-MM-dd HH:mm:ss') `
                -Metrics @{
                "에러"    = "헬스 체크 타임아웃"
                "응답 코드" = "0"
            } `
                -Channel $targetChannel
        }
    }
}

# 3. 모니터링 알림 테스트
if ($TestType -eq "all" -or $TestType -eq "monitoring") {
    Write-ColorOutput "═══ 모니터링 알림 테스트 ═══" "Magenta"
    Write-Host ""
    
    Test-Notification "모니터링 알림 - INFO" {
        Send-MonitoringAlert `
            -Title "시스템 정상" `
            -Message "모든 서비스가 정상 작동 중입니다." `
            -Severity "info" `
            -Channel $targetChannel
    }
    
    Test-Notification "모니터링 알림 - WARNING" {
        Send-MonitoringAlert `
            -Title "레이턴시 증가 감지" `
            -Message "P95 레이턴시가 10% 증가했습니다. 모니터링을 계속합니다." `
            -Severity "warning" `
            -Channel $targetChannel
    }
    
    Test-Notification "모니터링 알림 - ERROR" {
        Send-MonitoringAlert `
            -Title "에러율 임계값 초과" `
            -Message "에러율이 0.5%를 초과했습니다 (현재: 0.8%). 롤백을 고려하세요." `
            -Severity "error" `
            -Channel $targetChannel
    }
    
    Test-Notification "모니터링 알림 - CRITICAL" {
        Send-MonitoringAlert `
            -Title "서비스 다운 감지" `
            -Message "Canary 서비스가 응답하지 않습니다. 즉시 확인 필요!" `
            -Severity "critical" `
            -Channel $targetChannel
    }
}

# 결과 요약
$endTime = Get-Date
$duration = $endTime - $startTime

Write-Host ""
Write-ColorOutput "╔════════════════════════════════════════════════════════════╗" "Cyan"
Write-ColorOutput "║     테스트 결과 요약                                       ║" "Cyan"
Write-ColorOutput "╚════════════════════════════════════════════════════════════╝" "Cyan"
Write-Host ""

Write-ColorOutput "총 테스트: $script:testCount" "White"
Write-ColorOutput "성공: $script:successCount" "Green"
if ($script:failCount -gt 0) {
    Write-ColorOutput "실패: $script:failCount" "Red"
}
Write-ColorOutput "소요 시간: $([Math]::Round($duration.TotalSeconds, 1))초" "Gray"
Write-Host ""

if ($script:failCount -eq 0) {
    Write-ColorOutput "✅ 모든 테스트가 성공했습니다!" "Green"
    Write-Host ""
    Write-Host "이제 Slack 채널 ($targetChannel)에서 테스트 메시지를 확인하세요."
    Write-Host ""
    exit 0
}
else {
    Write-ColorOutput "⚠️  일부 테스트가 실패했습니다." "Yellow"
    Write-Host ""
    Write-Host "문제 해결:"
    Write-Host "  1. Slack Bot Token이 유효한지 확인"
    Write-Host "  2. Bot이 채널에 초대되었는지 확인 (/invite @Gitco)"
    Write-Host "  3. Bot 권한 확인 (chat:write, chat:write.public)"
    Write-Host ""
    exit 1
}
