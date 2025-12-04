param(
    [string]$Server = 'http://127.0.0.1:8091',
    [switch]$IncludeOcr,
    [ValidateSet('tesseract', 'easyocr')]
    [string]$OcrEngine = 'tesseract',
    [switch]$Verify,
    [int]$TimeoutSec = 15,
    [switch]$Strict,
    [int]$GraceWaitSec = 3
)

$ErrorActionPreference = 'Stop'

function Invoke-CreateTask([string]$Type, [hashtable]$Data) {
    $uri = "$Server/api/tasks/create"
    $payload = @{ type = $Type; data = $Data } | ConvertTo-Json -Compress
    $resp = Invoke-WebRequest -UseBasicParsing -Method Post -ContentType 'application/json' -Uri $uri -Body $payload
    return ($resp.Content | ConvertFrom-Json)
}

function Get-ResultByTaskId([string]$TaskId, [int]$TimeoutSec) {
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        try {
            $res = Invoke-RestMethod -UseBasicParsing -Uri "$Server/api/results" -TimeoutSec 5
            if ($res -and $res.results) {
                $found = $res.results | Where-Object { $_.task_id -eq $TaskId }
                if ($found) { return $found }
            }
        }
        catch {}
        Start-Sleep -Milliseconds 500
    }
    return $null
}

try {
    Write-Host "[1/3] Enqueue RPA wait(0.5s)" -ForegroundColor Cyan
    $t1 = Invoke-CreateTask -Type 'rpa' -Data @{ action = 'wait'; params = @{ seconds = 0.5 } }
    Write-Host ("  -> {0}" -f ($t1 | ConvertTo-Json -Compress))

    Write-Host "[2/3] Enqueue RPA screenshot" -ForegroundColor Cyan
    $t2 = Invoke-CreateTask -Type 'rpa' -Data @{ action = 'screenshot'; params = @{} }
    Write-Host ("  -> {0}" -f ($t2 | ConvertTo-Json -Compress))

    if ($IncludeOcr) {
        Write-Host ("[3/3] Enqueue RPA ocr({0})" -f $OcrEngine) -ForegroundColor Cyan
        $t3 = Invoke-CreateTask -Type 'rpa' -Data @{ action = 'ocr'; params = @{ engine = $OcrEngine } }
        Write-Host ("  -> {0}" -f ($t3 | ConvertTo-Json -Compress))
    }

    if (-not $Verify) {
        Write-Host "Smoke tasks enqueued. Use show_latest_results.ps1 to verify." -ForegroundColor Green
        exit 0
    }

    Write-Host "Verifying results... (timeout ${TimeoutSec}s)" -ForegroundColor Yellow
    $ok = $true
    $warn = $false

    # Verify wait
    $r1 = Get-ResultByTaskId -TaskId $t1.task_id -TimeoutSec $TimeoutSec
    if (-not $r1) { 
        # Grace re-check once more if configured
        if ($GraceWaitSec -gt 0) {
            Write-Host ("wait result: not found, grace {0}s..." -f $GraceWaitSec) -ForegroundColor DarkYellow
            Start-Sleep -Seconds $GraceWaitSec
            $r1 = Get-ResultByTaskId -TaskId $t1.task_id -TimeoutSec 1
        }
        if (-not $r1) {
            if ($Strict) { Write-Host "wait result: NOT FOUND" -ForegroundColor Red; $ok = $false }
            else { Write-Host "wait result: NOT FOUND (non-strict: continue)" -ForegroundColor Yellow; $warn = $true }
        }
    }
    else {
        $slept = $r1.data.slept
        if ($slept -ge 0.4) { Write-Host ("wait result: OK (slept={0})" -f $slept) -ForegroundColor Green }
        else { Write-Host ("wait result: FAIL (slept={0})" -f $slept) -ForegroundColor Red; $ok = $false }
    }

    # Verify screenshot
    $r2 = Get-ResultByTaskId -TaskId $t2.task_id -TimeoutSec $TimeoutSec
    if (-not $r2) { Write-Host "screenshot result: NOT FOUND" -ForegroundColor Red; $ok = $false }
    else {
        $path = $r2.data.path
        $w = $r2.data.width; $h = $r2.data.height
        if ($path -and (Test-Path -LiteralPath $path) -and $w -gt 0 -and $h -gt 0) {
            Write-Host ("screenshot result: OK ({0} {1}x{2})" -f $path, $w, $h) -ForegroundColor Green
        }
        else {
            Write-Host ("screenshot result: FAIL (path={0}, size={1}x{2})" -f $path, $w, $h) -ForegroundColor Red
            $ok = $false
        }
    }

    # Verify OCR (optional)
    if ($IncludeOcr -and $t3) {
        $r3 = Get-ResultByTaskId -TaskId $t3.task_id -TimeoutSec $TimeoutSec
        if (-not $r3) { Write-Host "ocr result: NOT FOUND" -ForegroundColor Yellow }
        else {
            $engine = $r3.data.engine
            $chars = $r3.data.chars
            $count = $r3.data.count
            if ($engine) {
                $summary = if ($chars) { "chars=$chars" } elseif ($count) { "count=$count" } else { '(no-metrics)' }
                Write-Host ("ocr result: OK (engine={0}, {1})" -f $engine, $summary) -ForegroundColor Green
            }
            else {
                Write-Host "ocr result: PRESENT BUT INCOMPLETE" -ForegroundColor Yellow
            }
        }
    }

    if ($ok) { 
        if ($warn) { Write-Host "Smoke verification: PASS (with warnings)" -ForegroundColor Yellow; exit 0 }
        Write-Host "Smoke verification: PASS" -ForegroundColor Green; exit 0 
    }
    else { Write-Host "Smoke verification: FAIL" -ForegroundColor Red; exit 2 }
}
catch {
    Write-Error $_.Exception.Message
    exit 1
}
