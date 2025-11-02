#!/usr/bin/env pwsh
# smoke_streaming_synthesis.ps1
# Phase 2.8: Synthesis Streaming Smoke Test

param(
    [string]$Mode = "streaming"  # "streaming" or "baseline"
)

$ErrorActionPreference = "Stop"
$WorkspaceRoot = Split-Path -Parent $PSScriptRoot

Write-Host "`n=== Phase 2.8: Synthesis Streaming Smoke Test ===" -ForegroundColor Cyan
Write-Host "Mode: $Mode" -ForegroundColor Yellow

# 환경변수 설정
if ($Mode -eq "baseline") {
    $env:SYNTHESIS_STREAMING = "false"
    Write-Host "SYNTHESIS_STREAMING=false (Baseline)" -ForegroundColor Gray
} else {
    $env:SYNTHESIS_STREAMING = "true"
    Write-Host "SYNTHESIS_STREAMING=true (Streaming)" -ForegroundColor Green
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
from personas.synthesis import run_synthesis

# Mock Thesis & Antithesis outputs
thesis_out = PersonaOutput(
    task_id="smoke-test-synth",
    persona="thesis",
    summary="제안: AGI 자율 작동 시스템 구축\n\n1단계: 요구사항 분석\n2단계: 근거 확보 (RAG 검색)\n3단계: 산출물 작성",
    citations=[{"source": "memory/resonance_ledger.jsonl", "snippet": "과거 성공 사례"}],
    actions=[]
)

anti_out = PersonaOutput(
    task_id="smoke-test-synth",
    persona="antithesis",
    summary="[ANTITHESIS] 검증: 근거 보강 필요\n- 권고: 로컬 히트 최소 2개 이상 확보",
    citations=[{"source": "memory/resonance_ledger.jsonl", "snippet": "검증 사례"}],
    actions=[]
)

# Task spec
task = TaskSpec(task_id="smoke-test-synth", title="Smoke Test", goal="테스트")

# Mock tools
class MockTools:
    def call(self, tool, args):
        pass

# Run synthesis
print("\\nRunning synthesis...")
t0 = time.perf_counter()
result = run_synthesis(task, [thesis_out, anti_out], MockTools(), conversation_context="")
t1 = time.perf_counter()

print(f"\\nTotal Time: {t1 - t0:.2f}s")
print(f"Summary: {result.summary[:150]}...")

# Ledger에서 TTFT 확인
import json
ledger_path = r'$WorkspaceRoot\fdo_agi_repo\memory\resonance_ledger.jsonl'
if os.path.exists(ledger_path):
    with open(ledger_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        if lines:
            last = json.loads(lines[-1])
            if last.get('persona') == 'synthesis':
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
