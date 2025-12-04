param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Info($msg) { Write-Host $msg -ForegroundColor Cyan }
function Write-Ok($msg) { Write-Host $msg -ForegroundColor Green }
function Write-Warn($msg) { Write-Host $msg -ForegroundColor Yellow }
function Write-Err($msg) { Write-Host $msg -ForegroundColor Red }

try {
    $root = Split-Path -Path $PSScriptRoot -Parent
    $outDir = Join-Path $root 'outputs'
    if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir | Out-Null }

    $dateTag = (Get-Date -Format 'yyyy-MM-dd')

    # 1) Capture ledger tail (last 400 lines)
    $ledgerCandidates = @(
        (Join-Path $root 'fdo_agi_repo\memory\resonance_ledger.jsonl'),
        (Join-Path $root 'memory\resonance_ledger.jsonl')
    )
    $ledger = $ledgerCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

    $tailOut = Join-Path $outDir ("unsaved_conversation_ledger_tail_{0}.jsonl" -f $dateTag)
    if ($ledger) {
        Write-Info "Reading tail from: $ledger"
        Get-Content -Path $ledger -Tail 400 | Set-Content -Path $tailOut -Encoding UTF8
        Write-Ok   "Saved ledger tail: $tailOut"
    }
    else {
        Write-Warn 'Ledger file not found. Skipping tail capture.'
    }

    # 2) Copy latest ledger summary (if exists)
    $summarySrcCandidates = @(
        (Join-Path $root 'fdo_agi_repo\outputs\ledger_summary_latest.md')
    )
    $summarySrc = $summarySrcCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

    $summaryOut = Join-Path $outDir ("unsaved_conversation_summary_{0}.md" -f $dateTag)
    if ($summarySrc) {
        Copy-Item -Path $summarySrc -Destination $summaryOut -Force
        Write-Ok "Copied summary: $summaryOut"
    }
    else {
        Set-Content -Path $summaryOut -Encoding UTF8 -Value "# Ledger summary not found

원본 요약 파일을 찾지 못했습니다. 필요한 경우 다음 태스크로 생성하세요:
- 'AGI: Summarize Ledger (12h)'
- 'AGI: Summarize Ledger (24h)'
"
        Write-Warn 'Ledger summary not found. Created placeholder.'
    }

    # 3) Create capture index with quick tips
    $indexOut = Join-Path $outDir ("unsaved_conversation_capture_{0}.md" -f $dateTag)

    $tailLine = if (Test-Path $tailOut) { '- Ledger tail: ' + $tailOut } else { '- Ledger tail: (not available)' }
    $summaryLine = if (Test-Path $summaryOut) { '- Ledger summary copy: ' + $summaryOut } else { '- Ledger summary copy: (placeholder)' }

    $codeBlock = @()
    if (Test-Path $tailOut) { $codeBlock += ("Select-String -Path '{0}' -Pattern '의식|무의식|트윈|twin|conscious|unconscious' -CaseSensitive:`$false" -f $tailOut) }
    $codeBlock += ("Select-String -Path '{0}' -Pattern 'context|phase|task|error|insight' -CaseSensitive:`$false" -f $summaryOut)
    $codeBlockText = ($codeBlock -join "`r`n")

    $indexMd = @"
# Unsaved Conversation Capture — $dateTag

이 파일은 입력 불가 상태였던 대화 내용을 복구하기 위해 생성되었습니다.

$tailLine
$summaryLine

## Quick Search Tips (PowerShell)
```powershell
$codeBlockText
```

## Notes
- 개인 정보가 포함되었을 수 있으니 공유 전 익명화하세요.
- 요약 재생성: 'AGI: Summarize Ledger (12h)' 또는 'AGI: Summarize Ledger (24h)' 태스크
"@

    Set-Content -Path $indexOut -Value $indexMd -Encoding UTF8
    Write-Ok "Wrote capture index: $indexOut"

    # Final summary
    Write-Host ''
    Write-Host 'Artifacts created:' -ForegroundColor Cyan
    if (Test-Path $tailOut) { Write-Host ("  - {0}" -f $tailOut) -ForegroundColor Cyan }
    if (Test-Path $summaryOut) { Write-Host ("  - {0}" -f $summaryOut) -ForegroundColor Cyan }
    Write-Host ("  - {0}" -f $indexOut) -ForegroundColor Cyan
    exit 0
}
catch {
    Write-Err ("Capture failed: {0}" -f $_.Exception.Message)
    exit 1
}