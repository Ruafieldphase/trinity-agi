param(
    [string]$PolicyFile = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\policy\core_constitution.json",
    [switch]$Quiet
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = 'Stop'
function Say($msg, $color = 'Gray') { if (-not $Quiet) { Write-Host $msg -ForegroundColor $color } }

if (-not (Test-Path -LiteralPath $PolicyFile)) {
    Write-Host "[CoreGuard] 정책 파일을 찾을 수 없습니다: $PolicyFile" -ForegroundColor Red
    exit 2
}

try {
    $json = Get-Content -Raw -LiteralPath $PolicyFile | ConvertFrom-Json -ErrorAction Stop
}
catch {
    Write-Host "[CoreGuard] 정책 JSON 파싱 실패: $($_.Exception.Message)" -ForegroundColor Red
    exit 3
}

Say "`n[CoreGuard] Core 최소 헌법 점검 (dry-run)" 'Cyan'
Say " version: $($json.version)" 'DarkGray'

$prohibitions = $json.prohibitions
$rest = $json.rest_triggers
$logging = $json.logging
$meta = $json.meta
$gov = $meta.governance
$principles = $meta.principles

# 간단한 규칙 표시
$flags = @(
    @{k = 'forbid_harm'; t = '해악 금지' },
    @{k = 'forbid_consent_bypass'; t = '동의 우회 금지' },
    @{k = 'forbid_dignity_tradeoff'; t = '메트릭-존엄 맞바꾸기 금지' },
    @{k = 'forbid_skip_rest_on_risk'; t = '위험 신호 시 휴식 우회 금지' },
    @{k = 'forbid_context_leakage'; t = '맥락 경계 침해 금지' },
    @{k = 'forbid_shadow_logging'; t = '그림자 로깅 금지' },
    @{k = 'forbid_deception'; t = '속임수/오도 금지' },
    @{k = 'forbid_irreversible_without_review'; t = '되돌릴 수 없는 조치 단독 금지' },
    @{k = 'forbid_addiction_loops'; t = '중독 루프 금지' },
    @{k = 'forbid_metric_over_human'; t = '메트릭 우선으로 인간 침해 금지' },
    @{k = 'forbid_responsibility_obfuscation'; t = '책임 회피 구조 금지' },
    @{k = 'forbid_silencing_rights'; t = '표현/이의제기/탈퇴 권리 침해 금지' }
)

$violations = @()
foreach ($f in $flags) {
    $val = $prohibitions.($f.k)
    if ($null -eq $val -or $val -ne $true) {
        $violations += $f.t
    }
}

if ($violations.Count -eq 0) {
    Say " 모든 금지 플래그: 활성화 OK" 'Green'
}
else {
    Say " 비활성 금지 플래그: $(($violations -join ', '))" 'Yellow'
}

Say " Rest 트리거: entropy_slope_max=$($rest.entropy_slope_max), error_spike%=$($rest.error_rate_spike_percent), p95=$($rest.p95_latency_ms)ms, fear>=$($rest.fear_level_threshold), backlog>=$($rest.queue_backlog_threshold)" 'DarkGray'
Say " 로깅 정책: transparent=$($logging.transparent_audit_log), maskPII=$($logging.pii_masking), retain<=${($logging.retain_days_max)}d" 'DarkGray'

# 거버넌스/원칙 점검 (경고 수준)
if ($null -ne $principles) {
    $flagsP = @(
        @{k = 'hypothesis_not_doctrine'; t = '반증 가능성(가설이지 교의가 아님)'; v = $principles.hypothesis_not_doctrine },
        @{k = 'dynamic_equilibrium'; t = '동적 평형(정중동)'; v = $principles.dynamic_equilibrium },
        @{k = 'anti_dogma'; t = '반교조주의'; v = $principles.anti_dogma }
    )
    $off = ($flagsP | Where-Object { $_.v -ne $true })
    if ($off.Count -gt 0) {
        Say " 원칙 비활성: $((($off | Select-Object -ExpandProperty t) -join ', '))" 'Yellow'
    }
    else {
        Say " 원칙: 과학적 겸허/동적 평형/반교조주의 활성화" 'Green'
    }
}

if ($null -ne $gov) {
    $lr = $null
    $overdue = $false
    if ($gov.last_reviewed_at) {
        try { $lr = [datetime]::Parse($gov.last_reviewed_at) } catch { $lr = $null }
    }
    $cad = [int]($gov.review_cadence_days)
    if ($lr -ne $null -and $cad -gt 0) {
        $days = (New-TimeSpan -Start $lr -End (Get-Date)).TotalDays
        if ($days -gt $cad) { $overdue = $true }
        Say (" 거버넌스: last_reviewed={0}, cadence={1}d, overdue={2}" -f ($lr.ToString('yyyy-MM-dd')), $cad, $overdue) ($overdue ? 'Yellow' : 'DarkGray')
    }
    elseif ($cad -gt 0) {
        Say " 거버넌스: last_reviewed 파싱 실패 또는 누락" 'Yellow'
    }

    if ($gov.sunset_date) {
        try {
            $sd = [datetime]::Parse($gov.sunset_date)
            $expired = $sd -lt (Get-Date)
            Say (" 선셋: {0} (expired={1})" -f ($sd.ToString('yyyy-MM-dd')), $expired) ($expired ? 'Yellow' : 'DarkGray')
        }
        catch {
            Say " 선셋: 날짜 파싱 실패" 'Yellow'
        }
    }
    else {
        Say " 선셋: 없음(null)" 'DarkGray'
    }

    $ov = $gov.override_policy
    if ($ov) {
        Say (" 오버라이드: allow={0}, approvers>={1}, audit={2}" -f $ov.allow_override_with_approval, $ov.required_approvers, $ov.require_audit_log) 'DarkGray'
    }
    $exp = $gov.experiment_policy
    if ($exp) {
        Say (" 실험정책: A/B={0}, optout={1}, min_risk={2}" -f $exp.allow_ab_test, $exp.require_opt_out, $exp.min_risk_class) 'DarkGray'
    }
}

# 결과 코드: 플래그 누락시 경고, JSON 실패시 오류
if ($violations.Count -gt 0) { exit 1 } else { exit 0 }