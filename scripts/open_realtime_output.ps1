param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('md', 'json')]
    [string]$Kind,

    [Parameter(Mandatory = $true)]
    [string]$WorkspaceFolder
)

try {
    $ErrorActionPreference = 'Stop'

    $rel = if ($Kind -eq 'md') {
        'outputs/realtime_resonance_latest.md'
    }
    elseif ($Kind -eq 'json') {
        'outputs/realtime_resonance_latest.json'
    }
    elseif ($Kind -eq 'pipeline-md') {
        'outputs/realtime_pipeline_status.md'
    }
    elseif ($Kind -eq 'pipeline-json') {
        'outputs/realtime_pipeline_status.json'
    }
    else {
        'outputs/realtime_resonance_latest.json'
    }
    $p = Join-Path -Path $WorkspaceFolder -ChildPath $rel

    if (Test-Path -LiteralPath $p) {
        try {
            if (Get-Command code -ErrorAction SilentlyContinue) {
                $argsStr = "--reuse-window `"$p`""
                Start-Process -FilePath code -ArgumentList $argsStr -PassThru | Out-Null
            }
            elseif (Get-Command notepad -ErrorAction SilentlyContinue) {
                Start-Process -FilePath notepad -ArgumentList "`"$p`"" -PassThru | Out-Null
            }
            else {
                Start-Process -FilePath $p -Verb Open -PassThru -ErrorAction SilentlyContinue | Out-Null
            }
        }
        catch {
            Write-Host "(non-fatal) Open failed, but continuing: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "No realtime_pipeline_status.$Kind found at: $p" -ForegroundColor Yellow
        Write-Host "Run: Autopoietic: Real-time Pipeline (no open)" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "(non-fatal) Unexpected error: $($_.Exception.Message)" -ForegroundColor Yellow
}
finally {
    $global:LASTEXITCODE = 0
    if ($host -and ($host.Name -like '*PowerShell*')) {
        try { $host.SetShouldExit(0) } catch {}
    }
    [Environment]::Exit(0)
}
