#Requires -Version 5.1
<#
.SYNOPSIS
    Setup Lubit (OpenAI) and Sian (Gemini) CLI bridges for Copilot error recovery.

.DESCRIPTION
    Installs dependencies and configures API keys for fallback AI agents.

.PARAMETER LubitOnly
    Only set up Lubit (OpenAI Codex) bridge.

.PARAMETER SianOnly
    Only set up Sian (Gemini) bridge.

.PARAMETER SkipInstall
    Skip package installation (only configure keys).

.EXAMPLE
    .\create_fallback_bridges.ps1
    
.EXAMPLE
    .\create_fallback_bridges.ps1 -LubitOnly
#>

Write-Host "   Installing openai..." -ForegroundColor Gray
& $VenvPython -m pip install --quiet --upgrade openai
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install openai" -ForegroundColor Red
    exit 1
}
[CmdletBinding()]
param(
    [switch]$LubitOnly,
    Write-Host "   Installing google-generativeai (Gemini) ..." -ForegroundColor Gray
    & $VenvPython -m pip install --quiet --upgrade google-generativeai
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install google-generativeai" -ForegroundColor Red
        exit 1
    }
    $VenvPython = Join-Path $WorkspaceRoot "fdo_agi_repo\.venv\Scripts\python.exe"

    # Check Python
    if (!(Test-Path $VenvPython)) {
        Write-Host "❌ fdo_agi_repo venv not found. Run setup first." -ForegroundColor Red
        exit 1
    }

    Write-Host "🚀 Setting up fallback AI bridges" -ForegroundColor Cyan
    Write-Host ""

    # Install packages
    if (!$SkipInstall) {
        Write-Host "📦 Installing dependencies..." -ForegroundColor Cyan
    
        if (!$SianOnly) {
            Write-Host "   Installing openai..." -ForegroundColor Gray
            & $VenvPython -m pip install --quiet --upgrade openai
            if ($LASTEXITCODE -ne 0) {
                Write-Host "❌ Failed to install openai" -ForegroundColor Red
                exit 1
            }
        }
    
        if (!$LubitOnly) {
            Write-Host "   Installing google-generativeai..." -ForegroundColor Gray
            & $VenvPython -m pip install --quiet --upgrade google-generativeai
            if ($LASTEXITCODE -ne 0) {
                Write-Host "❌ Failed to install google-generativeai" -ForegroundColor Red
                exit 1
            }
        }
    
        Write-Host "✅ Dependencies installed" -ForegroundColor Green
        Write-Host ""
    }

    # Configure API keys
    Write-Host "🔑 Configuring API keys" -ForegroundColor Cyan
    Write-Host ""

    if (!$SianOnly) {
        $openaiKey = [System.Environment]::GetEnvironmentVariable("OPENAI_API_KEY", "User")
    
        if ([string]::IsNullOrEmpty($openaiKey)) {
            Write-Host "   OpenAI API Key not set in user environment" -ForegroundColor Yellow
            $response = Read-Host "   Do you want to set it now? (y/n)"
        
            if ($response -eq 'y') {
                $apiKey = Read-Host "   Enter OpenAI API Key" -AsSecureString
                $plainKey = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
                    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($apiKey)
                )
            
                [System.Environment]::SetEnvironmentVariable("OPENAI_API_KEY", $plainKey, "User")
                Write-Host "   ✅ OPENAI_API_KEY set (restart VS Code to apply)" -ForegroundColor Green
            }
            else {
                Write-Host "   ⚠️  Lubit will require OPENAI_API_KEY at runtime" -ForegroundColor Yellow
            }
        }
        else {
            Write-Host "   ✅ OPENAI_API_KEY already set" -ForegroundColor Green
        }
    }

    if (!$LubitOnly) {
        $geminiKey = [System.Environment]::GetEnvironmentVariable("GEMINI_API_KEY", "User")
    
        if ([string]::IsNullOrEmpty($geminiKey)) {
            Write-Host "   Gemini API Key not set in user environment" -ForegroundColor Yellow
            $response = Read-Host "   Do you want to set it now? (y/n)"
        
            if ($response -eq 'y') {
                $apiKey = Read-Host "   Enter Gemini API Key" -AsSecureString
                $plainKey = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
                    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($apiKey)
                )
            
                [System.Environment]::SetEnvironmentVariable("GEMINI_API_KEY", $plainKey, "User")
                Write-Host "   ✅ GEMINI_API_KEY set (restart VS Code to apply)" -ForegroundColor Green
            }
            else {
                Write-Host "   ⚠️  Sian will require GEMINI_API_KEY at runtime" -ForegroundColor Yellow
            }
        }
        else {
            Write-Host "   ✅ GEMINI_API_KEY already set" -ForegroundColor Green
        }
    }

    Write-Host ""
    Write-Host "🧪 Testing bridges..." -ForegroundColor Cyan

    if (!$SianOnly) {
        Write-Host "   Testing Lubit (OpenAI)..." -ForegroundColor Gray
        $lubitBridge = Join-Path $WorkspaceRoot "fdo_agi_repo\integrations\openai_codex_bridge.py"
    
        $testResult = & $VenvPython $lubitBridge --mode test 2>&1
        if ($LASTEXITCODE -eq 0) {
            <#!
            create_fallback_bridges.ps1
            Purpose: Ensure local fallback bridges (Lubit / Sian) are provisioned for Copilot request rerouting.
            This script normalizes directory layout, seeds a .env with required secrets, and outputs a machine-readable status JSON.
            Upgrades vs previous version:
             - Clean parameter block ordering
             - Robust .env creation + reload
             - Structured logging with level filtering
             - Optional selective enable (LubitOnly / SianOnly)
             - Returns status JSON (writes outputs/fallback_bridges_status.json)
             - Idempotent: safe to re-run
            !>

            param(
                [switch]$LubitOnly,
                [switch]$SianOnly,
                [switch]$SkipInstall,
                [switch]$ForceNonInteractive,
                [switch]$Silent
            )

            $global:PathSep = [System.IO.Path]::DirectorySeparatorChar
            $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
            $WorkspaceRoot = Split-Path -Parent $ScriptDir
            if ($env:WORKSPACE_ROOT) { $WorkspaceRoot = $env:WORKSPACE_ROOT }
            $EnvFile = Join-Path $WorkspaceRoot '.env'
            $BridgeRoot = Join-Path $WorkspaceRoot 'bridges'
            $OutputsDir = Join-Path $WorkspaceRoot 'outputs'

            if (-not (Test-Path -LiteralPath $OutputsDir)) { New-Item -ItemType Directory -Path $OutputsDir | Out-Null }
            if (-not (Test-Path -LiteralPath $BridgeRoot))  { New-Item -ItemType Directory -Path $BridgeRoot  | Out-Null }

            function Write-Log {
                param([string]$Message,[string]$Level='INFO',[switch]$Force)
                if ($Silent -and -not $Force) { return }
                $ts = (Get-Date).ToString('HH:mm:ss')
                Write-Host "[$ts][$Level] $Message"
            }

            Write-Log "Fallback bridge creation starting" 'DEBUG'

            function Ensure-EnvFile {
                if (Test-Path -LiteralPath $EnvFile) { Write-Log ".env exists" 'DEBUG'; return }
                Write-Log "Creating .env with placeholder secrets" 'INFO'
                @"
            # --- Fallback Bridge Secrets (PLACEHOLDERS) ---
            OPENAI_API_KEY=__REPLACE__
            GEMINI_API_KEY=__REPLACE__
            LUBIT_HMAC_SECRET=__REPLACE__
            SIAN_HMAC_SECRET=__REPLACE__
            # Optional routing preferences
            FALLBACK_PREF=LUBIT_FIRST
            "@ | Set-Content -Path $EnvFile -Encoding UTF8
            }
            Ensure-EnvFile

            function Load-Env {
                if (-not (Test-Path -LiteralPath $EnvFile)) { return }
                Get-Content -Path $EnvFile | Where-Object { $_ -match '=' -and $_ -notmatch '^#' } | ForEach-Object {
                    $k,$rest = $_.Split('=',2); if ($k -and $rest) { $env:$k = $rest }
                }
            }
            Load-Env

            function Resolve-Python {
                $candidates = @(
                    "$WorkspaceRoot\fdo_agi_repo\.venv\Scripts\python.exe",
                    "$WorkspaceRoot\LLM_Unified\.venv\Scripts\python.exe",
                    'python'
                )
                foreach ($py in $candidates) { if (Test-Path -LiteralPath $py) { return $py } }
                return 'python'
            }
            $PythonExec = Resolve-Python
            Write-Log "Python executable: $PythonExec" 'DEBUG'

            function Ensure-BridgeLayout {
                param([string]$Name)
                $Dir = Join-Path $BridgeRoot $Name
                if (-not (Test-Path -LiteralPath $Dir)) { New-Item -ItemType Directory -Path $Dir | Out-Null }
                foreach ($sub in 'lua_requests','processed','errors') {
                    $p = Join-Path $Dir $sub; if (-not (Test-Path -LiteralPath $p)) { New-Item -ItemType Directory -Path $p | Out-Null }
                }
                $readme = Join-Path $Dir 'README.md'
                if (-not (Test-Path -LiteralPath $readme)) {
                    @"
            # $Name Bridge
            Purpose: Acts as a fallback execution surface for Copilot requests when primary provider fails.
            Folders:
            - lua_requests: inbound serialized request bodies
            - processed: successful structured responses
            - errors: failure artifacts & diagnostics
            This directory auto-generated by create_fallback_bridges.ps1.
            "@ | Set-Content -Path $readme -Encoding UTF8
                }
                return $Dir
            }

            $LubitDir = Ensure-BridgeLayout -Name 'lubit'
            $SianDir  = Ensure-BridgeLayout -Name 'sian'

            if (-not $SkipInstall) {
                Write-Log "Verifying Python packages (requests, jsonschema)" 'INFO'
                foreach ($pkg in 'requests','jsonschema') {
                    & $PythonExec -c "import $pkg" 2>$null; if ($LASTEXITCODE -ne 0) { Write-Log "Installing missing package: $pkg" 'INFO'; & $PythonExec -m pip install $pkg 2>$null }
                }
            }

            $Status = [ordered]@{
                workspace_root = $WorkspaceRoot
                bridges_root   = $BridgeRoot
                env_file       = $EnvFile
                python_exec    = $PythonExec
                lubit_dir      = $LubitDir
                sian_dir       = $SianDir
                lubit_enabled  = $true
                sian_enabled   = $true
                fallback_pref  = ($env:FALLBACK_PREF | ForEach-Object { $_ })
                timestamp      = (Get-Date).ToString('o')
            }
            if ($LubitOnly) { $Status.sian_enabled = $false }
            if ($SianOnly)  { $Status.lubit_enabled = $false }

            $Json = $Status | ConvertTo-Json -Depth 6
            $OutPath = Join-Path $OutputsDir 'fallback_bridges_status.json'
            Set-Content -Path $OutPath -Value $Json -Encoding UTF8
            Write-Log "Status written to $OutPath" 'INFO'
            if (-not $Silent) { Write-Output $Json }

            Write-Log "Fallback bridge creation complete" 'INFO' -Force
