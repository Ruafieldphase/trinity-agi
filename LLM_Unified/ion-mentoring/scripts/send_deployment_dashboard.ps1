#Requires -Version 5.1
<#
.SYNOPSIS
    Slack에 배포 대시보드 메시지를 생성/업데이트합니다.

.DESCRIPTION
    현재 배포 상태를 시각적으로 보여주는 대시보드를 Slack에 표시합니다.
    Block Kit을 사용하여 진행 상황, 메트릭, 다음 단계 등을 표시합니다.

.PARAMETER Phase
    현재 배포 단계 (5, 10, 25, 50, 100)

.PARAMETER Status
    배포 상태 (deploying, monitoring, validating, completed, failed)

.PARAMETER Metrics
    배포 메트릭 해시테이블 (error_rate, latency, success_rate 등)

.PARAMETER Channel
    Slack 채널 ID (선택)

.EXAMPLE
    .\send_deployment_dashboard.ps1 -Phase 50 -Status monitoring -Metrics @{error_rate="0.1%"; latency="45ms"}
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet(5, 10, 25, 50, 100)]
    [int]$Phase,
    
    [Parameter(Mandatory = $true)]
    [ValidateSet("deploying", "monitoring", "validating", "completed", "failed")]
    [string]$Status,
    
    [hashtable]$Metrics = @{},
    
    [string]$Channel,
    
    [string]$MonitoringEndTime = "",
    
    [string]$DeploymentStartTime = ""
)

$ErrorActionPreference = "Stop"

# Slack 알림 모듈 로드
$SlackModulePath = Join-Path $PSScriptRoot "SlackNotifications.ps1"
if (-not (Test-Path $SlackModulePath)) {
    Write-Error "Slack 알림 모듈을 찾을 수 없습니다: $SlackModulePath"
    exit 1
}

. $SlackModulePath

# 상태별 이모지 및 색상
$statusInfo = switch ($Status) {
    "deploying" { @{ emoji = "🔄"; text = "배포 중"; color = "#3498db" } }
    "monitoring" { @{ emoji = "👀"; text = "모니터링"; color = "#f39c12" } }
    "validating" { @{ emoji = "✔️"; text = "검증 중"; color = "#9b59b6" } }
    "completed" { @{ emoji = "✅"; text = "완료"; color = "#2ecc71" } }
    "failed" { @{ emoji = "❌"; text = "실패"; color = "#e74c3c" } }
}

# 진행 바 생성
function Get-ProgressBar {
    param([int]$Percentage)
    
    $filled = [math]::Floor($Percentage / 10)
    $empty = 10 - $filled
    
    $bar = "█" * $filled + "░" * $empty
    return "$bar $Percentage%"
}

# 메트릭 필드 생성
$metricFields = @()

if ($Metrics.Count -gt 0) {
    foreach ($key in $Metrics.Keys) {
        $metricFields += @{
            type = "mrkdwn"
            text = "*${key}:*`n$($Metrics[$key])"
        }
    }
}

# 기본 메트릭이 없으면 플레이스홀더 추가
if ($metricFields.Count -eq 0) {
    $metricFields = @(
        @{
            type = "mrkdwn"
            text = "*Error Rate:*`n측정 중..."
        },
        @{
            type = "mrkdwn"
            text = "*Latency (P95):*`n측정 중..."
        },
        @{
            type = "mrkdwn"
            text = "*Success Rate:*`n측정 중..."
        },
        @{
            type = "mrkdwn"
            text = "*Active Users:*`n측정 중..."
        }
    )
}

# Block Kit 메시지 구성
$blocks = @(
    @{
        type = "header"
        text = @{
            type  = "plain_text"
            text  = "$($statusInfo.emoji) 카나리 배포 대시보드"
            emoji = $true
        }
    },
    @{
        type   = "section"
        fields = @(
            @{
                type = "mrkdwn"
                text = "*배포 단계:*`n$Phase%"
            },
            @{
                type = "mrkdwn"
                text = "*상태:*`n$($statusInfo.text)"
            }
        )
    },
    @{
        type = "section"
        text = @{
            type = "mrkdwn"
            text = "*진행률:*`n``````n$(Get-ProgressBar -Percentage $Phase)`n```````"
        }
    }
    @{
        type = "divider"
    }
    @{
        type = "section"
        text = @{
            type = "mrkdwn"
            text = "*📊 실시간 메트릭*"
        }
    }
    @{
        type = "section"
        fields = $metricFields
    }
)

# 타임라인 추가
if ($DeploymentStartTime -or $MonitoringEndTime) {
    $timelineFields = @()
    
    if ($DeploymentStartTime) {
        $timelineFields += @{
            type = "mrkdwn"
            text = "*배포 시작:*`n$DeploymentStartTime"
        }
    }
    
    if ($MonitoringEndTime) {
        $timelineFields += @{
            type = "mrkdwn"
            text = "*모니터링 종료:*`n$MonitoringEndTime"
        }
        
        # 남은 시간 계산
        try {
            $endTime = [datetime]::Parse($MonitoringEndTime)
            $remaining = $endTime - (Get-Date)
            if ($remaining.TotalMinutes -gt 0) {
                $timelineFields += @{
                    type = "mrkdwn"
                    text = "*남은 시간:*`n$([math]::Ceiling($remaining.TotalMinutes))분"
                }
            }
        } catch {}
    }
    
    if ($timelineFields.Count -gt 0) {
        $blocks += @{
            type = "divider"
        }
        $blocks += @{
            type = "section"
            text = @{
                type = "mrkdwn"
                text = "*⏱️ 타임라인*"
            }
        }
        $blocks += @{
            type = "section"
            fields = $timelineFields
        }
    }
}

# 다음 단계 또는 액션
if ($Status -eq "monitoring") {
    $blocks += @{
        type = "divider"
    }
    $blocks += @{
        type = "section"
        text = @{
            type = "mrkdwn"
            text = "*📋 다음 단계*`n• 메트릭 모니터링 계속`n• 에러율 0.5% 미만 유지 확인`n• P95 레이턴시 10% 미만 증가 확인"
        }
    }
} elseif ($Status -eq "completed") {
    $blocks += @{
        type = "divider"
    }
    $blocks += @{
        type = "section"
        text = @{
            type = "mrkdwn"
            text = "*🎉 배포 성공!*`nCanary $Phase% 배포가 성공적으로 완료되었습니다."
        }
    }
} elseif ($Status -eq "failed") {
    $blocks += @{
        type = "divider"
    }
    $blocks += @{
        type = "section"
        text = @{
            type = "mrkdwn"
            text = "*⚠️ 즉시 확인 필요*`n배포에 문제가 발생했습니다. 로그를 확인하고 롤백을 고려하세요."
        }
    }
}

# 컨텍스트 푸터
$blocks += @{
    type = "context"
    elements = @(
        @{
            type = "mrkdwn"
            text = "마지막 업데이트: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') | 자동 갱신"
        }
    )
}

# 메시지 전송
$params = @{
    Message = "카나리 $Phase% - $($statusInfo.text)"
    Blocks = $blocks
}

if ($Channel) {
    $params.Channel = $Channel
}

$result = Send-SlackMessage @params

if ($result) {
    Write-Host "✅ 대시보드 업데이트 성공" -ForegroundColor Green
} else {
    Write-Warning "대시보드 업데이트 실패"
    exit 1
}
