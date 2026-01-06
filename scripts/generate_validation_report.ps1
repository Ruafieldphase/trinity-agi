#!/usr/bin/env pwsh
# 24시간 검증 결과 리포트 생성

param(
    [Parameter(Mandatory = $true)]
    [string]$ValidationDir,
    [switch]$OpenMd
)

$ErrorActionPreference = "Stop"

Write-Host "📊 Generating 24-Hour Validation Report..." -ForegroundColor Cyan

$logPath = Join-Path $ValidationDir "validation_log.jsonl"
$summaryPath = Join-Path $ValidationDir "validation_summary.json"
$reportPath = Join-Path $ValidationDir "validation_report.md"

if (!(Test-Path $logPath) -or !(Test-Path $summaryPath)) {
    Write-Host "❌ Validation files not found in: $ValidationDir" -ForegroundColor Red
    exit 1
}

# 로그 파싱
$entries = Get-Content $logPath | ForEach-Object {
    $_ | ConvertFrom-Json
}

$summary = Get-Content $summaryPath -Raw | ConvertFrom-Json

# 마크다운 리포트 생성
$md = @"
# 🔬 24-Hour Autonomous System Validation Report

Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

## 📊 Executive Summary

| Metric | Value |
|--------|-------|
| **Start Time** | $($summary.start_time) |
| **End Time** | $($summary.current_time) |
| **Duration** | $([math]::Round($summary.elapsed_hours, 2)) hours |
| **Total Checks** | $($summary.total_checks) |
| **Success Checks** | $($summary.success_checks) ✅ |
| **Warning Checks** | $($summary.warning_checks) ⚠️ |
| **Failure Checks** | $($summary.failure_checks) ❌ |
| **Overall Success Rate** | $($summary.overall_success_rate)% |

## 🎯 Assessment

"@

if ($summary.overall_success_rate -ge 90) {
    $md += @"
**Status: 🎉 EXCELLENT**

The system demonstrated exceptional stability and autonomous operation over 24 hours. All critical components functioned reliably.

"@
}
elseif ($summary.overall_success_rate -ge 75) {
    $md += @"
**Status: ✅ GOOD**

The system maintained good operational status over 24 hours with minor issues. Some components may benefit from attention.

"@
}
elseif ($summary.overall_success_rate -ge 50) {
    $md += @"
**Status: ⚠️ ACCEPTABLE**

The system remained operational but experienced several issues. Review and improvements recommended.

"@
}
else {
    $md += @"
**Status: ❌ NEEDS ATTENTION**

The system experienced significant issues during the 24-hour period. Immediate investigation required.

"@
}

# 타임라인
$md += @"

## 📈 Timeline

| Check # | Time | Status | Pass Rate | Notes |
|---------|------|--------|-----------|-------|
"@

$checkEntries = $entries | Where-Object { $_.type -eq "success" -or $_.type -eq "warning" -or $_.type -eq "error" } | 
Group-Object check_number | ForEach-Object {
    $checkNum = $_.Name
    $checkEntries = $_.Group
        
    $successCount = ($checkEntries | Where-Object { $_.type -eq "success" }).Count
    $total = $checkEntries.Count
    $passRate = if ($total -gt 0) { [math]::Round(($successCount / $total) * 100, 1) } else { 0 }
        
    $status = if ($passRate -ge 75) { "✅" } elseif ($passRate -ge 50) { "⚠️" } else { "❌" }
        
    $time = ($checkEntries | Select-Object -First 1).timestamp
    $timeStr = ([datetime]$time).ToString('HH:mm:ss')
        
    $issues = ($checkEntries | Where-Object { $_.type -ne "success" }).message -join "; "
    $notes = if ($issues) { $issues.Substring(0, [Math]::Min(50, $issues.Length)) } else { "All systems operational" }
        
    "| $checkNum | $timeStr | $status | $passRate% | $notes |"
}

$md += "`n" + ($checkEntries -join "`n")

# 컴포넌트 상태
$md += @"


## 🔧 Component Analysis

### System Health Checks

"@

$healthChecks = $entries | Where-Object { $_.message -like "*health*" }
$healthSuccess = ($healthChecks | Where-Object { $_.type -eq "success" }).Count
$healthTotal = $healthChecks.Count
$healthRate = if ($healthTotal -gt 0) { [math]::Round(($healthSuccess / $healthTotal) * 100, 1) } else { 0 }

$md += "- **Total Checks**: $healthTotal`n"
$md += "- **Success Rate**: $healthRate%`n"
$md += "- **Status**: $(if ($healthRate -ge 90) { '✅ Excellent' } elseif ($healthRate -ge 75) { '⚠️ Good' } else { '❌ Needs Attention' })`n`n"

$md += "### Autonomous Goal Execution`n`n"

$goalChecks = $entries | Where-Object { $_.message -like "*goal*" }
$goalSuccess = ($goalChecks | Where-Object { $_.type -eq "success" }).Count
$goalTotal = $goalChecks.Count
$goalRate = if ($goalTotal -gt 0) { [math]::Round(($goalSuccess / $goalTotal) * 100, 1) } else { 0 }

$md += "- **Total Checks**: $goalTotal`n"
$md += "- **Success Rate**: $goalRate%`n"
$md += "- **Status**: $(if ($goalRate -ge 90) { '✅ Excellent' } elseif ($goalRate -ge 75) { '⚠️ Good' } else { '❌ Needs Attention' })`n`n"

$md += "### Task Queue Server`n`n"

$queueChecks = $entries | Where-Object { $_.message -like "*queue*" -or $_.message -like "*server*" }
$queueSuccess = ($queueChecks | Where-Object { $_.type -eq "success" }).Count
$queueTotal = $queueChecks.Count
$queueRate = if ($queueTotal -gt 0) { [math]::Round(($queueSuccess / $queueTotal) * 100, 1) } else { 0 }

$md += "- **Total Checks**: $queueTotal`n"
$md += "- **Success Rate**: $queueRate%`n"
$md += "- **Status**: $(if ($queueRate -ge 90) { '✅ Excellent' } elseif ($queueRate -ge 75) { '⚠️ Good' } else { '❌ Needs Attention' })`n`n"

$md += "### Metrics Collection`n`n"

$metricsChecks = $entries | Where-Object { $_.message -like "*metrics*" }
$metricsSuccess = ($metricsChecks | Where-Object { $_.type -eq "success" }).Count
$metricsTotal = $metricsChecks.Count
$metricsRate = if ($metricsTotal -gt 0) { [math]::Round(($metricsSuccess / $metricsTotal) * 100, 1) } else { 0 }

$md += "- **Total Checks**: $metricsTotal`n"
$md += "- **Success Rate**: $metricsRate%`n"
$md += "- **Status**: $(if ($metricsRate -ge 90) { '✅ Excellent' } elseif ($metricsRate -ge 75) { '⚠️ Good' } else { '❌ Needs Attention' })`n`n"

# 이슈 요약
$md += "## ⚠️ Issues Detected`n`n"

$warnings = $entries | Where-Object { $_.type -eq "warning" }
$errors = $entries | Where-Object { $_.type -eq "error" }

if ($warnings.Count -gt 0) {
    $md += "### Warnings ($($warnings.Count))`n`n"
    $warnings | Group-Object message | ForEach-Object {
        $md += "- **$($_.Name)** (occurred $($_.Count) times)`n"
    }
    $md += "`n"
}

if ($errors.Count -gt 0) {
    $md += "### Errors ($($errors.Count))`n`n"
    $errors | Group-Object message | ForEach-Object {
        $md += "- **$($_.Name)** (occurred $($_.Count) times)`n"
    }
    $md += "`n"
}

if ($warnings.Count -eq 0 -and $errors.Count -eq 0) {
    $md += "✅ No issues detected during the 24-hour period!`n`n"
}

# 권장사항
$md += "## 💡 Recommendations`n`n"

if ($summary.overall_success_rate -ge 95) {
    $md += "- ✅ System is operating optimally. Continue current monitoring schedule.`n"
    $md += "- 📈 Consider expanding autonomous capabilities.`n"
}
elseif ($summary.overall_success_rate -ge 85) {
    $md += "- ✅ System is stable. Address minor warnings during maintenance windows.`n"
    $md += "- 🔍 Monitor components with lower success rates.`n"
}
elseif ($summary.overall_success_rate -ge 70) {
    $md += "- ⚠️ Review and address recurring warnings.`n"
    $md += "- 🔧 Consider implementing auto-recovery for failing components.`n"
    $md += "- 📊 Increase monitoring frequency for unstable components.`n"
}
else {
    $md += "- ❌ Immediate attention required for failing components.`n"
    $md += "- 🚨 Review system logs for root cause analysis.`n"
    $md += "- 🔧 Implement fixes for recurring errors.`n"
    $md += "- 📞 Consider manual intervention if auto-recovery fails.`n"
}

$md += @"


## 📚 Detailed Logs

Full validation log: ``$logPath``

---

*Report generated by AGI Autonomous Validation System*
*Self-Care + Feedback Trinity Integration*
"@

# 리포트 저장
$md | Set-Content -Path $reportPath -Encoding UTF8

Write-Host "✅ Report generated: $reportPath" -ForegroundColor Green

if ($OpenMd) {
    Write-Host "📖 Opening report..." -ForegroundColor Cyan
    code $reportPath
}

# JSON 요약도 생성
$jsonReport = @{
    generated_at     = (Get-Date).ToString('o')
    summary          = $summary
    component_health = @{
        system_health      = @{
            total   = $healthTotal
            success = $healthSuccess
            rate    = $healthRate
        }
        goal_execution     = @{
            total   = $goalTotal
            success = $goalSuccess
            rate    = $goalRate
        }
        queue_server       = @{
            total   = $queueTotal
            success = $queueSuccess
            rate    = $queueRate
        }
        metrics_collection = @{
            total   = $metricsTotal
            success = $metricsSuccess
            rate    = $metricsRate
        }
    }
    issues           = @{
        warnings = $warnings.Count
        errors   = $errors.Count
    }
}

$jsonPath = Join-Path $ValidationDir "validation_report.json"
$jsonReport | ConvertTo-Json -Depth 10 | Set-Content -Path $jsonPath

Write-Host "✅ JSON report: $jsonPath" -ForegroundColor Green
Write-Host "`n✨ Done!" -ForegroundColor Green