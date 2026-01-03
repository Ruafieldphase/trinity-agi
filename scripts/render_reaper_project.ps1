[CmdletBinding()]
param(
    [string]$ProjectPath,
    [string]$TemplateKey,
    [string]$OutputName,
    [string]$ConfigPath = "config/reaper_automation.json",
    [string]$ReaperPath,
    [switch]$SkipRenderFileRewrite,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptRoot "..")

function Resolve-RepoPath {
    param([string]$PathValue)
    if ([string]::IsNullOrWhiteSpace($PathValue)) {
        return $null
    }
    if ([System.IO.Path]::IsPathRooted($PathValue)) {
        return [System.IO.Path]::GetFullPath($PathValue)
    }
    $combined = Join-Path $repoRoot $PathValue
    return [System.IO.Path]::GetFullPath($combined)
}

function Get-Config {
    param([string]$PathValue)
    if (-not (Test-Path $PathValue)) {
        Write-Warning "Config file '$PathValue' not found. Using built-in defaults."
        return @{}
    }
    try {
        return Get-Content -Raw -Path $PathValue | ConvertFrom-Json
    } catch {
        throw "Failed to parse config file '$PathValue': $($_.Exception.Message)"
    }
}

$configFullPath = Resolve-RepoPath $ConfigPath
$config = Get-Config -PathValue $configFullPath

function Get-ConfigValue {
    param(
        [string]$Key,
        [object]$Fallback = $null
    )
    if ($config -and ($config.PSObject.Properties.Name -contains $Key) -and $config.$Key) {
        return $config.$Key
    }
    return $Fallback
}

$reaperExe = if ($ReaperPath) { $ReaperPath } else { Get-ConfigValue -Key "reaper_path" -Fallback (Join-Path ${env:ProgramFiles} "REAPER (x64)\reaper.exe") }
$reaperExe = Resolve-RepoPath $reaperExe
if (-not (Test-Path $reaperExe)) {
    throw "REAPER executable not found at '$reaperExe'. Set 'reaper_path' in config or pass -ReaperPath."
}

function Resolve-TemplateDefinition {
    param(
        [string]$ExplicitPath,
        [string]$Key
    )
    if ($ExplicitPath) {
        return @{
            path = $ExplicitPath
        }
    }

    if ($Key) {
        $templates = Get-ConfigValue -Key "templates"
        if (-not $templates) {
            throw "Template key '$Key' requested but no 'templates' block present in config."
        }

        $templateEntry = $null
        if ($templates -is [System.Collections.IDictionary]) {
            $templateEntry = $templates[$Key]
        } else {
            $property = $templates.PSObject.Properties | Where-Object { $_.Name -eq $Key }
            if ($property) {
                $templateEntry = $property.Value
            }
        }

        if (-not $templateEntry) {
            throw "Template key '$Key' not found in config."
        }

        if ($templateEntry -is [string]) {
            return @{
                path = $templateEntry
            }
        }

        if (-not ($templateEntry.PSObject.Properties.Name -contains "path")) {
            throw "Template definition for '$Key' must include a 'path'."
        }

        return @{
            path             = $templateEntry.path
            render_extension = $templateEntry.render_extension
            output_subdir    = $templateEntry.output_subdir
        }
    }

    $fallback = Get-ConfigValue -Key "template_path"
    if ($fallback) {
        return @{
            path = $fallback
        }
    }

    throw "No project/template path provided. Pass -ProjectPath, -TemplateKey, or set 'template_path'/'templates' in config."
}

$templateDefinition = Resolve-TemplateDefinition -ExplicitPath $ProjectPath -Key $TemplateKey
$projectSource = $templateDefinition.path
$projectFull = Resolve-RepoPath $projectSource
if (-not (Test-Path $projectFull)) {
    throw "Project/template file not found at '$projectFull'."
}

$outputRoot = Resolve-RepoPath (Get-ConfigValue -Key "output_root" -Fallback "outputs/audio")
if (-not (Test-Path $outputRoot)) {
    New-Item -ItemType Directory -Path $outputRoot -Force | Out-Null
}

if (-not $OutputName) {
    $OutputName = Get-Date -Format "yyyyMMdd_HHmmss"
}

$outputBaseRoot = $outputRoot
if ($templateDefinition.output_subdir) {
    $outputBaseRoot = Join-Path $outputRoot $templateDefinition.output_subdir
    if (-not (Test-Path $outputBaseRoot)) {
        New-Item -ItemType Directory -Path $outputBaseRoot -Force | Out-Null
    }
}

$sessionDir = Join-Path $outputBaseRoot $OutputName
New-Item -ItemType Directory -Path $sessionDir -Force | Out-Null

$renderExt = if ($templateDefinition.render_extension) { $templateDefinition.render_extension } else { Get-ConfigValue -Key "render_extension" -Fallback ".wav" }
if (-not $renderExt.StartsWith(".")) {
    $renderExt = ".$renderExt"
}

$renderBasePath = Join-Path $sessionDir $OutputName
$renderOutputPath = "$renderBasePath$renderExt"
$sessionProjectPath = Join-Path $sessionDir "$OutputName.rpp"
Copy-Item -Path $projectFull -Destination $sessionProjectPath -Force

if (-not $SkipRenderFileRewrite) {
    $projectContent = Get-Content -Path $sessionProjectPath -Raw
    $replacementLine = "RENDER_FILE ""$renderOutputPath"""
    if ($projectContent -match 'RENDER_FILE\s+".*"') {
        $projectContent = [System.Text.RegularExpressions.Regex]::Replace($projectContent, 'RENDER_FILE\s+".*"', $replacementLine, 1)
    } else {
        $projectContent = "$replacementLine`r`n$projectContent"
    }
    Set-Content -Path $sessionProjectPath -Value $projectContent -Encoding UTF8
}

$stdoutLog = Join-Path $sessionDir "render.log"
$stderrLog = Join-Path $sessionDir "render-error.log"

Write-Host "Starting REAPER render..."
Write-Host "  Template : $projectFull"
Write-Host "  Session  : $sessionProjectPath"
Write-Host "  Output   : $renderOutputPath"
Write-Host "  REAPER   : $reaperExe"

$arguments = @("-renderproject", $sessionProjectPath)
$startTime = Get-Date
$exitCode = 0
$duration = [TimeSpan]::Zero

if ($DryRun) {
    Write-Host "[DRY-RUN] Skipping REAPER invocation. Metadata/output paths still generated."
    New-Item -ItemType File -Path $renderOutputPath -Force | Out-Null
    "Dry run executed at $($startTime.ToString("o"))" | Set-Content -Path $stdoutLog -Encoding UTF8
    "" | Set-Content -Path $stderrLog -Encoding UTF8
} else {
    if (Test-Path $stdoutLog) { Remove-Item $stdoutLog -Force }
    if (Test-Path $stderrLog) { Remove-Item $stderrLog -Force }
    $process = Start-Process -FilePath $reaperExe `
        -ArgumentList $arguments `
        -RedirectStandardOutput $stdoutLog `
        -RedirectStandardError $stderrLog `
        -NoNewWindow `
        -Wait `
        -PassThru
    $duration = (Get-Date) - $startTime
    $exitCode = $process.ExitCode
}

$renderExists = Test-Path $renderOutputPath
if (-not $renderExists) {
    Write-Warning "Render output not found at '$renderOutputPath'. Check REAPER render settings."
}

$metadata = [ordered]@{
    template_path          = (Resolve-Path $projectFull).ProviderPath.Replace("$repoRoot\", "")
    template_key           = $TemplateKey
    template_output_subdir = $templateDefinition.output_subdir
    session_project        = (Resolve-Path $sessionProjectPath).ProviderPath.Replace("$repoRoot\", "")
    output_file            = if ($renderExists) { (Resolve-Path $renderOutputPath).ProviderPath.Replace("$repoRoot\", "") } else { $renderOutputPath }
    reaper_path            = $reaperExe
    started_at             = $startTime.ToString("o")
    duration_seconds       = [Math]::Round($duration.TotalSeconds, 2)
    exit_code              = $exitCode
    render_success         = ($DryRun -or ($exitCode -eq 0 -and $renderExists))
    dry_run                = [bool]$DryRun
    skip_file_rewrite      = [bool]$SkipRenderFileRewrite
    config_path            = if ($configFullPath) { $configFullPath.Replace("$repoRoot\", "") } else { $null }
    log_stdout             = if (Test-Path $stdoutLog) { (Resolve-Path $stdoutLog).ProviderPath.Replace("$repoRoot\", "") } else { $stdoutLog }
    log_stderr             = if (Test-Path $stderrLog) { (Resolve-Path $stderrLog).ProviderPath.Replace("$repoRoot\", "") } else { $stderrLog }
}

$metadataPath = Join-Path $sessionDir "metadata.json"
$metadata | ConvertTo-Json -Depth 4 | Set-Content -Path $metadataPath -Encoding UTF8

if ($metadata.render_success) {
    if ($DryRun) {
        Write-Host "[OK] Dry-run completed. Output placeholder: $renderOutputPath"
    } else {
        Write-Host "[OK] Render completed in $([Math]::Round($duration.TotalSeconds,2))s."
        Write-Host "Result: $renderOutputPath"
    }
} else {
    Write-Warning "[WARN] Render finished with exit code $exitCode. Inspect REAPER log or GUI for details."
}

Write-Host "Metadata saved to $metadataPath"