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
    [Parameter(Position=0, ValueFromRemainingArguments=$true)]
    [string[]]$Prompt,
    
    [string]$Model = "gemini-2.0-flash",
    
    [switch]$Thinking,
    
    [switch]$Pro,
    
    [switch]$Quiet
)

$scriptDir = Split-Path -Parent $PSCommandPath
$sianScript = Join-Path $scriptDir "sian_cli.py"

if (-not (Test-Path $sianScript)) {
    Write-Host "❌ sian_cli.py를 찾을 수 없습니다: $sianScript" -ForegroundColor Red
    exit 1
}

# Python 스크립트 호출
$args = @()
if ($Thinking) { $args += "--thinking" }
if ($Pro) { $args += "--pro" }
if ($Quiet) { $args += "--quiet" }
if ($Model -ne "gemini-2.0-flash") { $args += "--model", $Model }

if ($Prompt) {
    $args += $Prompt
    python $sianScript @args
} else {
    # 프롬프트가 없으면 stdin에서 읽기
    python $sianScript @args
}

exit $LASTEXITCODE
