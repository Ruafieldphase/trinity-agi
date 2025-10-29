Add-Type -AssemblyName Microsoft.VisualBasic | Out-Null
$wshell = New-Object -ComObject WScript.Shell

function Try-Activate {
    param([string[]]$Titles)
    foreach ($t in $Titles) {
        if ($wshell.AppActivate($t)) { Start-Sleep -Milliseconds 200; return $true }
    }
    # Try by process
    $p = Get-Process -Name 'Code', 'Code - Insiders' -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($p) {
        try { [Microsoft.VisualBasic.Interaction]::AppActivate($p.Id) | Out-Null; Start-Sleep -Milliseconds 200; return $true } catch {}
    }
    return $false
}

function Send-Reload {
    param([string]$phrase)
    $wshell.SendKeys('^+p'); Start-Sleep -Milliseconds 300
    $wshell.SendKeys($phrase); Start-Sleep -Milliseconds 200
    $wshell.SendKeys('{ENTER}')
}

if (-not (Try-Activate @('Visual Studio Code', 'VS Code', 'Code'))) {
    Write-Host '❌ VS Code window not found/activated.' -ForegroundColor Red
    exit 1
}

Write-Host "Opening Command Palette and triggering Reload Window..." -ForegroundColor Cyan
try {
    Send-Reload -phrase 'Developer: Reload Window'
    Start-Sleep -Seconds 1
    # Fallbacks (Korean UI or short form)
    Send-Reload -phrase '개발자: 창 다시 로드'
    Start-Sleep -Seconds 1
    Send-Reload -phrase 'Reload Window'
    Write-Host "Reload command sent (one of the variants)." -ForegroundColor Green
}
catch {
    Write-Host "❌ Failed to send reload command: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
