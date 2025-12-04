# Integration Conflict & Performance Diagnosis
# 정반합 통합 충돌 및 성능 저하 원인 진단

param(
    [string]$WorkspaceRoot = "C:\workspace\agi"
)

$ErrorActionPreference = 'Continue'

Write-Host "`n=== AGI Integration Conflict Diagnosis ===" -ForegroundColor Cyan
Write-Host "Checking Thesis-Antithesis-Synthesis integration status...`n"

$issues = @()
$warnings = @()

# 1. Check orchestrator files
Write-Host "[1/6] Checking orchestrator integration files..." -ForegroundColor Yellow

$pipelineFile = Join-Path $WorkspaceRoot "fdo_agi_repo\orchestrator\pipeline.py"
$bridgeFile = Join-Path $WorkspaceRoot "fdo_agi_repo\orchestrator\resonance_bridge.py"

if (Test-Path $pipelineFile) {
    $pipelineSize = (Get-Item $pipelineFile).Length
    $pipelineModified = (Get-Item $pipelineFile).LastWriteTime
    Write-Host "  ✅ pipeline.py found ($pipelineSize bytes, modified: $pipelineModified)"
}
else {
    $issues += "❌ pipeline.py not found"
    Write-Host "  ❌ pipeline.py NOT FOUND" -ForegroundColor Red
}

if (Test-Path $bridgeFile) {
    $bridgeSize = (Get-Item $bridgeFile).Length
    $bridgeModified = (Get-Item $bridgeFile).LastWriteTime
    Write-Host "  ✅ resonance_bridge.py found ($bridgeSize bytes, modified: $bridgeModified)"
}
else {
    $issues += "❌ resonance_bridge.py not found"
    Write-Host "  ❌ resonance_bridge.py NOT FOUND" -ForegroundColor Red
}

# 2. Check recent ledger for errors
Write-Host "`n[2/6] Checking recent ledger for integration errors..." -ForegroundColor Yellow

$ledger = Join-Path $WorkspaceRoot "fdo_agi_repo\memory\resonance_ledger.jsonl"
if (Test-Path $ledger) {
    $recentLines = Get-Content $ledger -Tail 100
    $errors = $recentLines | ForEach-Object {
        try { 
            $obj = $_ | ConvertFrom-Json
            if ($obj.event -like '*error*' -or $obj.event -like '*fail*' -or $obj.level -eq 'ERROR') {
                $obj
            }
        }
        catch {}
    }
    
    if ($errors.Count -gt 0) {
        Write-Host "  ⚠️  Found $($errors.Count) error events in last 100 entries" -ForegroundColor Yellow
        $warnings += "Found $($errors.Count) error events"
        $errors | Select-Object -First 3 | ForEach-Object {
            Write-Host "    - $($_.timestamp): $($_.event) - $($_.error)"
        }
    }
    else {
        Write-Host "  ✅ No error events found in recent ledger"
    }
}
else {
    $issues += "❌ Ledger file not found"
}

# 3. Check for conflicting configurations
Write-Host "`n[3/6] Checking for configuration conflicts..." -ForegroundColor Yellow

$configFile = Join-Path $WorkspaceRoot "fdo_agi_repo\config\agi_config.yaml"
if (Test-Path $configFile) {
    $config = Get-Content $configFile -Raw
    
    # Check for conflicting rhythm settings
    if ($config -match 'rhythm_enabled:\s*true' -and $config -match 'legacy_mode:\s*true') {
        $issues += "⚠️  Both rhythm_enabled and legacy_mode are true"
        Write-Host "  ⚠️  CONFLICT: Both rhythm and legacy modes enabled" -ForegroundColor Red
    }
    else {
        Write-Host "  ✅ No mode conflicts detected"
    }
    
    # Check pipeline integration settings
    if ($config -match 'pipeline_integration:\s*incomplete' -or $config -match 'integration_status:\s*partial') {
        $warnings += "Integration marked as incomplete"
        Write-Host "  ⚠️  WARNING: Integration marked as incomplete in config" -ForegroundColor Yellow
    }
}
else {
    Write-Host "  ℹ️  Config file not found (may be using defaults)"
}

# 4. Check system resource usage
Write-Host "`n[4/6] Checking system resource usage..." -ForegroundColor Yellow

$cpu = (Get-WmiObject Win32_Processor | Measure-Object -Property LoadPercentage -Average).Average
$mem = Get-WmiObject Win32_OperatingSystem
$memUsedPercent = [math]::Round((($mem.TotalVisibleMemorySize - $mem.FreePhysicalMemory) / $mem.TotalVisibleMemorySize) * 100, 1)

Write-Host "  CPU Load: $cpu%"
Write-Host "  Memory Usage: $memUsedPercent%"

if ($cpu -gt 80) {
    $warnings += "High CPU usage: $cpu%"
    Write-Host "  ⚠️  HIGH CPU LOAD" -ForegroundColor Yellow
}
if ($memUsedPercent -gt 85) {
    $warnings += "High memory usage: $memUsedPercent%"
    Write-Host "  ⚠️  HIGH MEMORY USAGE" -ForegroundColor Yellow
}

# 5. Check for incomplete integration markers
Write-Host "`n[5/6] Scanning for incomplete integration markers..." -ForegroundColor Yellow

$pythonFiles = Get-ChildItem -Path "$WorkspaceRoot\fdo_agi_repo" -Filter "*.py" -Recurse -ErrorAction SilentlyContinue
$incompleteMarkers = $pythonFiles | ForEach-Object {
    $content = Get-Content $_.FullName -Raw -ErrorAction SilentlyContinue
    if ($content -match '(?i)(TODO.*integration|FIXME.*integration|incomplete.*integration|WIP.*integration)') {
        [PSCustomObject]@{
            File  = $_.FullName.Replace($WorkspaceRoot, '.')
            Match = $Matches[1]
        }
    }
} | Select-Object -First 5

if ($incompleteMarkers) {
    Write-Host "  ⚠️  Found incomplete integration markers:" -ForegroundColor Yellow
    $incompleteMarkers | ForEach-Object {
        Write-Host "    $($_.File): $($_.Match)"
        $warnings += "Incomplete marker in $($_.File)"
    }
}
else {
    Write-Host "  ✅ No incomplete integration markers found"
}

# 6. Check for data schema conflicts
Write-Host "`n[6/6] Checking for data schema conflicts..." -ForegroundColor Yellow

$oldDataDirs = @(
    "$WorkspaceRoot\fdo_agi_repo\memory_old",
    "$WorkspaceRoot\fdo_agi_repo\data\legacy",
    "$WorkspaceRoot\fdo_agi_repo\outputs\backup_pre_rhythm"
)

foreach ($dir in $oldDataDirs) {
    if (Test-Path $dir) {
        Write-Host "  ⚠️  Found legacy data: $dir" -ForegroundColor Yellow
        $warnings += "Legacy data found: $dir"
    }
}

# Check for conflicting ledger formats
if (Test-Path $ledger) {
    $sampleLines = Get-Content $ledger -Tail 10
    $schemas = $sampleLines | ForEach-Object {
        try {
            $obj = $_ | ConvertFrom-Json
            ($obj | Get-Member -MemberType NoteProperty).Name | Sort-Object
        }
        catch {}
    }
    
    $uniqueSchemas = $schemas | Select-Object -Unique
    if ($uniqueSchemas.Count -gt 1) {
        Write-Host "  ⚠️  Multiple ledger schemas detected (possible format conflict)" -ForegroundColor Yellow
        $warnings += "Multiple ledger schemas detected"
    }
    else {
        Write-Host "  ✅ Consistent ledger schema"
    }
}

# Summary
Write-Host "`n=== Diagnosis Summary ===" -ForegroundColor Cyan

if ($issues.Count -eq 0 -and $warnings.Count -eq 0) {
    Write-Host "✅ No critical issues or warnings detected" -ForegroundColor Green
    Write-Host "`nPerformance slowdown may be due to:" -ForegroundColor Yellow
    Write-Host "  1. Network latency to LLM endpoints"
    Write-Host "  2. Increased complexity after integration"
    Write-Host "  3. Background processes consuming resources"
}
else {
    if ($issues.Count -gt 0) {
        Write-Host "`n❌ Critical Issues ($($issues.Count)):" -ForegroundColor Red
        $issues | ForEach-Object { Write-Host "  - $_" }
    }
    
    if ($warnings.Count -gt 0) {
        Write-Host "`n⚠️  Warnings ($($warnings.Count)):" -ForegroundColor Yellow
        $warnings | ForEach-Object { Write-Host "  - $_" }
    }
    
    Write-Host "`nRecommended Actions:" -ForegroundColor Cyan
    if ($issues -like '*pipeline.py*' -or $issues -like '*resonance_bridge*') {
        Write-Host "  1. Restore missing orchestrator files from backup"
    }
    if ($warnings -like '*incomplete*' -or $warnings -like '*Integration*') {
        Write-Host "  2. Complete the integration by running integration script"
    }
    if ($warnings -like '*legacy data*') {
        Write-Host "  3. Migrate or archive legacy data to avoid conflicts"
    }
    if ($warnings -like '*schema*') {
        Write-Host "  4. Run ledger sanitization to unify schema"
    }
}

Write-Host ""
exit 0
