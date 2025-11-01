param(
    [ValidateSet('disabled','observe','enforce')]
    [string]$Mode = 'observe'
)

$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [System.Text.UTF8Encoding]::UTF8; $OutputEncoding = [System.Text.UTF8Encoding]::UTF8 } catch {}

$cfgDir = Join-Path $PSScriptRoot '..' | Resolve-Path
$cfgDir = Join-Path $cfgDir 'configs'
$cfgPath = Join-Path $cfgDir 'resonance_config.json'
$examplePath = Join-Path $cfgDir 'resonance_config.example.json'

if (-not (Test-Path -LiteralPath $cfgPath)) {
    if (Test-Path -LiteralPath $examplePath) {
        Copy-Item -Force -Path $examplePath -Destination $cfgPath
        Write-Host "Created configs/resonance_config.json from example." -ForegroundColor Yellow
    } else {
        New-Item -ItemType Directory -Path $cfgDir -Force | Out-Null
        '{"active_mode":"observe","default_policy":"quality-first","policies":{"quality-first":{"min_quality":0.8,"require_evidence":true,"max_latency_ms":8000}}}' | Out-File -FilePath $cfgPath -Encoding utf8 -Force
        Write-Host "Created minimal configs/resonance_config.json." -ForegroundColor Yellow
    }
}

if (-not (Test-Path -LiteralPath $cfgPath)) { throw "Could not locate or create $cfgPath" }

$json = Get-Content -LiteralPath $cfgPath -Raw -Encoding UTF8 | ConvertFrom-Json
$prev = $json.active_mode
$json | Add-Member -NotePropertyName 'active_mode' -NotePropertyValue $Mode -Force

$tmp = $json | ConvertTo-Json -Depth 6
[System.IO.File]::WriteAllText($cfgPath, $tmp, [System.Text.Encoding]::UTF8)

Write-Host "Resonance mode updated:" -ForegroundColor Green
Write-Host ("  {0} -> {1}" -f ($prev ? $prev : 'unknown'), $Mode) -ForegroundColor Green
Write-Host ("  Path: {0}" -f (Resolve-Path $cfgPath)) -ForegroundColor DarkGray

exit 0

