param(
    [string]$Server = 'http://127.0.0.1:8091',
    [int]$Count = 5,
    [switch]$SuccessOnly,
    [switch]$FailedOnly,
    [string]$Filter,
    [string]$OutJson,
    [string]$OutJsonl,
    [switch]$Append
)

$ErrorActionPreference = 'Stop'
try {
    $res = Invoke-RestMethod -UseBasicParsing -Uri "$Server/api/results" -TimeoutSec 10
    $items = @()
    if ($res -and $res.results) { $items = $res.results }
    if ($SuccessOnly -and -not $FailedOnly) { $items = $items | Where-Object { $_.success -eq $true } }
    elseif ($FailedOnly -and -not $SuccessOnly) { $items = $items | Where-Object { $_.success -ne $true } }
    if ($Filter -and $Filter.Trim().Length -gt 0) {
        $pat = [regex]::Escape($Filter)
        $items = $items | Where-Object {
            ($_ -join ' ') -match $pat
        }
    }
    # 정렬: submitted_at 기준(없으면 task_id로 안정 정렬)
    $items = $items | Sort-Object -Property @{Expression = { $_.submitted_at }; Descending = $true }, @{Expression = { $_.task_id }; Descending = $true }
    $items = $items | Select-Object -First $Count

    if (-not $items -or $items.Count -eq 0) {
        Write-Host "No results found." -ForegroundColor Yellow
        exit 0
    }

    $summary = $items | ForEach-Object {
        $typeVal = '(n/a)'
        $sumVal = '(n/a)'
        if ($_.data) {
            if ($_.data.message) { $typeVal = $_.data.message; $sumVal = $_.data.message }
            elseif ($_.data.action) { $typeVal = $_.data.action }
            # Heuristics for common RPA outputs
            if ($_.data.slept) { $sumVal = "slept=" + [string]$_.data.slept }
            elseif ($_.data.path -and $_.data.width -and $_.data.height) { $sumVal = "screenshot " + [string]$_.data.width + "x" + [string]$_.data.height }
            elseif ($_.data.engine -and $_.data.chars) { $sumVal = "ocr " + [string]$_.data.engine + " chars=" + [string]$_.data.chars }
            elseif ($_.data.engine -and $_.data.count) { $sumVal = "ocr " + [string]$_.data.engine + " count=" + [string]$_.data.count }
        }
        [pscustomobject]@{
            task_id      = $_.task_id
            success      = $_.success
            type         = $typeVal
            summary      = $sumVal
            submitted_at = $_.submitted_at
        }
    }
    $json = $summary | ConvertTo-Json -Depth 6
    if ($OutJson -and $OutJson.Trim().Length -gt 0) {
        $dir = Split-Path -Parent $OutJson
        if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
        if ($Append) { Add-Content -LiteralPath $OutJson -Value $json -Encoding UTF8 }
        else { Set-Content -LiteralPath $OutJson -Value $json -Encoding UTF8 }
    }
    if ($OutJsonl -and $OutJsonl.Trim().Length -gt 0) {
        $dir2 = Split-Path -Parent $OutJsonl
        if ($dir2 -and -not (Test-Path -LiteralPath $dir2)) { New-Item -ItemType Directory -Path $dir2 -Force | Out-Null }
        # 각 항목을 JSONL로 한 줄씩 기록
        foreach ($row in $summary) {
            $line = $row | ConvertTo-Json -Depth 6 -Compress
            Add-Content -LiteralPath $OutJsonl -Value $line -Encoding UTF8
        }
    }
    $json
    exit 0
}
catch {
    Write-Error $_.Exception.Message
    exit 1
}
