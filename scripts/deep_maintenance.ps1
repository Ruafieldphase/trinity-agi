#Requires -Version 5.1
<#
.SYNOPSIS
    Deep Maintenance stub (Fear ≥ 0.9 경고 시 수동/자동 실행)

.DESCRIPTION
    - 인덱스 리빌드, 캐시 초기화 등 고강도 안정화 절차의 자리를 차지하는 스텁
    - 현재는 기본 로그와 파일 점검만 수행
    - 향후 실제 유지보수 스크립트를 이 자리에 연결

.EXAMPLE
    .\scripts\deep_maintenance.ps1 -DryRun
    .\scripts\deep_maintenance.ps1 -Force
#>

[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$Force,
    [switch]$RebuildRagIndex,
    [int]$LogMaxMB = 2,
    [int]$LogKeep = 5
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$LogPath = "outputs/deep_maintenance.log"
$SummaryPath = "outputs/deep_maintenance_summary.md"
$BackupRoot = "outputs/deep_maintenance"
$WORKSPACE_ROOT = (Resolve-Path ".").Path

function Out-FileUtf8NoBomAppend {
    param(
        [Parameter(Mandatory=$true)][string]$Path,
        [Parameter(Mandatory=$true)][string]$Text
    )
    $dir = Split-Path -Parent $Path
    if ($dir -and -not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
    $enc = New-Object System.Text.UTF8Encoding($false)
    $sw = New-Object System.IO.StreamWriter($Path, $true, $enc)
    try { $sw.WriteLine($Text) } finally { $sw.Dispose() }
}

function Rotate-LogIfNeeded {
    param(
        [string]$Path,
        [int]$MaxMB = 2,
        [int]$Keep = 5
    )
    if (-not (Test-Path -LiteralPath $Path)) { return }
    try {
        $limit = [int64]$MaxMB * 1MB
        $info = Get-Item -LiteralPath $Path -ErrorAction Stop
        if ($info.Length -le $limit) { return }

        $dir = Split-Path -Parent $Path
        $base = Split-Path -Leaf $Path
        for ($i = $Keep; $i -ge 2; $i--) {
            $src = Join-Path $dir ("{0}.{1}" -f $base, $i - 1)
            $dst = Join-Path $dir ("{0}.{1}" -f $base, $i)
            if (Test-Path -LiteralPath $src) {
                Rename-Item -LiteralPath $src -NewName (Split-Path -Leaf $dst) -Force -ErrorAction SilentlyContinue
            }
        }
        Rename-Item -LiteralPath $Path -NewName ("{0}.1" -f $base) -Force -ErrorAction SilentlyContinue
    }
    catch {
        Write-Host "[WARN] Log rotation skipped: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logLine = "[$timestamp] [$Level] $Message"
    Out-FileUtf8NoBomAppend -Path $LogPath -Text $logLine

    switch ($Level) {
        "ERROR" { Write-Host $logLine -ForegroundColor Red }
        "WARNING" { Write-Host $logLine -ForegroundColor Yellow }
        "SUCCESS" { Write-Host $logLine -ForegroundColor Green }
        default { Write-Host $logLine -ForegroundColor Cyan }
    }
}

function Write-SummaryLine {
    param([string]$Text)
    $enc = New-Object System.Text.UTF8Encoding($false)
    $dir = Split-Path -Parent $SummaryPath
    if ($dir -and -not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
    $sw = New-Object System.IO.StreamWriter($SummaryPath, $true, $enc)
    try { $sw.WriteLine($Text) } finally { $sw.Dispose() }
}

function Get-PythonPath {
    $venv = Join-Path $WORKSPACE_ROOT ".venv\Scripts\python.exe"
    if (Test-Path $venv) { return $venv }
    return "python"
}

function Backup-Artifacts {
    param([string]$TargetDir)
    $paths = @(
        "fdo_agi_repo/memory/resonance_ledger.jsonl",
        "fdo_agi_repo/memory/vector_store.json",
        "outputs/performance_metrics_latest.json",
        "outputs/monitoring_report_latest.md",
        "outputs/policy_ab_snapshot_latest.md"
    )
    $copied = 0
    foreach ($rel in $paths) {
        $abs = Join-Path $WORKSPACE_ROOT $rel
        if (Test-Path -LiteralPath $abs) {
            $dest = Join-Path $TargetDir $rel
            $destDir = Split-Path -Parent $dest
            if (-not (Test-Path -LiteralPath $destDir)) {
                New-Item -ItemType Directory -Path $destDir -Force | Out-Null
            }
            Copy-Item -LiteralPath $abs -Destination $dest -Force
            $copied++
            Write-Log "백업 완료: $rel" "INFO"
        }
        else {
            Write-Log "백업 대상 누락: $rel" "WARNING"
        }
    }
    return $copied
}

function Invoke-RagRebuild {
    param([string]$WorkingDir)
    if ($DryRun) {
        Write-Log "[DRY-RUN] RAG 인덱스 재구축 스킵" "INFO"
        return
    }
    try {
        $py = Get-PythonPath
        $cmd = @($py, "-m", "tools.rag.index_docs", "--force")
        Write-Log "RAG 인덱스 재구축 실행: $($cmd -join ' ')" "INFO"
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = $cmd[0]
        $psi.Arguments = ($cmd[1..($cmd.Length-1)] -join " ")
        $psi.WorkingDirectory = $WORKSPACE_ROOT
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $psi.UseShellExecute = $false
        $proc = [System.Diagnostics.Process]::Start($psi)
        $stdout = $proc.StandardOutput.ReadToEnd()
        $stderr = $proc.StandardError.ReadToEnd()
        $proc.WaitForExit()
        if ($stdout) { Write-Log $stdout.Trim() "INFO" }
        if ($stderr) { Write-Log $stderr.Trim() "WARNING" }
        if ($proc.ExitCode -ne 0) {
            Write-Log "RAG 인덱스 재구축 실패 (exit=$($proc.ExitCode))" "ERROR"
        }
        else {
            Write-Log "RAG 인덱스 재구축 완료" "SUCCESS"
        }
    }
    catch {
        Write-Log "RAG 인덱스 재구축 중 예외: $_" "ERROR"
    }
}

function Invoke-DeepMaintenance {
    Rotate-LogIfNeeded -Path $LogPath -MaxMB $LogMaxMB -Keep $LogKeep
    Write-Log "=== Deep Maintenance Stub 시작 ===" "INFO"
    Write-Log "DryRun: $DryRun" "INFO"

    if (!$Force -and !$DryRun) {
        $confirm = Read-Host "고강도 유지보수를 실행할까요? (y/N)"
        if ($confirm -ne "y") {
            Write-Log "사용자가 취소함" "WARNING"
            return 0
        }
    }

    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $sessionDir = Join-Path $BackupRoot $timestamp
    if (-not (Test-Path -LiteralPath $sessionDir)) {
        New-Item -ItemType Directory -Force -Path $sessionDir | Out-Null
    }

    Write-Log "시스템 스냅샷 디렉터리: $sessionDir" "INFO"
    $copied = Backup-Artifacts -TargetDir $sessionDir
    Write-Log "백업 파일 수: $copied" "INFO"

    if ($RebuildRagIndex) {
        Invoke-RagRebuild -WorkingDir $WORKSPACE_ROOT
    }
    else {
        Write-Log "RAG 인덱스 재구축 스킵 (RebuildRagIndex 미설정)" "INFO"
    }

    if (-not $DryRun) {
        Write-Log "캐시/임시 파일 정리" "INFO"
        $tempTargets = @(
            "outputs/cache",
            "outputs/tmp",
            "fdo_agi_repo/.pytest_cache"
        )
        foreach ($t in $tempTargets) {
            $abs = Join-Path $WORKSPACE_ROOT $t
            if (Test-Path -LiteralPath $abs) {
                try {
                    Remove-Item -LiteralPath $abs -Recurse -Force -ErrorAction Stop
                    Write-Log "정리 완료: $t" "INFO"
                }
                catch {
                    Write-Log "정리 실패: $t - $_" "WARNING"
                }
            }
        }
    }
    else {
        Write-Log "[DRY-RUN] 캐시 정리 스킵" "INFO"
    }

    $summaryLine = "* $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - Deep maintenance executed (DryRun=$DryRun, RebuildRagIndex=$RebuildRagIndex, BackupDir=$sessionDir, Copied=$copied)"
    Write-SummaryLine -Text $summaryLine
    Write-Log "정리 완료" "SUCCESS"
    return 0
}

try {
    exit (Invoke-DeepMaintenance)
}
catch {
    Write-Log "예외 발생: $_" "ERROR"
    exit 1
}
