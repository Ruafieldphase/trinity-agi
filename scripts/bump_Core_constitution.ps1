param(
    [string]$PolicyFile = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\policy\core_constitution.json",
    [ValidateSet('major', 'minor', 'patch')]
    [string]$Bump = 'minor',
    [int]$ReviewCadenceDays,
    [string]$SunsetDate,
    [string]$Note
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $PolicyFile)) { throw "Policy file not found: $PolicyFile" }

function Get-VersionParts($v) {
    if (-not $v) { return @{major = 1; minor = 0; patch = 0 } }
    $parts = $v.Split('.')
    return @{ major = [int]$parts[0]; minor = [int]$parts[1]; patch = [int]$parts[2] }
}

function Update-Version($obj, $kind) {
    switch ($kind) {
        'major' { $obj.major += 1; $obj.minor = 0; $obj.patch = 0 }
        'minor' { $obj.minor += 1; $obj.patch = 0 }
        'patch' { $obj.patch += 1 }
    }
    return ("{0}.{1}.{2}" -f $obj.major, $obj.minor, $obj.patch)
}

$json = Get-Content -Raw -LiteralPath $PolicyFile | ConvertFrom-Json
$ver = Get-VersionParts $json.version
$newVersion = Update-Version $ver $Bump

if (-not $json.meta) { $json | Add-Member -MemberType NoteProperty -Name meta -Value (@{}) }
if (-not $json.meta.principles) { $json.meta | Add-Member -MemberType NoteProperty -Name principles -Value (@{ hypothesis_not_doctrine = $true; dynamic_equilibrium = $true; anti_dogma = $true }) }
if (-not $json.meta.governance) {
    $json.meta | Add-Member -MemberType NoteProperty -Name governance -Value (@{ last_reviewed_at = ''; review_cadence_days = 14; sunset_date = $null; owners = @('ethics', 'ops', 'research'); override_policy = @{ allow_override_with_approval = $true; required_approvers = 2; require_audit_log = $true }; experiment_policy = @{ allow_ab_test = $true; require_opt_out = $true; min_risk_class = 'low' }; changelog = @() })
}

$json.version = $newVersion
$json.meta.governance.last_reviewed_at = (Get-Date).ToUniversalTime().ToString('o')
if ($PSBoundParameters.ContainsKey('ReviewCadenceDays')) { $json.meta.governance.review_cadence_days = $ReviewCadenceDays }
if ($PSBoundParameters.ContainsKey('SunsetDate')) { $json.meta.governance.sunset_date = $SunsetDate }

$entry = @{ at = (Get-Date).ToUniversalTime().ToString('o'); by = $env:USERNAME; bump = $Bump; version = $newVersion; note = $Note }
$json.meta.governance.changelog += $entry

# Pretty-print JSON
$json | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $PolicyFile -Encoding UTF8

Write-Host "[Bump] version=$newVersion; last_reviewed_at=$($entry.at)" -ForegroundColor Green
if ($Note) { Write-Host "[Note] $Note" -ForegroundColor DarkGray }