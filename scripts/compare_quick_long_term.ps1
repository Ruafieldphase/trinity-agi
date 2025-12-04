# Quick Performance Comparison - 7d vs 30d
param([switch]$Open)
$ErrorActionPreference = "Stop"
& "$PSScriptRoot\compare_performance_periods.ps1" -PeriodDays1 7 -PeriodDays2 30 -Label1 "Last Week" -Label2 "Last Month" $(if ($Open) { "-OpenReport" })
