param(
    [string]$Server = 'http://127.0.0.1:8091',
    [int]$Count = 20,
    [switch]$SuccessOnly
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$out = Join-Path -Path (Join-Path $WorkspaceRoot "outputs") -ChildPath ("results_snapshot_{0}.json" -f $ts)

$ErrorActionPreference = 'Stop'
try {
    $scriptPath = Join-Path $PSScriptRoot 'show_latest_results.ps1'
    $psArgs = @('-NoProfile','-ExecutionPolicy','Bypass','-File', '"' + $scriptPath + '"', '-Server', $Server, '-Count', [string]$Count, '-OutJson', '"' + $out + '"')
    if ($SuccessOnly) { $psArgs += '-SuccessOnly' }
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = 'powershell'
    $psi.Arguments = ($psArgs -join ' ')
    $psi.RedirectStandardOutput = $true
    $psi.UseShellExecute = $false
    $p = [System.Diagnostics.Process]::Start($psi)
    $stdout = $p.StandardOutput.ReadToEnd()
    $p.WaitForExit()
    if ($p.ExitCode -eq 0 -and (Test-Path -LiteralPath $out)) {
        Write-Host ("Saved snapshot: {0}" -f $out) -ForegroundColor Green
        Write-Output $stdout
        exit 0
    }
    else {
        if (Test-Path -LiteralPath $out) {
            Write-Host ("Snapshot path prepared but source failed: {0}" -f $out) -ForegroundColor Yellow
        }
        Write-Error ("show_latest_results.ps1 exited with code {0}" -f $p.ExitCode)
        Write-Output $stdout
        exit 1
    }
}
catch {
    Write-Error $_.Exception.Message
    exit 1
}