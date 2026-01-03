# Requires: Windows PowerShell 5.1+
# Purpose: Run BQI learners (Phase 4, 5, and optionally 6).
[CmdletBinding()]
param(
    [switch] $VerboseLog,
    [int] $Phase = 6  # Default: run all phases (4+5+6)
)

$ErrorActionPreference = 'Stop'

function Resolve-Python {
    param(
        [string] $RepoRoot
    )
    $venvPy = Join-Path $RepoRoot '.venv\Scripts\python.exe'
    if (Test-Path $venvPy) { return $venvPy }
    return 'python'
}

try {
    $repoRoot = Split-Path -Parent $PSScriptRoot
    $pythonExe = Resolve-Python -RepoRoot $repoRoot
    
    # Phase 4: BQI Pattern Learner
    if ($Phase -ge 4) {
        $learner = Join-Path $repoRoot 'scripts\learn_bqi_patterns.py'
        if (!(Test-Path $learner)) {
            throw "Learner script not found: $learner"
        }

        Push-Location $repoRoot
        try {
            if ($VerboseLog) { Write-Host "[BQI Phase 4] Running learner via: $pythonExe $learner" -ForegroundColor Cyan }
            & $pythonExe $learner
            if ($LASTEXITCODE -ne 0) {
                throw "Learner returned non-zero exit code: $LASTEXITCODE"
            }
        }
        finally { Pop-Location }
    }

    # Phase 5: Run Feedback Predictor (learn satisfaction-by-BQI)
    if ($Phase -ge 5) {
        $predictor = Join-Path $repoRoot 'scripts\rune\feedback_predictor.py'
        if (Test-Path $predictor) {
            Push-Location $repoRoot
            try {
                if ($VerboseLog) { Write-Host "[BQI Phase 5] Running feedback predictor via: $pythonExe $predictor" -ForegroundColor Cyan }
                & $pythonExe $predictor
                if ($LASTEXITCODE -ne 0) {
                    Write-Warning "[BQI Phase 5] Feedback predictor returned non-zero exit code: $LASTEXITCODE"
                }
            }
            finally { Pop-Location }
        }
        else {
            Write-Host "[BQI Phase 5] Feedback predictor not found, skipping: $predictor" -ForegroundColor Yellow
        }
    }

    # Phase 6: Run Binoche_Observer Persona Learner (learn decision patterns)
    if ($Phase -ge 6) {
        $personaLearner = Join-Path $repoRoot 'scripts\rune\binoche_persona_learner.py'
        if (Test-Path $personaLearner) {
            Push-Location $repoRoot
            try {
                if ($VerboseLog) { Write-Host "[BQI Phase 6] Running Binoche_Observer persona learner via: $pythonExe $personaLearner" -ForegroundColor Cyan }
                & $pythonExe $personaLearner
                if ($LASTEXITCODE -ne 0) {
                    Write-Warning "[BQI Phase 6] Binoche_Observer persona learner returned non-zero exit code: $LASTEXITCODE"
                }
            }
            finally { Pop-Location }
        }
        else {
            Write-Host "[BQI Phase 6] Binoche_Observer persona learner not found, skipping: $personaLearner" -ForegroundColor Yellow
        }
    }

    $outDir = Join-Path $repoRoot 'outputs'
    if (!(Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir | Out-Null }
    $modelPath = Join-Path $outDir 'bqi_pattern_model.json'
    $logPath = Join-Path $outDir 'bqi_learner_last_run.txt'

    $summary = "$(Get-Date -Format o) | status=ok"
    if (Test-Path $modelPath) {
        try {
            $model = Get-Content -Path $modelPath -Raw | ConvertFrom-Json
            $tasks = $null
            $used = $null
            try { $tasks = $model.meta.tasks_scanned } catch {}
            try { $used = $model.meta.samples_used } catch {}
            $prules = ($model.priority_rules | Get-Member -MemberType NoteProperty | Measure-Object).Count
            $erules = ($model.emotion_rules | Get-Member -MemberType NoteProperty | Measure-Object).Count
            $rrules = ($model.rhythm_rules | Get-Member -MemberType NoteProperty | Measure-Object).Count
            if ($tasks -ne $null -and $used -ne $null) {
                $summary = "$(Get-Date -Format o) | status=ok | tasks=$tasks used=$used prules=$prules erules=$erules rrules=$rrules"
            }
            else {
                $summary = "$(Get-Date -Format o) | status=ok | prules=$prules erules=$erules rrules=$rrules"
            }
        }
        catch {
            $summary = "$(Get-Date -Format o) | status=ok | note=could-not-parse-model-json"
        }
    }
    else {
        $summary = "$(Get-Date -Format o) | status=ok | note=no-model-file"
    }

    # Append Feedback Predictor summary if available
    $feedbackModelPath = Join-Path $outDir 'feedback_prediction_model.json'
    $fbSuffix = ""
    if (Test-Path $feedbackModelPath) {
        try {
            $fb = Get-Content -Path $feedbackModelPath -Raw | ConvertFrom-Json
            $fbSamples = $null
            try { $fbSamples = $fb.samples_count } catch {}
            $fbPatterns = 0
            try { $fbPatterns = ($fb.satisfaction_by_bqi | Get-Member -MemberType NoteProperty | Measure-Object).Count } catch {}
            $fbRules = 0
            try { $fbRules = ($fb.adjustment_rules | Measure-Object).Count } catch {}
            if ($fbSamples -ne $null) {
                $fbSuffix = " fb_samples=$fbSamples fb_patterns=$fbPatterns fb_rules=$fbRules"
            }
            else {
                $fbSuffix = " fb_patterns=$fbPatterns fb_rules=$fbRules"
            }
        }
        catch {
            $fbSuffix = " fb_note=could-not-parse-feedback-model"
        }
    }
    else {
        $fbSuffix = " fb_note=no-feedback-model"
    }
    $summary = $summary + $fbSuffix

    # Append Binoche_Observer Persona summary if available (Phase 6)
    $personaModelPath = Join-Path $outDir 'binoche_persona.json'
    $personaSuffix = ""
    if (Test-Path $personaModelPath) {
        try {
            $persona = Get-Content -Path $personaModelPath -Raw | ConvertFrom-Json
            $pTasks = $null
            $pDecisions = $null
            $pPatterns = 0
            $pRules = 0
            try { $pTasks = $persona.stats.total_tasks } catch {}
            try { $pDecisions = $persona.stats.total_decisions } catch {}
            try { $pPatterns = ($persona.bqi_probabilities | Get-Member -MemberType NoteProperty | Measure-Object).Count } catch {}
            try { $pRules = ($persona.rules | Measure-Object).Count } catch {}
            
            if ($pTasks -ne $null -and $pDecisions -ne $null) {
                $personaSuffix = " persona_tasks=$pTasks persona_decisions=$pDecisions persona_patterns=$pPatterns persona_rules=$pRules"
            }
            else {
                $personaSuffix = " persona_patterns=$pPatterns persona_rules=$pRules"
            }
        }
        catch {
            $personaSuffix = " persona_note=could-not-parse-persona-model"
        }
    }
    else {
        $personaSuffix = " persona_note=no-persona-model"
    }
    $summary = $summary + $personaSuffix

    $summary | Out-File -FilePath $logPath -Encoding UTF8 -Append
    Write-Host "[BQI] Learner run complete." -ForegroundColor Green
    Write-Host $summary
    exit 0
}
catch {
    Write-Error $_
    try {
        $repoRoot = Split-Path -Parent $PSScriptRoot
        $outDir = Join-Path $repoRoot 'outputs'
        if (!(Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir | Out-Null }
        $logPath = Join-Path $outDir 'bqi_learner_last_run.txt'
        "$(Get-Date -Format o) | status=fail | error=$($_.Exception.Message)" | Out-File -FilePath $logPath -Encoding UTF8 -Append
    }
    catch {}
    exit 1
}
