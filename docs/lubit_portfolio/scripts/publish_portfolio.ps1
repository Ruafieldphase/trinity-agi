<#!
.SYNOPSIS
    루빛 포트폴리오를 정적 배포용으로 패키징합니다.
.DESCRIPTION
    1) 시각화 PNG를 최신화하고 2) 대상 폴더를 초기화한 뒤 3) 전체 `lubit_portfolio` 내용을 복사합니다.
    GitHub Pages `docs/` 폴더나 별도 아카이브 디렉터리에 바로 넣을 수 있도록 설계했습니다.
.PARAMETER Destination
    배포 산출물을 둘 경로. 기본값은 저장소 루트의 `publish/lubit_portfolio_dist`입니다.
.PARAMETER Python
    시각화 갱신에 사용할 파이썬 실행 파일 경로. 기본값은 `python`.
.PARAMETER CleanOnly
    true로 지정하면 복사하지 않고 대상 폴더만 비운 후 종료합니다.
.PARAMETER SkipVisuals
    true면 PNG 리젠 단계를 건너뜁니다.
.EXAMPLE
    powershell -File publish_portfolio.ps1
.EXAMPLE
    pwsh ./publish_portfolio.ps1 -Destination ..\docs\lubit_portfolio
#>
param(
    [string]$Destination = "publish/lubit_portfolio_dist",
    [string]$Python = "python",
    [switch]$CleanOnly,
    [switch]$SkipVisuals
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$lubitRoot = Split-Path -Parent $scriptDir
$repoRoot = Split-Path -Parent $lubitRoot
if (-not (Test-Path -LiteralPath $lubitRoot)) {
    Write-Error "lubit_portfolio 디렉터리를 찾을 수 없습니다: $lubitRoot"
    exit 1
}

$updateScript = Join-Path $lubitRoot 'scripts/update_visualizations.ps1'
if (-not (Test-Path -LiteralPath $updateScript)) {
    Write-Error "시각화 스크립트를 찾을 수 없습니다: $updateScript"
    exit 1
}

if (-not $SkipVisuals) {
    Write-Host "[1/3] 시각화 갱신 중..."
    & powershell -File $updateScript -Python $Python
    if ($LASTEXITCODE -ne 0) {
        Write-Error "시각화 생성에 실패했습니다."
        exit $LASTEXITCODE
    }
}

# 목적지 경로 보정: 절대 경로면 그대로 사용, 아니면 repoRoot 기준으로 결합
try {
    $isAbsolute = [System.IO.Path]::IsPathRooted($Destination)
} catch { $isAbsolute = $false }

if ($isAbsolute) {
    $destinationPath = $Destination
} else {
    $destinationPath = Join-Path $repoRoot $Destination
}

# 존재할 경우 정규화된 실제 경로 확인(없어도 무시)
$resolved = $null
try { $resolved = Resolve-Path -LiteralPath $destinationPath -ErrorAction Stop } catch { $resolved = $null }
if ($resolved) { $destinationPath = $resolved.Path }

Write-Host "[2/3] 대상 폴더 정리: $destinationPath"
if (Test-Path -LiteralPath $destinationPath) {
    Remove-Item -LiteralPath $destinationPath -Recurse -Force
}
if ($CleanOnly) {
    New-Item -ItemType Directory -Path $destinationPath -Force | Out-Null
    Write-Host "CleanOnly 옵션이 지정되어 복사 없이 종료합니다."
    exit 0
}

New-Item -ItemType Directory -Path $destinationPath -Force | Out-Null
Write-Host "[3/3] 포트폴리오 콘텐츠 복사"
# -LiteralPath는 와일드카드를 확장하지 않으므로 -Path를 사용해 모든 항목을 복사
$copySource = Join-Path $lubitRoot '*'
Copy-Item -Path $copySource -Destination $destinationPath -Recurse -Force
Write-Host "완료: $destinationPath"
