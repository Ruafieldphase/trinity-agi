# Requires: Windows PowerShell 5.1+
# Purpose: Verify BQI pattern model JSON and print concise summary.
[CmdletBinding()]
param(
    [string] $ModelPath = ""
)

$ErrorActionPreference = 'Stop'

try {
    if (-not $ModelPath) {
        $repoRoot = Split-Path -Parent $PSScriptRoot
        $ModelPath = Join-Path $repoRoot 'outputs\bqi_pattern_model.json'
    }

    if (!(Test-Path $ModelPath)) {
        throw "Model file not found: $ModelPath"
    }

    $raw = Get-Content -Path $ModelPath -Raw -ErrorAction Stop
    try {
        $json = $raw | ConvertFrom-Json -ErrorAction Stop
    }
    catch {
        throw "Failed to parse JSON: $($_.Exception.Message)"
    }

    # Extract meta safely
    $meta = $json.meta
    $taskCount = $null
    $samplesUsed = $null
    # task_count or tasks_scanned (treat 0 as valid)
    try {
        if ($meta -and $meta.PSObject.Properties.Name -contains 'task_count') { $taskCount = $meta.task_count }
        elseif ($meta -and $meta.PSObject.Properties.Name -contains 'tasks_scanned') { $taskCount = $meta.tasks_scanned }
    }
    catch {}
    # samples_used may exist at top-level or under meta (treat 0 as valid)
    try {
        if ($json.PSObject.Properties.Name -contains 'samples_used') { $samplesUsed = $json.samples_used }
        elseif ($meta -and $meta.PSObject.Properties.Name -contains 'samples_used') { $samplesUsed = $meta.samples_used }
    }
    catch {}

    function Get-RuleCount($obj) {
        if ($null -eq $obj) { return 0 }
        try {
            # Count top-level properties for PSCustomObject
            $props = $obj | Get-Member -MemberType NoteProperty -ErrorAction SilentlyContinue
            if ($props) { return ($props | Measure-Object).Count }
            # If hashtable/dictionary, count keys
            if ($obj -is [System.Collections.IDictionary]) { return $obj.Keys.Count }
            # If array, length
            if ($obj -is [System.Array]) { return $obj.Length }
        }
        catch {}
        return 0
    }

    $prules = Get-RuleCount $json.priority_rules
    $erules = Get-RuleCount $json.emotion_rules
    $rrules = Get-RuleCount $json.rhythm_rules

    $summary = "[BQI] Model OK | tasks=$taskCount samples=$samplesUsed prules=$prules erules=$erules rrules=$rrules"
    Write-Host $summary -ForegroundColor Green
    exit 0
}
catch {
    Write-Error $_
    exit 1
}
