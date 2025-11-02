#!/usr/bin/env pwsh
# smoke_streaming_antithesis.ps1
# Phase 2.7: Antithesis Streaming Smoke Test

param(
    [string]$Mode = "streaming"  # "streaming" or "baseline"
)

$ErrorActionPreference = "Stop"
$WorkspaceRoot = Split-Path -Parent $PSScriptRoot

Write-Host "`n=== Phase 2.7: Antithesis Streaming Smoke Test ===" -ForegroundColor Cyan
Write-Host "Mode: $Mode" -ForegroundColor Yellow

# 환경변수 설정
if ($Mode -eq "baseline") {
    $env:ANTITHESIS_STREAMING = "false"
    Write-Host "ANTITHESIS_STREAMING=false (Baseline)" -ForegroundColor Gray
}
else {
    $env:ANTITHESIS_STREAMING = "true"
    Write-Host "ANTITHESIS_STREAMING=true (Streaming)" -ForegroundColor Green
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

from orchestrator.contracts import TaskSpec, PersonaOutput
from personas.antithesis import run_antithesis

# Mock Thesis output
thesis_out = PersonaOutput(
    task_id="smoke-test-anti",
    persona="thesis",
    summary="제안: AGI 자율 작동 시스템 구축\n\n1단계: 요구사항 분석\n2단계: 근거 확보 (RAG 검색)\n3단계: 산출물 작성 (sandbox/docs/result.md)\n\n근거:\n- memory/resonance_ledger.jsonl 참조\n- 과거 성공 사례 3건 인용",
    citations=[{"source": "memory/resonance_ledger.jsonl", "snippet": "과거 성공 사례"}],
    actions=[]
)

# Task spec
task = TaskSpec(task_id="smoke-test-anti", title="Smoke Test", goal="테스트")

# Run antithesis
print("\\nRunning antithesis...")
t0 = time.perf_counter()
result = run_antithesis(task, thesis_out, tools=None, conversation_context="")
t1 = time.perf_counter()

print(f"\\nTotal Time: {t1 - t0:.2f}s")
print(f"Summary Length: {len(result.summary)} chars")
print(f"\\nSummary Preview:\\n{result.summary[:200]}...")

# Ledger에서 TTFT 확인
import json
ledger_path = r'$WorkspaceRoot\fdo_agi_repo\memory\resonance_ledger.jsonl'
if os.path.exists(ledger_path):
    with open(ledger_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        if lines:
            last = json.loads(lines[-1])
            if last.get('persona') == 'antithesis':
                print(f"\\nLedger Entry:")
                print(f"  Duration: {last.get('duration_sec', 0):.2f}s")
                print(f"  Streaming: {last.get('streaming', False)}")
                if 'ttft_sec' in last:
                    print(f"  TTFT: {last['ttft_sec']:.2f}s")
                    print(f"  Perceived Improvement: {last['perceived_improvement_pct']:.1f}%")
"@

# 테스트 실행
$TestScript | & $PythonExe

Write-Host "`n=== Smoke Test Complete ===" -ForegroundColor Green
