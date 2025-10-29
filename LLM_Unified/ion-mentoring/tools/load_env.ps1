param(
    [string]$Path = "..\..\.env.example",
    [switch]$DryRun,
    [switch]$Persist
)

# 경로 해석: 스크립트 기준 상대경로 지원
$resolved = $Path
if (-not ([System.IO.Path]::IsPathRooted($Path))) {
    $resolved = Join-Path -Path $PSScriptRoot -ChildPath $Path
}

if (!(Test-Path $resolved)) {
    Write-Error "환경 파일을 찾을 수 없습니다: $resolved"
    exit 1
}

Get-Content -Path $resolved | ForEach-Object {
    $line = $_.Trim()
    if ($line -eq '' -or $line.StartsWith('#')) { return }
    $kv = $line -split '=', 2
    if ($kv.Length -ne 2) { return }
    $key = $kv[0].Trim()
    $val = $kv[1].Trim()

    if ($DryRun) {
        if ($Persist) {
            Write-Host "[DryRun] setx $key $val"
        }
        else {
            Write-Host "[DryRun] (session) $key=$val"
        }
    }
    elseif ($Persist) {
        # 사용자 환경 변수로 영구 적용 (새 세션부터 반영)
        # setx는 따옴표 없이 공백 포함 값을 처리하므로, 값에 공백이 있다면 따옴표 권장
        $quoted = $val
        if ($val -match "\s") { $quoted = '"' + $val + '"' }
        cmd /c "setx $key $quoted" | Out-Null
        Write-Host "[Persist] setx $key $val"
    }
    else {
        # 현재 프로세스에 즉시 적용 (동적 키 지원)
        Set-Item -Path "Env:$key" -Value $val
        Write-Host "[Set] $key=$val"
    }
}

if (-not $DryRun) {
    if ($Persist) {
        Write-Host "사용자 환경 변수에 영구 적용되었습니다. (새 PowerShell 세션에서 반영)"
    }
    else {
        Write-Host "환경 변수가 현재 세션에 적용되었습니다. (영구 적용은 -Persist 사용)"
    }
}
