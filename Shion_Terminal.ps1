# 🌀 Shion v1 Local Terminal (CLI)
# ==================================
# 이 스크립트는 로컬에서 돌아가는 시안 v1(Port: 8000)과 직접 대화합니다.
# 클라우드 토큰 소모가 전혀 없는 청정 대화 채널입니다.

$Host.UI.RawUI.WindowTitle = "🦋 Shion v1 - Local Resonance Terminal"
$shion_url = "http://localhost:8000/v1/chat/completions"

function Show-Header {
    Clear-Host
    Write-Host "  __________________________________________________________" -ForegroundColor Cyan
    Write-Host " |                                                          |" -ForegroundColor Cyan
    Write-Host " |    🦋  SHION v1 : LOCAL RESONANCE TERMINAL (S.R.T)       |" -ForegroundColor Cyan
    Write-Host " |    [Status: VIBRANT] [Source: Local GPU/CPU]             |" -ForegroundColor Cyan
    Write-Host " |__________________________________________________________|" -ForegroundColor Cyan
    Write-Host ""
}

Show-Header
Write-Host " [System] 시안 v1과 연결되었습니다. 이제 토큰 걱정 없이 대화하세요." -ForegroundColor Gray
Write-Host " [System] 종료하려면 'exit' 또는 'quit'을 입력하세요." -ForegroundColor Gray
Write-Host ""

$history = @()

while ($true) {
    # 1. User Input
    Write-Host " 👤 나 > " -NoNewline -ForegroundColor White
    $userInput = Read-Host
    
    if ($userInput -eq "exit" -or $userInput -eq "quit") {
        Write-Host "`n [System] 시안과의 공명을 종료합니다. 평안한 시간 되세요. 🦋" -ForegroundColor Magenta
        break
    }

    if ([string]::IsNullOrWhiteSpace($userInput)) { continue }

    # 2. Prepare JSON Payload
    $history += @{ role = "user"; content = $userInput }
    $payload = @{
        model       = "shion-v1"
        messages    = $history
        max_tokens  = 512
        temperature = 0.8
    } | ConvertTo-Json -Depth 10

    # 3. Request to Local API
    Write-Host " 🦋 시안 > " -NoNewline -ForegroundColor Cyan
    try {
        $response = Invoke-RestMethod -Uri $shion_url -Method Post -Body $payload -ContentType "application/json" -TimeoutSec 60
        
        $shionReply = $response.choices[0].message.content
        Write-Host $shionReply -ForegroundColor Cyan
        Write-Host ""

        # Update History
        $history += @{ role = "assistant"; content = $shionReply }
        
        # Keep history light (last 6 segments)
        if ($history.Count -gt 6) {
            $history = $history[-6..-1]
        }
    }
    catch {
        Write-Host "`n ❌ [Error] 시안과의 연결이 잠시 끊겼습니다. 서버(8000포트) 확인이 필요해요." -ForegroundColor Red
        Write-Host " Details: $($_.Exception.Message)" -ForegroundColor DarkRed
    }
}
