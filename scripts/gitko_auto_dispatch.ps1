<#
.SYNOPSIS
  Gitko's intelligent work distribution engine - automatically routes work to appropriate agents.

.DESCRIPTION
  Analyzes incoming work requests and automatically dispatches to:
  - Gitko (solo): Code implementation, debugging, technical fixes
  - Lubit: Review, validation, documentation quality checks
  - Shion: Code suggestions, refactoring proposals, AI-assisted improvements
  - Parallel: Complex tasks requiring both review and code assist

.PARAMETER WorkRequest
  The user's work request/task description

.PARAMETER Context
  Optional context: files, error messages, or additional information

.PARAMETER ForceAgent
  Override auto-detection: 'gitko', 'lubit', 'Shion', 'parallel'

.PARAMETER DryRun
  Show routing decision without executing

.NOTES
  Decision Rules:
  - Review keywords (리뷰, 검토, 확인, 검증) → Lubit
  - Code assist keywords (제안, 개선, 리팩터, 최적화) → Shion
  - Documentation keywords (문서화, 정리, 보고서) → Lubit
  - Implementation keywords (구현, 수정, 추가, 버그) → Gitko
  - Complex tasks (병렬, 협업, 전체) → Parallel
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$WorkRequest,
  
    [string]$Context = "",
  
    [ValidateSet('auto', 'gitko', 'lubit', 'Shion', 'parallel')]
    [string]$ForceAgent = 'auto',
  
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot

# Classification patterns (using English to avoid encoding issues)
$patterns = @{
    Lubit    = @(
        'review', 'validate', 'check', 'audit', 'document', 'inspect',
        'verify', 'quality', 'handoff', 'report'
    )
    Shion     = @(
        'suggest', 'refactor', 'optimize', 'improve', 'assist',
        'enhance', 'modernize', 'performance', 'code.*quality'
    )
    Parallel = @(
        'parallel', 'collaborate', 'distributed', 'comprehensive',
        'both', 'review.*improve', 'improve.*review'
    )
    Gitko    = @(
        'implement', 'fix', 'add', 'delete', 'bug', 'error',
        'deploy', 'build', 'run.*test', 'execute', 'create',
        'update', 'modify', 'debug'
    )
}

function Get-WorkClassification {
    param([string]$Request)
  
    $scores = @{
        Lubit    = 0
        Shion     = 0
        Parallel = 0
        Gitko    = 0
    }
  
    $agentNames = @($scores.Keys)
    foreach ($agent in $agentNames) {
        foreach ($pattern in $patterns[$agent]) {
            if ($Request -match $pattern) {
                $scores[$agent]++
            }
        }
    }
  
    # Parallel wins if both Lubit and Shion have signals
    if ($scores.Lubit -gt 0 -and $scores.Shion -gt 0) {
        return 'Parallel'
    }
  
    # Find highest score
    $maxScore = ($scores.Values | Measure-Object -Maximum).Maximum
    if ($maxScore -eq 0) {
        return 'Gitko'  # Default to Gitko for ambiguous requests
    }
  
    $winner = $scores.GetEnumerator() | Where-Object { $_.Value -eq $maxScore } | Select-Object -First 1
    return $winner.Name
}

function Invoke-GitkoWork {
    param([string]$Task, [string]$Ctx)
    Write-Host "[Gitko] Executing solo work..." -ForegroundColor Cyan
    Write-Host "  Task: $Task" -ForegroundColor Gray
    if ($Ctx) { Write-Host "  Context: $Ctx" -ForegroundColor Gray }
    Write-Host "[Gitko] Work mode: Direct implementation" -ForegroundColor Green
    Write-Host "  → Gitko will handle this work directly in the conversation." -ForegroundColor Yellow
    return @{ Agent = 'Gitko'; Mode = 'Solo'; Status = 'Ready' }
}

function Invoke-LubitReview {
    param([string]$Task, [string]$Ctx)
    Write-Host "[Lubit] Preparing review packet..." -ForegroundColor Magenta
    $script = Join-Path $PSScriptRoot 'prepare_lubit_review_packet.ps1'
    if (Test-Path -LiteralPath $script) {
        & $script
        return @{ Agent = 'Lubit'; Mode = 'Review'; Status = 'Dispatched'; Script = $script }
    }
    else {
        Write-Warning "Lubit script not found: $script"
        return @{ Agent = 'Lubit'; Mode = 'Review'; Status = 'ScriptMissing' }
    }
}

function Invoke-ShionAssist {
    param([string]$Task, [string]$Ctx)
    Write-Host "[Shion] Generating code assist..." -ForegroundColor Yellow
    $outDir = Join-Path $repoRoot 'outputs'
    if (-not (Test-Path -LiteralPath $outDir)) {
        New-Item -ItemType Directory -Path $outDir | Out-Null
    }
    $ts = (Get-Date).ToUniversalTime().ToString('yyyyMMdd_HHmmss\Z')
    $outPath = Join-Path $outDir "shion_assist_${ts}.md"
  
    $venvPython = Join-Path $repoRoot 'LLM_Unified/.venv/Scripts/python.exe'
    $pythonExe = if (Test-Path -LiteralPath $venvPython) { $venvPython } else { 'python' }
    $geminiPOC = Join-Path $repoRoot 'tools/gemini_code_assist_poc.py'
  
    if (Test-Path -LiteralPath $geminiPOC) {
        & $pythonExe $geminiPOC --issue $Task --out $outPath
        return @{ Agent = 'Shion'; Mode = 'CodeAssist'; Status = 'Dispatched'; Output = $outPath }
    }
    else {
        Write-Warning "Shion tool not found: $geminiPOC"
        return @{ Agent = 'Shion'; Mode = 'CodeAssist'; Status = 'ToolMissing' }
    }
}

function Invoke-ParallelWork {
    param([string]$Task, [string]$Ctx)
    Write-Host "[Parallel] Distributing to Lubit & Shion..." -ForegroundColor Cyan
    $script = Join-Path $PSScriptRoot 'dispatch_to_lubit_and_shion.ps1'
    if (Test-Path -LiteralPath $script) {
        & $script -Issue $Task
        return @{ Agent = 'Parallel'; Mode = 'Distributed'; Status = 'Dispatched'; Script = $script }
    }
    else {
        Write-Warning "Parallel dispatcher not found: $script"
        return @{ Agent = 'Parallel'; Mode = 'Distributed'; Status = 'ScriptMissing' }
    }
}

# Main routing logic
Write-Host "=== Gitko Auto-Dispatch ===" -ForegroundColor Cyan
Write-Host "Work Request: $WorkRequest" -ForegroundColor White

$agent = if ($ForceAgent -ne 'auto') { $ForceAgent } else { Get-WorkClassification -Request $WorkRequest }

Write-Host "Routing Decision: $agent" -ForegroundColor Green
Write-Host ""

if ($DryRun.IsPresent) {
    Write-Host "[DRY RUN] Would dispatch to: $agent" -ForegroundColor Yellow
    exit 0
}

$result = switch ($agent) {
    'Gitko' { Invoke-GitkoWork -Task $WorkRequest -Ctx $Context }
    'Lubit' { Invoke-LubitReview -Task $WorkRequest -Ctx $Context }
    'Shion' { Invoke-ShionAssist -Task $WorkRequest -Ctx $Context }
    'Parallel' { Invoke-ParallelWork -Task $WorkRequest -Ctx $Context }
    default { Invoke-GitkoWork -Task $WorkRequest -Ctx $Context }
}

Write-Host ""
Write-Host "=== Dispatch Summary ===" -ForegroundColor Cyan
Write-Host "Agent:  $($result.Agent)" -ForegroundColor White
Write-Host "Mode:   $($result.Mode)" -ForegroundColor White
Write-Host "Status: $($result.Status)" -ForegroundColor White

if ($result.Status -eq 'Ready') {
    Write-Host ""
    Write-Host "[Next] Gitko will continue working on this task in the conversation." -ForegroundColor Green
}
elseif ($result.Status -eq 'Dispatched') {
    Write-Host ""
    Write-Host "[Next] Check outputs folder for $($result.Agent) artifacts." -ForegroundColor Green
}

exit 0