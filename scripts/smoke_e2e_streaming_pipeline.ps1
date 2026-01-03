#!/usr/bin/env pwsh
# smoke_e2e_streaming_pipeline.ps1
# Phase 2.9: End-to-End Streaming Pipeline Smoke Test

param(
    [string]$Mode = "streaming"  # "streaming" or "baseline"
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Stop"
$WorkspaceRoot = Split-Path -Parent $PSScriptRoot

Write-Host "`n=== Phase 2.9: E2E Streaming Pipeline Smoke Test ===" -ForegroundColor Cyan
Write-Host "Mode: $Mode" -ForegroundColor Yellow

# 환경변수 설정
if ($Mode -eq "baseline") {
    $env:THESIS_STREAMING = "false"
    $env:ANTITHESIS_STREAMING = "false"
    $env:SYNTHESIS_STREAMING = "false"
    Write-Host "All Streaming=false (Baseline)" -ForegroundColor Gray
} else {
    $env:THESIS_STREAMING = "true"
    $env:ANTITHESIS_STREAMING = "true"
    $env:SYNTHESIS_STREAMING = "true"
    Write-Host "All Streaming=true (E2E Pipeline)" -ForegroundColor Green
}

# Python 경로
$PythonExe = "$WorkspaceRoot\fdo_agi_repo\.venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    $PythonExe = "python"
}

# 테스트 코드 작성
$TestScript = @"
import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, r'$WorkspaceRoot\fdo_agi_repo')

# Simple test: Just call run_task
from orchestrator.pipeline import run_task

task_spec = {
    "task_id": "e2e-smoke-test",
    "title": "E2E Pipeline Test",
    "goal": "AGI 자율 작동 시스템의 핵심 구조를 3문장으로 설명하세요"
}

tool_cfg = {}

# Run full pipeline
print("\\nRunning full E2E pipeline...")
t0 = time.perf_counter()

try:
    result = run_task(tool_cfg, task_spec)
    t1 = time.perf_counter()
    
    print(f"\\nTotal Pipeline Time: {t1 - t0:.2f}s")
    print(f"Result: {result.get('summary', 'No summary')[:200]}...")
except Exception as e:
    print(f"\\nError: {e}")
    import traceback
    traceback.print_exc()
    t1 = time.perf_counter()
    print(f"\\nTime before error: {t1 - t0:.2f}s")

# Ledger에서 Pipeline 메트릭 확인
import json
ledger_path = r'$WorkspaceRoot\fdo_agi_repo\memory\resonance_ledger.jsonl'
if os.path.exists(ledger_path):
    with open(ledger_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        # 마지막 pipeline_e2e_complete 이벤트 찾기
        for line in reversed(lines[-50:]):  # 마지막 50줄만
            try:
                entry = json.loads(line)
                if entry.get('event') == 'pipeline_e2e_complete':
                    print(f"\\nPipeline Metrics:")
                    print(f"  Total Duration: {entry.get('total_duration_sec', 0):.2f}s")
                    print(f"  Streaming Enabled: {entry.get('streaming_enabled', False)}")
                    if 'pipeline_ttft_sec' in entry:
                        print(f"  Pipeline TTFT: {entry['pipeline_ttft_sec']:.2f}s")
                        print(f"  Perceived Improvement: {entry['pipeline_perceived_improvement_pct']:.1f}%")
                    break
            except:
                continue
"@

# 테스트 실행
$TestScript | & $PythonExe

Write-Host "`n=== Smoke Test Complete ===" -ForegroundColor Green