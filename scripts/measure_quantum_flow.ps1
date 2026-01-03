#!/usr/bin/env pwsh
# -*- coding: utf-8 -*-
<#
.SYNOPSIS
    Quantum Flow State 측정 - 무의식/의식 간 결맞음 측정

.DESCRIPTION
    해마(무의식) ↔ 실행 제어(의식) 간 위상 동기화를 측정하여
    초전도 상태(flow state) 여부를 판단합니다.
    
    이론적 배경:
    - 도파민/세로토닌 = 시냅스 전위차 생성
    - 무의식/의식 공명 = 위상 결맞음 (phase coherence)
    - 결맞음 > 0.95 → 초전도 상태 (flow state)

.PARAMETER Measure
    현재 flow state 측정

.PARAMETER Report
    Flow state 리포트 생성

.PARAMETER Hours
    리포트 기간 (시간)

.PARAMETER Watch
    실시간 모니터링

.PARAMETER OutJson
    JSON 출력 파일 경로

.EXAMPLE
    .\measure_quantum_flow.ps1 -Measure
    현재 flow state 측정

.EXAMPLE
    .\measure_quantum_flow.ps1 -Report -Hours 24
    24시간 flow state 리포트

.EXAMPLE
    .\measure_quantum_flow.ps1 -Watch
    실시간 모니터링
#>

param(
    [switch]$Measure,
    [switch]$Report,
    [int]$Hours = 24,
    [switch]$Watch,
    [string]$OutJson = ""
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Stop"
$WorkspaceRoot = Split-Path -Parent $PSScriptRoot

# Python 경로 찾기
$PythonExe = "$WorkspaceRoot\fdo_agi_repo\.venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $PythonExe)) {
    $PythonExe = "python"
}

# 모듈 경로
$MonitorScript = "$WorkspaceRoot\fdo_agi_repo\copilot\quantum_flow_monitor.py"

if (-not (Test-Path -LiteralPath $MonitorScript)) {
    Write-Host "❌ Quantum Flow Monitor not found: $MonitorScript" -ForegroundColor Red
    exit 1
}

# 명령 구성
$CmdArgs = @(
    $MonitorScript,
    "--workspace", $WorkspaceRoot
)

if ($Measure) {
    $CmdArgs += "--measure"
}
elseif ($Report) {
    $CmdArgs += "--report", "--hours", $Hours
}
elseif ($Watch) {
    $CmdArgs += "--watch"
}
else {
    Write-Host "Usage: .\measure_quantum_flow.ps1 [-Measure | -Report | -Watch]" -ForegroundColor Yellow
    exit 0
}

# 실행
Write-Host "🌌 Quantum Flow Monitor" -ForegroundColor Cyan
& $PythonExe $CmdArgs

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Flow measurement failed" -ForegroundColor Red
    exit $LASTEXITCODE
}

# JSON 출력
if ($OutJson -and (Test-Path -LiteralPath "$WorkspaceRoot\outputs\quantum_flow_history.jsonl")) {
    Copy-Item "$WorkspaceRoot\outputs\quantum_flow_history.jsonl" $OutJson -Force
    Write-Host "✅ Saved to: $OutJson" -ForegroundColor Green
}