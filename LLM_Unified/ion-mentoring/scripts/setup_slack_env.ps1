#Requires -Version 5.1
<#
.SYNOPSIS
    Slack 환경 변수를 대화형으로 설정합니다.

.DESCRIPTION
    Slack Bot Token과 Alert Channel을 사용자로부터 입력받아 
    영구 환경 변수로 설정합니다. 기존 값이 있으면 표시하고 
    변경 여부를 묻습니다.

.PARAMETER BotToken
    Slack Bot Token (xoxb-로 시작). 지정하지 않으면 대화형으로 입력받습니다.

.PARAMETER AlertChannel
    배포 알림을 받을 Slack 채널 (예: #deployments). 지정하지 않으면 대화형으로 입력받습니다.

.PARAMETER Verify
    설정 후 검증만 수행합니다.

.EXAMPLE
    .\setup_slack_env.ps1
    대화형으로 모든 환경 변수 설정

.EXAMPLE
    .\setup_slack_env.ps1 -BotToken "xoxb-123456" -AlertChannel "#deployments"
    명령줄에서 직접 설정

.EXAMPLE
    .\setup_slack_env.ps1 -Verify
    현재 설정 확인
#>

[CmdletBinding()]
param(
    [string]$BotToken,
    [string]$AlertChannel,
    [switch]$Verify
)

$ErrorActionPreference = "Stop"

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Get-EnvironmentVariable {
    param([string]$Name)
    return [Environment]::GetEnvironmentVariable($Name, "User")
}

function Set-EnvironmentVariableUser {
    param(
        [string]$Name,
        [string]$Value
    )
    [Environment]::SetEnvironmentVariable($Name, $Value, "User")
    # 현재 세션에도 적용
    Set-Item -Path "env:$Name" -Value $Value
}

function Test-SlackToken {
    param([string]$Token)
    
    if ([string]::IsNullOrWhiteSpace($Token)) {
        return $false
    }
    
    # xoxb- 또는 xoxp-로 시작하는지 확인
    if ($Token -notmatch '^xox[bp]-') {
        Write-ColorOutput "⚠️  경고: Slack Token은 'xoxb-' 또는 'xoxp-'로 시작해야 합니다." "Yellow"
        return $false
    }
    
    return $true
}

function Test-SlackChannel {
    param([string]$Channel)
    
    if ([string]::IsNullOrWhiteSpace($Channel)) {
        return $false
    }
    
    # #으로 시작하는지 확인
    if ($Channel -notmatch '^#') {
        Write-ColorOutput "⚠️  경고: Slack 채널은 '#'으로 시작해야 합니다 (예: #deployments)." "Yellow"
        return $false
    }
    
    return $true
}

# 배너 출력
Write-Host ""
Write-ColorOutput "╔════════════════════════════════════════════════════════════╗" "Cyan"
Write-ColorOutput "║     Slack 환경 변수 설정 도구                              ║" "Cyan"
Write-ColorOutput "╚════════════════════════════════════════════════════════════╝" "Cyan"
Write-Host ""

# 검증 모드
if ($Verify) {
    Write-ColorOutput "📋 현재 Slack 환경 변수 설정:" "Green"
    Write-Host ""
    
    $currentToken = Get-EnvironmentVariable "SLACK_BOT_TOKEN"
    $currentChannel = Get-EnvironmentVariable "SLACK_ALERT_CHANNEL"
    
    if ($currentToken) {
        $maskedToken = $currentToken.Substring(0, [Math]::Min(10, $currentToken.Length)) + "..." + 
        $currentToken.Substring([Math]::Max(0, $currentToken.Length - 4))
        Write-ColorOutput "  ✅ SLACK_BOT_TOKEN: $maskedToken" "Green"
    }
    else {
        Write-ColorOutput "  ❌ SLACK_BOT_TOKEN: (설정되지 않음)" "Red"
    }
    
    if ($currentChannel) {
        Write-ColorOutput "  ✅ SLACK_ALERT_CHANNEL: $currentChannel" "Green"
    }
    else {
        Write-ColorOutput "  ⚠️  SLACK_ALERT_CHANNEL: (설정되지 않음)" "Yellow"
        Write-ColorOutput "     → 배포 알림을 받으려면 이 값을 설정하세요." "Gray"
    }
    
    Write-Host ""
    
    if ($currentToken) {
        Write-ColorOutput "✅ Slack 환경 변수가 설정되어 있습니다!" "Green"
    }
    else {
        Write-ColorOutput "❌ SLACK_BOT_TOKEN이 설정되지 않았습니다." "Red"
        Write-ColorOutput "   실행하세요: .\setup_slack_env.ps1" "Yellow"
    }
    
    exit 0
}

# 현재 설정 표시
Write-ColorOutput "📋 현재 설정 확인 중..." "Cyan"
Write-Host ""

$currentToken = Get-EnvironmentVariable "SLACK_BOT_TOKEN"
$currentChannel = Get-EnvironmentVariable "SLACK_ALERT_CHANNEL"

if ($currentToken) {
    $maskedToken = $currentToken.Substring(0, [Math]::Min(10, $currentToken.Length)) + "..."
    Write-ColorOutput "  현재 SLACK_BOT_TOKEN: $maskedToken (설정됨)" "Gray"
}
else {
    Write-ColorOutput "  현재 SLACK_BOT_TOKEN: (없음)" "Gray"
}

if ($currentChannel) {
    Write-ColorOutput "  현재 SLACK_ALERT_CHANNEL: $currentChannel" "Gray"
}
else {
    Write-ColorOutput "  현재 SLACK_ALERT_CHANNEL: (없음)" "Gray"
}

Write-Host ""

# Bot Token 설정
if (-not $BotToken) {
    Write-ColorOutput "🔑 Slack Bot Token 설정" "Yellow"
    Write-Host ""
    Write-Host "  1. https://api.slack.com/apps 접속"
    Write-Host "  2. 앱 선택 → OAuth & Permissions"
    Write-Host "  3. 'Bot User OAuth Token' 복사 (xoxb-로 시작)"
    Write-Host ""
    
    if ($currentToken) {
        $response = Read-Host "기존 토큰이 있습니다. 변경하시겠습니까? (y/N)"
        if ($response -notmatch '^[yY]') {
            Write-ColorOutput "  → 기존 토큰 유지" "Green"
            $BotToken = $currentToken
        }
        else {
            $BotToken = Read-Host "새 Bot Token 입력"
        }
    }
    else {
        $BotToken = Read-Host "Bot Token 입력 (xoxb-로 시작)"
    }
}

# Bot Token 검증
if (-not (Test-SlackToken $BotToken)) {
    Write-ColorOutput "❌ 유효하지 않은 Slack Bot Token입니다." "Red"
    exit 1
}

# Alert Channel 설정
if (-not $AlertChannel) {
    Write-Host ""
    Write-ColorOutput "📢 배포 알림 채널 설정 (선택 사항)" "Yellow"
    Write-Host ""
    Write-Host "  배포 진행 상황을 Slack 채널로 실시간 알림받을 수 있습니다."
    Write-Host "  예: #deployments, #ops, #engineering"
    Write-Host ""
    
    if ($currentChannel) {
        $response = Read-Host "기존 채널이 있습니다 ($currentChannel). 변경하시겠습니까? (y/N)"
        if ($response -notmatch '^[yY]') {
            Write-ColorOutput "  → 기존 채널 유지" "Green"
            $AlertChannel = $currentChannel
        }
        else {
            $AlertChannel = Read-Host "새 Alert Channel 입력 (예: #deployments, 공백=건너뛰기)"
        }
    }
    else {
        $AlertChannel = Read-Host "Alert Channel 입력 (예: #deployments, 공백=건너뛰기)"
    }
}

# 환경 변수 설정
Write-Host ""
Write-ColorOutput "💾 환경 변수 저장 중..." "Cyan"

try {
    # Bot Token 저장
    Set-EnvironmentVariableUser "SLACK_BOT_TOKEN" $BotToken
    Write-ColorOutput "  ✅ SLACK_BOT_TOKEN 저장 완료" "Green"
    
    # Alert Channel 저장 (값이 있을 때만)
    if (-not [string]::IsNullOrWhiteSpace($AlertChannel)) {
        if (Test-SlackChannel $AlertChannel) {
            Set-EnvironmentVariableUser "SLACK_ALERT_CHANNEL" $AlertChannel
            Write-ColorOutput "  ✅ SLACK_ALERT_CHANNEL 저장 완료: $AlertChannel" "Green"
        }
        else {
            Write-ColorOutput "  ⚠️  SLACK_ALERT_CHANNEL 형식이 올바르지 않아 건너뜁니다." "Yellow"
        }
    }
    else {
        Write-ColorOutput "  ⚠️  SLACK_ALERT_CHANNEL 건너뜀 (배포 알림 비활성화)" "Yellow"
    }
    
    Write-Host ""
    Write-ColorOutput "╔════════════════════════════════════════════════════════════╗" "Green"
    Write-ColorOutput "║  ✅ Slack 환경 변수 설정 완료!                            ║" "Green"
    Write-ColorOutput "╚════════════════════════════════════════════════════════════╝" "Green"
    Write-Host ""
    
    Write-ColorOutput "📝 다음 단계:" "Cyan"
    Write-Host ""
    Write-Host "  1. PowerShell 재시작 (또는 새 터미널 열기)"
    Write-Host "  2. 환경 변수 확인:"
    Write-Host "     `$env:SLACK_BOT_TOKEN"
    Write-Host "     `$env:SLACK_ALERT_CHANNEL"
    Write-Host ""
    Write-Host "  3. Slack 봇 시작:"
    Write-Host "     cd D:\nas_backup\LLM_Unified\ion-mentoring"
    Write-Host "     .\scripts\start_gitco_bot.ps1"
    Write-Host ""
    
    if ($AlertChannel) {
        Write-Host "  4. 배포 알림 테스트:"
        Write-Host "     .\scripts\test_slack_notifications.ps1"
        Write-Host ""
    }
    
    Write-ColorOutput "💡 팁: 설정 확인하려면 실행하세요:" "Yellow"
    Write-Host "   .\setup_slack_env.ps1 -Verify"
    Write-Host ""
    
}
catch {
    Write-ColorOutput "❌ 환경 변수 설정 실패: $_" "Red"
    exit 1
}
