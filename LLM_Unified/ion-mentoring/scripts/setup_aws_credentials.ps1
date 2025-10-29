# ======================================================================
# setup_aws_credentials.ps1
# ----------------------------------------------------------------------
# 루빛 작업 환경에서 AWS CLI 기본 프로필 자격 증명을 손쉽게 구성하기 위한 스크립트
# 사용 예:
#   .\setup_aws_credentials.ps1
#   .\setup_aws_credentials.ps1 -Profile "lubit-canary" -Region "ap-northeast-2"
# ======================================================================

[CmdletBinding()]
param(
    [string]$Profile = $(if ($env:AWS_PROFILE) { $env:AWS_PROFILE } else { "default" }),
    [string]$AccessKey,
    [string]$SecretKey,
    [string]$SessionToken,
    [string]$Region = $(if ($env:AWS_REGION) { $env:AWS_REGION } else { "us-east-1" }),
    [ValidateSet("json", "text", "table")]
    [string]$Output = $(if ($env:AWS_DEFAULT_OUTPUT) { $env:AWS_DEFAULT_OUTPUT } else { "json" }),
    [switch]$PersistEnv,
    # 현재 PowerShell 프로세스 범위에만 환경 변수 설정 (영구 저장 아님)
    [switch]$ExportEnv,
    # 형식 검증 경고를 무시하고 진행
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-Warn {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-Err {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Test-AwsCliVersion {
    try {
        $ver = & aws --version 2>$null
        if (-not $ver) { return }
        if ($ver -notmatch 'aws-cli/2\.') { Write-Warn "AWS CLI v2 권장 (현재: $ver)" }
    }
    catch { }
}

function Validate-CredentialsFormat {
    param(
        [string]$AccessKey,
        [string]$SecretKey
    )
    $akOk = $true
    $skOk = $true
    if ($AccessKey) {
        if ($AccessKey -notmatch '^(AKIA|ASIA)[A-Z0-9]{16}$') { $akOk = $false }
    }
    if ($SecretKey) {
        if ($SecretKey -notmatch '^[A-Za-z0-9/+=]{40}$') { $skOk = $false }
    }
    if (-not $akOk -or -not $skOk) {
        if (-not $Force) {
            if (-not $akOk -and -not $skOk) { Write-Warn "AccessKey/SecretKey 형식이 예상과 다릅니다. 계속 진행합니다." }
            elseif (-not $akOk) { Write-Warn "AccessKey 형식이 예상과 다릅니다. 계속 진행합니다." }
            elseif (-not $skOk) { Write-Warn "SecretKey 형식이 예상과 다릅니다. 계속 진행합니다." }
        }
    }
}

function Read-Secret {
    param([string]$Prompt)

    $secure = Read-Host -Prompt $Prompt -AsSecureString
    if (-not $secure) {
        throw "비어 있는 값은 허용되지 않습니다."
    }

    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try {
        [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
    }
    finally {
        if ($ptr -ne [IntPtr]::Zero) {
            [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
        }
    }
}

if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    throw "AWS CLI를 찾을 수 없습니다. 먼저 AWS CLI를 설치한 뒤 다시 시도하세요."
}
Test-AwsCliVersion

Write-Info "AWS 자격 증명을 프로필 '$Profile'에 적용합니다."

if (-not $AccessKey) {
    if ($env:AWS_ACCESS_KEY_ID) {
        Write-Info "환경 변수 AWS_ACCESS_KEY_ID 값을 사용합니다."
        $AccessKey = $env:AWS_ACCESS_KEY_ID
    }
    else {
        $AccessKey = Read-Host -Prompt "AWS Access Key ID"
    }
}

if (-not $SecretKey) {
    if ($env:AWS_SECRET_ACCESS_KEY) {
        Write-Info "환경 변수 AWS_SECRET_ACCESS_KEY 값을 사용합니다."
        $SecretKey = $env:AWS_SECRET_ACCESS_KEY
    }
    else {
        $SecretKey = Read-Secret -Prompt "AWS Secret Access Key (입력 내용은 표시되지 않습니다)"
    }
}

if (-not $SessionToken -and $env:AWS_SESSION_TOKEN) {
    Write-Info "환경 변수 AWS_SESSION_TOKEN 값을 사용합니다."
    $SessionToken = $env:AWS_SESSION_TOKEN
}

# 기본 형식 검증 (엄격 차단은 아님)
Validate-CredentialsFormat -AccessKey $AccessKey -SecretKey $SecretKey

try {
    & aws configure set aws_access_key_id $AccessKey --profile $Profile | Out-Null
    & aws configure set aws_secret_access_key $SecretKey --profile $Profile | Out-Null

    if ($SessionToken) {
        & aws configure set aws_session_token $SessionToken --profile $Profile | Out-Null
    }
    else {
        # 기존에 세션 토큰이 남아 있을 경우를 대비해 제거
        & aws configure set aws_session_token "" --profile $Profile | Out-Null
    }

    & aws configure set region $Region --profile $Profile | Out-Null
    & aws configure set output $Output --profile $Profile | Out-Null
}
catch {
    throw "aws configure 명령 실행 중 오류가 발생했습니다: $($_.Exception.Message)"
}

if ($PersistEnv) {
    Write-Warn "환경 변수에 자격 증명을 저장합니다. 이 설정은 현재 사용자 프로필에 보존되며, 공유 PC에서는 지양하세요."
    [Environment]::SetEnvironmentVariable("AWS_ACCESS_KEY_ID", $AccessKey, "User")
    [Environment]::SetEnvironmentVariable("AWS_SECRET_ACCESS_KEY", $SecretKey, "User")
    if ($SessionToken) {
        [Environment]::SetEnvironmentVariable("AWS_SESSION_TOKEN", $SessionToken, "User")
    }
    else {
        [Environment]::SetEnvironmentVariable("AWS_SESSION_TOKEN", $null, "User")
    }
    [Environment]::SetEnvironmentVariable("AWS_DEFAULT_REGION", $Region, "User")
    [Environment]::SetEnvironmentVariable("AWS_DEFAULT_OUTPUT", $Output, "User")
    [Environment]::SetEnvironmentVariable("AWS_PROFILE", $Profile, "User")
}

if ($ExportEnv) {
    Write-Info "현재 세션 환경 변수에 자격 증명을 내보냅니다(프로세스 범위)."
    [Environment]::SetEnvironmentVariable("AWS_ACCESS_KEY_ID", $AccessKey, "Process")
    [Environment]::SetEnvironmentVariable("AWS_SECRET_ACCESS_KEY", $SecretKey, "Process")
    if ($SessionToken) {
        [Environment]::SetEnvironmentVariable("AWS_SESSION_TOKEN", $SessionToken, "Process")
    }
    else {
        [Environment]::SetEnvironmentVariable("AWS_SESSION_TOKEN", $null, "Process")
    }
    [Environment]::SetEnvironmentVariable("AWS_DEFAULT_REGION", $Region, "Process")
    [Environment]::SetEnvironmentVariable("AWS_DEFAULT_OUTPUT", $Output, "Process")
    [Environment]::SetEnvironmentVariable("AWS_PROFILE", $Profile, "Process")
}

$SecretKey = $null
$SessionToken = $null
$AccessKey = $null

Write-Info "자격 증명 설정이 완료되었습니다."

try {
    $identity = aws sts get-caller-identity --profile $Profile | ConvertFrom-Json
    Write-Info ("STS 검증 완료: Account {0}, ARN {1}" -f $identity.Account, $identity.Arn)
}
catch {
    Write-Warn "STS 호출 중 오류가 발생했습니다. 네트워크 또는 권한 설정을 확인하세요. 오류: $($_.Exception.Message)"
}

${_msg} = "필요 시 'aws configure list --profile {0}' 명령으로 값을 확인할 수 있습니다." -f $Profile
Write-Info ${_msg}
