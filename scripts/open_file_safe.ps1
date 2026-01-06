param(
    [Parameter(Mandatory = $true)]
    [string]$Path
)

# Robust, always-zero-exit file opener for VS Code tasks
# Strategy: code --reuse-window -> default handler (Open verb) -> notepad
# Never fail the task: non-fatal warnings only, exit code forced to 0

function Invoke-OpenFileSafely {
    param([string]$Target)
    try {
        if (-not (Test-Path -LiteralPath $Target)) {
            Write-Host "File not found: $Target" -ForegroundColor Yellow
            return
        }
        try {
            if (Get-Command code -ErrorAction SilentlyContinue) {
                $argsStr = "--reuse-window `"$Target`""
                Start-Process -FilePath code -ArgumentList $argsStr -PassThru | Out-Null
                return
            }
        }
        catch {
            Write-Host "(non-fatal) VS Code open failed: $($_.Exception.Message)" -ForegroundColor Yellow
        }
        try {
            Start-Process -FilePath $Target -Verb Open -PassThru -ErrorAction Stop | Out-Null
            return
        }
        catch {
            Write-Host "(non-fatal) Default handler open failed: $($_.Exception.Message)" -ForegroundColor Yellow
        }
        try {
            if (Get-Command notepad -ErrorAction SilentlyContinue) {
                Start-Process -FilePath notepad -ArgumentList "`"$Target`"" -PassThru | Out-Null
                return
            }
        }
        catch {
            Write-Host "(non-fatal) Notepad open failed: $($_.Exception.Message)" -ForegroundColor Yellow
        }
        Write-Host "(non-fatal) Unable to open file with any method: $Target" -ForegroundColor Yellow
    }
    catch {
        Write-Host "(non-fatal) Unexpected error: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

Invoke-OpenFileSafely -Target $Path

# Force zero exit code for VS Code tasks
$global:LASTEXITCODE = 0
try { if ($host) { $host.SetShouldExit(0) } } catch {}
[Environment]::Exit(0)