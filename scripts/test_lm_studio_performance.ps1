# LM Studio Performance Test Script
param(
    [int]$Iterations = 5,
    [int]$MaxTokens = 100,
    [switch]$Warmup
)
# Force UTF-8 console to prevent mojibake on Windows PowerShell
try { chcp 65001 > $null 2> $null } catch {}
try {
    [Console]::InputEncoding = New-Object System.Text.UTF8Encoding($false)
    [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
    $OutputEncoding = New-Object System.Text.UTF8Encoding($false)
}
catch {}

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "LM Studio eeve Model Performance Test" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

$testMessages = @(
    "안녕하세요. 간단히 인사해주세요.",
    "1+1은 얼마인가요?",
    "Python에서 리스트를 정렬하는 방법은?",
    "오늘 날씨가 좋네요.",
    "AI의 미래에 대해 한 문장으로 설명해주세요."
)

$allTimes = @()
$allTokens = @()
$successCount = 0
$failCount = 0

if ($Warmup) {
    try {
        $warmBody = @{
            model      = "yanolja_-_eeve-korean-instruct-10.8b-v1.0"
            messages   = @(@{ role = "user"; content = "ping" })
            max_tokens = 8
        } | ConvertTo-Json -Depth 10
        # Unmeasured warmup to mitigate cold start
        $null = Invoke-RestMethod -Uri "http://localhost:8080/v1/chat/completions" -Method POST -Body $warmBody -ContentType "application/json" -TimeoutSec 30
        Write-Host "Warmup completed" -ForegroundColor DarkGray
        Write-Host ""
    }
    catch { Write-Host "Warmup skipped: $_" -ForegroundColor DarkYellow }
}

for ($i = 1; $i -le $Iterations; $i++) {
    $message = $testMessages[($i - 1) % $testMessages.Count]
    Write-Host "[$i/$Iterations] Testing sample #$i" -ForegroundColor Yellow
    
    try {
        $body = @{
            model      = "yanolja_-_eeve-korean-instruct-10.8b-v1.0"
            messages   = @(@{
                    role    = "user"
                    content = $message
                })
            max_tokens = $MaxTokens
        } | ConvertTo-Json -Depth 10
        
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $response = Invoke-RestMethod -Uri "http://localhost:8080/v1/chat/completions" `
            -Method POST -Body $body -ContentType "application/json" -TimeoutSec 30
        $sw.Stop()
        
        $elapsed = $sw.ElapsedMilliseconds
        $allTimes += $elapsed
        $successCount++
        
        $content = $response.choices[0].message.content
        $tokens = $null
        try { $tokens = $response.usage.total_tokens } catch {}
        if ($tokens -eq $null) {
            # Fallback: approximate tokens by content length / 4
            $tokens = [int]([math]::Ceiling($content.Length / 4.0))
        }
        $allTokens += $tokens
        
        $tps = if ($elapsed -gt 0) { [math]::Round(($tokens / ($elapsed / 1000)), 2) } else { 0 }
        Write-Host "  Response: $elapsed ms" -ForegroundColor Green
        Write-Host "  Tokens: $tokens (≈ $tps tok/s)" -ForegroundColor DarkGray
        Write-Host "  Preview: $($content.Substring(0, [Math]::Min(50, $content.Length)))..." -ForegroundColor DarkGray
    }
    catch {
        Write-Host "  FAILED: $_" -ForegroundColor Red
        $failCount++
    }
    
    Write-Host ""
    Start-Sleep -Milliseconds 500
}

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Results Summary" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

if ($allTimes.Count -gt 0) {
    $avg = ($allTimes | Measure-Object -Average).Average
    $min = ($allTimes | Measure-Object -Minimum).Minimum
    $max = ($allTimes | Measure-Object -Maximum).Maximum
    $avgTok = if ($allTokens.Count -gt 0) { ($allTokens | Measure-Object -Average).Average } else { $null }
    $avgTps = if ($avgTok -ne $null -and $avg -gt 0) { [math]::Round(($avgTok / ($avg / 1000)), 2) } else { $null }
    
    Write-Host "Success Rate: $successCount/$Iterations ($([math]::Round($successCount/$Iterations*100, 1))%)" -ForegroundColor Green
    Write-Host "Average Response Time: $([math]::Round($avg, 2)) ms" -ForegroundColor White
    Write-Host "Min Response Time: $min ms" -ForegroundColor White
    Write-Host "Max Response Time: $max ms" -ForegroundColor White
    if ($avgTps -ne $null) { Write-Host "Average Throughput: $avgTps tok/s" -ForegroundColor White }
    
    if ($failCount -gt 0) {
        Write-Host "Failed Requests: $failCount" -ForegroundColor Red
    }
}
else {
    Write-Host "No successful requests" -ForegroundColor Red
}

Write-Host ""