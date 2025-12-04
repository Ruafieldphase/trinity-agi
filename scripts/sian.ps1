<#
.SYNOPSIS
    Sian CLI PowerShell 래퍼
.DESCRIPTION
    Gemini API를 통해 메타층 AI 오케스트레이터와 대화
.PARAMETER Prompt
    Gemini에게 보낼 프롬프트
.PARAMETER Model
    사용할 모델 (기본: gemini-2.0-flash)
.PARAMETER Thinking
    추론 모델 사용
.PARAMETER Pro
    고급 모델 사용
.PARAMETER Quiet
    응답만 출력
.EXAMPLE
    .\sian.ps1 "Hello, Sian!"
.EXAMPLE
    .\sian.ps1 -Thinking "복잡한 논리 문제를 풀어주세요"
.EXAMPLE
    .\sian.ps1 -Pro "고급 분석이 필요한 작업"
#>
param(
    [Parameter(Position = 0, ValueFromRemainingArguments = $true)]
    [string[]]$Prompt,
    
    [string]$Model = "gemini-2.0-flash",
    
    [switch]$Thinking,
    
    [switch]$Pro,
    
    [switch]$Quiet,
    
    [switch]$OutMd,
    
    [string]$OutDir
)

$scriptDir = Split-Path -Parent $PSCommandPath
$workspace = Split-Path -Parent $scriptDir
$defaultOutDir = Join-Path $workspace "outputs\sian"
if (-not $OutDir -or [string]::IsNullOrWhiteSpace($OutDir)) { $OutDir = $defaultOutDir }
$sianScript = Join-Path $scriptDir "sian_cli.py"

if (-not (Test-Path $sianScript)) {
    Write-Host "❌ sian_cli.py를 찾을 수 없습니다: $sianScript" -ForegroundColor Red
    exit 1
}

# Python 스크립트 호출
$pythonArgs = @()
if ($Thinking) { $pythonArgs += "--thinking" }
if ($Pro) { $pythonArgs += "--pro" }
if ($Quiet) { $pythonArgs += "--quiet" }
if ($Model -ne "gemini-2.0-flash") { $pythonArgs += "--model", $Model }

try {
    if ($Prompt) { $pythonArgs += $Prompt }
    # Python 실행 및 출력 캡처 (stderr 포함)
    $result = & python $sianScript @pythonArgs 2>&1
    $exitCode = $LASTEXITCODE

    # 화면 출력 (Quiet 아닐 때)
    if (-not $Quiet) {
        $result | Write-Output
    }

    # MD 저장 옵션 처리
    if ($OutMd) {
        try {
            if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir -Force | Out-Null }
            $ts = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
            $fileBase = "sian_${ts}.md"
            $filePath = Join-Path $OutDir $fileBase
            $latestPath = Join-Path $OutDir "sian_latest.md"

            $modelSuffix = ""
            if ($Thinking) { $modelSuffix += " (thinking)" }
            if ($Pro) { $modelSuffix += " (pro)" }
            $promptJoined = if ($Prompt) { ($Prompt -join ' ') } else { '' }
            $promptLine = if ($Prompt) { "- Prompt: `"$promptJoined`"" } else { "- Prompt: (stdin)" }

            $headerLines = @()
            $headerLines += "# SiAN Thinking Output"
            $headerLines += ""
            $headerLines += "- Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss K')"
            $headerLines += "- Model: $Model$modelSuffix"
            $headerLines += $promptLine
            $headerLines += ""
            $headerLines += "---"
            $headerLines += ""
            $headerLines += "````markdown"
            $headerLines += "$result"
            $headerLines += "````"
            $header = $headerLines -join "`n"

            Set-Content -Path $filePath -Value $header -Encoding UTF8
            # 최신 링크/복사본 갱신
            Copy-Item -Path $filePath -Destination $latestPath -Force
            if (-not $Quiet) { Write-Host "`n📝 Saved: $filePath`n📎 Latest: $latestPath" -ForegroundColor Cyan }
        }
        catch {
            if (-not $Quiet) { Write-Host "⚠️  Failed to save MD output: $($_.Exception.Message)" -ForegroundColor Yellow }
        }
    }

    exit $exitCode
}
catch {
    if (-not $Quiet) { Write-Host "❌ sian.ps1 error: $($_.Exception.Message)" -ForegroundColor Red }
    exit 1
}
