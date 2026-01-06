param(
    [string]$Host = "127.0.0.1",
    [int]$Port = 8011,
    [string]$Provider = "stub",
    [string]$Schema = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\ai_binoche_conversation_origin\Core\chatgpt-?보?론철학?분??tools\luon\intent_schema.yaml",
    [string]$Rules = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\ai_binoche_conversation_origin\Core\chatgpt-?보?론철학?분??tools\luon\intent_rules.yaml",
    [string]$LabelMap = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\ai_binoche_conversation_origin\Core\chatgpt-?보?론철학?분??tools\luon\intent_label_map.yaml"
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot



$ErrorActionPreference = "Stop"

# Resolve python executable (prefer .venv)
$venvPython = Join-Path "$WorkspaceRoot" ".venv\Scripts\python.exe"
$pythonExe = if (Test-Path $venvPython) { $venvPython } else { "C:\Python313\python.exe" }
if (-not (Test-Path $pythonExe)) {
    throw "Python executable not found at $pythonExe"
}

$serviceScript = "$WorkspaceRoot\ai_binoche_conversation_origin\Core\chatgpt-?보?론철학?분??tools\luon\intent_shadow_service.py"
$clientScript  = "$WorkspaceRoot\ai_binoche_conversation_origin\Core\chatgpt-?보?론철학?분??tools\luon\intent_shadow_client.py"

if (-not (Test-Path $serviceScript)) { throw "Service script not found: $serviceScript" }
if (-not (Test-Path $clientScript))  { throw "Client script not found: $clientScript" }

$env:ELO_INTENT_SCHEMA    = $Schema
$env:ELO_INTENT_RULES     = $Rules
$env:ELO_INTENT_LABEL_MAP = $LabelMap
$env:ELO_INTENT_PROVIDER  = $Provider
$env:ELO_INTENT_HOST      = $Host
$env:ELO_INTENT_PORT      = $Port.ToString()

$serviceArgs = @($serviceScript)
Write-Host "Starting intent shadow service on http://$Host`:$Port ..."
$serviceProcess = Start-Process -FilePath $pythonExe -ArgumentList $serviceArgs -WindowStyle Hidden -PassThru

try {
    $healthUrl = "http://$Host`:$Port/health"
    Write-Host "Waiting for service to become available ..."
    $maxWaitSeconds = 30
    $elapsed = 0
    while ($elapsed -lt $maxWaitSeconds) {
        try {
            $null = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 5
            Write-Host "Service is up."
            break
        } catch {
            Start-Sleep -Seconds 1
            $elapsed++
        }
    }
    if ($elapsed -ge $maxWaitSeconds) {
        throw "Shadow service did not respond within $maxWaitSeconds seconds."
    }

    # Create temporary sample file
    $sampleFile = New-TemporaryFile
    @"
?스?드 초기?? ?요?니??
추천 ?워??병합 ?업 ?청?니??
지???파?크 ?문???비?? ?립?다.
"@ | Set-Content -Path $sampleFile -Encoding UTF8

    Write-Host "Sending sample queries ..."
    $clientArgs = @($clientScript, "--host", "http://$Host`:$Port", "--input", $sampleFile)
    & $pythonExe $clientArgs

} finally {
    if ($serviceProcess -and -not $serviceProcess.HasExited) {
        Write-Host "Stopping intent shadow service (PID=$($serviceProcess.Id)) ..."
        $serviceProcess.CloseMainWindow() | Out-Null
        Start-Sleep -Seconds 1
        if (-not $serviceProcess.HasExited) {
            Stop-Process -Id $serviceProcess.Id -Force
        }
    }
}