# Quick Performance Comparison - 3d vs 7d
param([switch]$Open)
$ErrorActionPreference = "Stop"
& "$PSScriptRoot\compare_performance_periods.ps1" -PeriodDays1 3 -PeriodDays2 7 -Label1 "Last 3 Days" -Label2 "Last 7 Days" $(if ($Open) { "-OpenReport" })