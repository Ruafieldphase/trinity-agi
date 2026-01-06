# GPU Monitoring Integration
# Collects GPU metrics using nvidia-smi and outputs to JSON
# Part of Phase 3+ Real-Time Monitoring Enhancement

param(
    [string]$OutJson = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\gpu_usage_latest.json",
    [switch]$Quiet
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Stop"

function Get-GPUMetrics {
    try {
        # Check if nvidia-smi exists
        $nvidiaSmi = Get-Command "nvidia-smi" -ErrorAction SilentlyContinue
        if (-not $nvidiaSmi) {
            return @{
                available = $false
                error     = "nvidia-smi not found (NVIDIA GPU drivers not installed or not in PATH)"
            }
        }

        # Query GPU metrics in CSV format
        $query = "index,name,utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw,power.limit"
        # Use strict csv,noheader,nounits to avoid spacing issues; handle multi-GPU by selecting first line
        $output = & nvidia-smi --query-gpu=$query --format=csv, noheader, nounits 2>&1

        if ($LASTEXITCODE -ne 0) {
            return @{
                available = $false
                error     = "nvidia-smi command failed: $output"
            }
        }

        # Parse CSV output (support multi-line output -> pick first GPU)
        $lines = @()
        if ($output -is [System.Array]) { $lines = $output | Where-Object { $_ -and $_.Trim() -ne '' } }
        else { $lines = @($output) }
        if ($lines.Count -eq 0) {
            return @{
                available = $false
                error     = "nvidia-smi returned no data"
            }
        }
        $firstLine = $lines[0]
        $fields = $firstLine -split ','
        if ($fields.Count -lt 8) {
            return @{
                available = $false
                error     = "Unexpected nvidia-smi output format"
            }
        }

        return @{
            available                  = $true
            timestamp                  = (Get-Date -Format "o")
            gpu_index                  = [int]($fields[0].Trim())
            gpu_name                   = $fields[1].Trim()
            gpu_utilization_percent    = [int]($fields[2].Trim())
            memory_used_mb             = [int]($fields[3].Trim())
            memory_total_mb            = [int]($fields[4].Trim())
            temperature_celsius        = [int]($fields[5].Trim())
            power_draw_watts           = [double]($fields[6].Trim())
            power_limit_watts          = [double]($fields[7].Trim())
            memory_utilization_percent = [math]::Round(([int]($fields[3].Trim()) / [int]($fields[4].Trim())) * 100, 2)
            power_utilization_percent  = [math]::Round(([double]($fields[6].Trim()) / [double]($fields[7].Trim())) * 100, 2)
        }
    }
    catch {
        return @{
            available = $false
            error     = $_.Exception.Message
        }
    }
}

# Main
$metrics = Get-GPUMetrics

# Save to JSON
$outDir = Split-Path $OutJson -Parent
if (-not (Test-Path $outDir)) {
    New-Item -ItemType Directory -Path $outDir -Force | Out-Null
}

$metrics | ConvertTo-Json -Depth 5 | Set-Content $OutJson -Encoding UTF8

# Output to console
if (-not $Quiet) {
    if ($metrics.available) {
        Write-Host "✓ GPU Metrics Collected" -ForegroundColor Green
        Write-Host "  Name: $($metrics.gpu_name)"
        Write-Host "  Utilization: $($metrics.gpu_utilization_percent)%"
        Write-Host "  Memory: $($metrics.memory_used_mb) MB / $($metrics.memory_total_mb) MB ($($metrics.memory_utilization_percent)%)"
        Write-Host "  Temperature: $($metrics.temperature_celsius)°C"
        Write-Host "  Power: $($metrics.power_draw_watts) W / $($metrics.power_limit_watts) W ($($metrics.power_utilization_percent)%)"
    }
    else {
        Write-Host "⚠ GPU Metrics Not Available" -ForegroundColor Yellow
        Write-Host "  Reason: $($metrics.error)"
    }
    Write-Host "  Output: $OutJson" -ForegroundColor Cyan
}

exit 0