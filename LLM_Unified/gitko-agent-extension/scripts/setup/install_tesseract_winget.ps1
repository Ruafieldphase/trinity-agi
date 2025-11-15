#requires -version 5.1
[CmdletBinding()]
param(
    [switch]$Admin,
    [switch]$English
)

try { [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false) } catch {}
try { $script:OutputEncoding = [Console]::OutputEncoding } catch {}
try { chcp 65001 | Out-Null } catch {}

function Say {
    param(
        [string]$Ko,
        [string]$En,
        [ConsoleColor]$Color = [ConsoleColor]::White
    )
    $msg = if ($English) { $En } else { $Ko }
    Write-Host $msg -ForegroundColor $Color
}

function Invoke-WingetInstall([string]$Id) {
    Say "➡️ winget으로 설치 시도: $Id" "Attempt winget install: $Id" ([ConsoleColor]::Cyan)
    $wingetArgs = @('install', '-e', '--id', $Id, '--accept-package-agreements', '--accept-source-agreements')
    if ($Admin) { $wingetArgs += '--scope' ; $wingetArgs += 'machine' }
    winget @wingetArgs
    return $LASTEXITCODE
}

# Try several known IDs
$ids = @(
    'Tesseract-OCR.Tesseract',            # 공식 빌드
    'UB-Mannheim.TesseractOCR',           # Mannheim 빌드(자주 사용됨)
    'Shreeshrii.Tesseract-OCR'            # 대안 커뮤니티 빌드
)

$installed = $false
foreach ($id in $ids) {
    $code = Invoke-WingetInstall $id
    if ($code -eq 0) { $installed = $true; break }
}

if (-not $installed) {
    if ($English) {
        Write-Error 'All winget installation attempts failed. Try running install_tesseract_admin.ps1 in an elevated PowerShell.'
    }
    else {
        Write-Error 'winget 설치가 모두 실패했습니다. 관리자 PowerShell에서 install_tesseract_admin.ps1을 시도하세요.'
    }
    exit 1
}

# Locate tesseract
$tessExe = $null
try { $tessExe = (Get-Command tesseract.exe -ErrorAction SilentlyContinue).Source } catch {}
if (-not $tessExe) {
    $candidates = @(
        'C:\\Program Files\\Tesseract-OCR\\tesseract.exe',
        'C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe'
    )
    foreach ($c in $candidates) { if (Test-Path $c) { $tessExe = $c; break } }
}

if ($tessExe) {
    Say "[OK] Tesseract 설치 경로: $tessExe" "Installed path: $tessExe" ([ConsoleColor]::Green)
}
else {
    if ($English) {
        Write-Warning 'Could not locate tesseract.exe. Refresh PATH or log off/on and retry.'
    }
    else {
        Write-Warning 'Tesseract 실행 파일을 찾지 못했습니다. PATH를 새로고침하거나 로그아웃/로그인 후 다시 시도하세요.'
    }
}

# Configure for Python
$repoRoot = Split-Path -Parent $PSCommandPath
$configScript = Join-Path $repoRoot 'configure_tesseract.ps1'
if (Test-Path $configScript) {
    Say '[CONFIG] Python 환경에서 Tesseract 경로를 구성합니다...' 'Configure Tesseract path for Python backend...' ([ConsoleColor]::Cyan)
    if ($English) { & $configScript -Verbose:$false -English } else { & $configScript -Verbose:$false }
}

Say '[SUCCESS] Tesseract 설치가 완료되었습니다 (winget).' 'Tesseract installation completed (winget).' ([ConsoleColor]::Green)
