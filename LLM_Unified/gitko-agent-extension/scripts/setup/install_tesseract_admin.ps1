#requires -version 5.1
[CmdletBinding(SupportsShouldProcess = $true)]
param(
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

function Test-IsAdmin {
    try {
        $current = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
        return $current.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    }
    catch { return $false }
}

# Relaunch as admin if needed
if (-not (Test-IsAdmin)) {
    Say 'ℹ️ 관리자 권한이 필요합니다. 관리자 권한으로 다시 실행합니다...' 'Administrator privileges required. Relaunching elevated...' ([ConsoleColor]::Yellow)
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = 'powershell.exe'
    $psi.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    $psi.Verb = 'runas'
    try {
        [System.Diagnostics.Process]::Start($psi) | Out-Null
    }
    catch {
        if ($English) { Write-Error 'Admin elevation was denied.' } else { Write-Error '관리자 권한 승인이 거부되었습니다.' }
    }
    exit
}

# Ensure TLS 1.2
try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch {}

# Install Chocolatey if missing
if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
    Say '🍫 Chocolatey가 설치되어 있지 않습니다. 설치를 진행합니다...' 'Chocolatey is not installed. Installing...' ([ConsoleColor]::Yellow)
    Set-ExecutionPolicy Bypass -Scope Process -Force
    $script = (New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1')
    Invoke-Expression $script
}

# Attempt to clean problematic lock folders
$chocoLib = 'C:\\ProgramData\\chocolatey\\lib'
$chocoLibBad = 'C:\\ProgramData\\chocolatey\\lib-bad'
if (Test-Path $chocoLibBad) {
    Say '🧹 lib-bad 폴더를 정리합니다...' 'Cleaning up lib-bad folder...' ([ConsoleColor]::Yellow)
    try { Remove-Item -Path $chocoLibBad -Recurse -Force -ErrorAction Stop } catch { Write-Warning $_ }
}
$partial = Join-Path $chocoLib 'tesseract*'
Get-Item $partial -ErrorAction SilentlyContinue | ForEach-Object {
    Say "🧹 부분 설치 흔적 제거: $($_.FullName)" "Removing partial install: $($_.FullName)" ([ConsoleColor]::Yellow)
    try { Remove-Item -Path $_.FullName -Recurse -Force -ErrorAction Stop } catch { Write-Warning $_ }
}

# Upgrade choco and install tesseract
choco upgrade chocolatey -y | Out-Null

Say '⬇️ Tesseract 설치를 시작합니다 (Chocolatey)...' 'Installing Tesseract (Chocolatey)...' ([ConsoleColor]::Cyan)
choco install tesseract -y --force
if ($LASTEXITCODE -ne 0) {
    if ($English) { Write-Warning 'Chocolatey installation failed. Try winget: install_tesseract_winget.ps1' } else { Write-Warning 'Chocolatey 설치가 실패했습니다. winget 방법을 시도해보세요: install_tesseract_winget.ps1' }
    exit 1
}

# Try to locate tesseract
$tessExe = $null
try { $tessExe = (Get-Command tesseract.exe -ErrorAction SilentlyContinue).Source } catch {}
if (-not $tessExe) {
    $candidates = @(
        'C:\\Program Files\\Tesseract-OCR\\tesseract.exe',
        'C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe',
        'C:\\ProgramData\\chocolatey\\bin\\tesseract.exe'
    )
    foreach ($c in $candidates) { if (Test-Path $c) { $tessExe = $c; break } }
}

if ($tessExe) {
    Say "[OK] Tesseract 설치 경로: $tessExe" "Installed path: $tessExe" ([ConsoleColor]::Green)
}
else {
    if ($English) { Write-Warning 'Could not locate tesseract.exe. Refresh PATH or log off/on and retry.' } else { Write-Warning 'Tesseract 실행 파일을 찾지 못했습니다. PATH를 새로고침하거나 로그아웃/로그인 후 다시 시도하세요.' }
}

# Configure Python side
$repoRoot = Split-Path -Parent $PSCommandPath
$configScript = Join-Path $repoRoot 'configure_tesseract.ps1'
if (Test-Path $configScript) {
    Say '[CONFIG] Python 환경에서 Tesseract 경로를 구성합니다...' 'Configure Tesseract path for Python backend...' ([ConsoleColor]::Cyan)
    if ($English) { & $configScript -Verbose:$false -English } else { & $configScript -Verbose:$false }
}

Say '[SUCCESS] Tesseract 설치가 완료되었습니다.' 'Tesseract installation completed.' ([ConsoleColor]::Green)
