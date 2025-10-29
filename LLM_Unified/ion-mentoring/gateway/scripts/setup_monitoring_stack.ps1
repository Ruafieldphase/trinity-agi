<#
.SYNOPSIS
    Lumen Gateway 전체 모니터링 스택 설정 스크립트
    
.DESCRIPTION
    Prometheus + Alertmanager + Gateway Exporter 통합 설정
    - Prometheus 설치 및 설정
    - Alertmanager 설치 및 설정
    - Alert Rules 복사
    - 자동 시작 설정
    
.PARAMETER InstallPath
    설치 경로 (기본값: C:\prometheus)
    
.PARAMETER SkipPrometheus
    Prometheus 설치 건너뛰기 (이미 설치된 경우)
    
.PARAMETER SkipAlertmanager
    Alertmanager 설치 건너뛰기 (이미 설치된 경우)
    
.PARAMETER StartServices
    설치 후 서비스 자동 시작
    
.EXAMPLE
    .\setup_monitoring_stack.ps1
    전체 스택 설치
    
.EXAMPLE
    .\setup_monitoring_stack.ps1 -SkipPrometheus
    Alertmanager만 설치
    
.EXAMPLE
    .\setup_monitoring_stack.ps1 -StartServices
    설치 후 자동 시작
#>

[CmdletBinding()]
param(
    [string]$InstallPath = "C:\prometheus",
    [switch]$SkipPrometheus,
    [switch]$SkipAlertmanager,
    [switch]$StartServices
)

$ErrorActionPreference = "Stop"

# 버전 정보
$PrometheusVersion = "2.48.0"
$AlertmanagerVersion = "0.27.0"

# Gateway 경로
$GatewayPath = Split-Path -Parent $PSScriptRoot
$AlertsPath = Join-Path $GatewayPath "alerts"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Lumen Gateway Monitoring Stack Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📦 Install Path: $InstallPath" -ForegroundColor Yellow
Write-Host "🔧 Prometheus Version: $PrometheusVersion" -ForegroundColor Yellow
Write-Host "🔔 Alertmanager Version: $AlertmanagerVersion" -ForegroundColor Yellow
Write-Host ""

# 설치 디렉토리 생성
if (-not (Test-Path $InstallPath)) {
    Write-Host "📂 Creating install directory..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path $InstallPath | Out-Null
    Write-Host "✅ Directory created" -ForegroundColor Green
}

# === Prometheus 설치 ===
if (-not $SkipPrometheus) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host " Installing Prometheus" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    
    $prometheusExe = Join-Path $InstallPath "prometheus\prometheus.exe"
    
    if (Test-Path $prometheusExe) {
        Write-Host "⚠️  Prometheus already installed at $prometheusExe" -ForegroundColor Yellow
        $overwrite = Read-Host "Overwrite? (y/n)"
        if ($overwrite -ne 'y') {
            Write-Host "⏭️  Skipping Prometheus installation" -ForegroundColor Yellow
            $SkipPrometheus = $true
        }
    }
    
    if (-not $SkipPrometheus) {
        try {
            # 다운로드
            $url = "https://github.com/prometheus/prometheus/releases/download/v$PrometheusVersion/prometheus-$PrometheusVersion.windows-amd64.zip"
            $zipFile = Join-Path $InstallPath "prometheus.zip"
            
            Write-Host "📥 Downloading Prometheus $PrometheusVersion..." -ForegroundColor Yellow
            Invoke-WebRequest -Uri $url -OutFile $zipFile -UseBasicParsing
            Write-Host "✅ Download complete" -ForegroundColor Green
            
            # 압축 해제
            Write-Host "📦 Extracting..." -ForegroundColor Yellow
            Expand-Archive -Path $zipFile -DestinationPath $InstallPath -Force
            
            # 파일 이동
            $extractedDir = Join-Path $InstallPath "prometheus-$PrometheusVersion.windows-amd64"
            $targetDir = Join-Path $InstallPath "prometheus"
            
            if (Test-Path $targetDir) {
                Remove-Item $targetDir -Recurse -Force
            }
            
            Move-Item $extractedDir $targetDir
            Remove-Item $zipFile -Force
            
            Write-Host "✅ Prometheus installed" -ForegroundColor Green
            
            # 설정 파일 생성
            $prometheusConfig = @"
global:
  scrape_interval: 15s
  evaluation_interval: 15s

# Alertmanager configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - localhost:9093

# Load rules once and periodically evaluate them
rule_files:
  - "rules\*.yml"

# Scrape configurations
scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'lumen-gateway'
    static_configs:
      - targets: ['localhost:9108']
        labels:
          service: 'lumen-gateway'
          environment: 'production'
"@
            
            $configPath = Join-Path $InstallPath "prometheus\prometheus.yml"
            Set-Content -Path $configPath -Value $prometheusConfig -Encoding UTF8
            Write-Host "✅ Configuration created" -ForegroundColor Green
            
            # Rules 디렉토리 생성
            $rulesDir = Join-Path $InstallPath "prometheus\rules"
            if (-not (Test-Path $rulesDir)) {
                New-Item -ItemType Directory -Force -Path $rulesDir | Out-Null
            }
            
            # Alert Rules 복사
            $rulesFile = Join-Path $AlertsPath "prometheus_rules.yml"
            if (Test-Path $rulesFile) {
                Copy-Item $rulesFile -Destination (Join-Path $rulesDir "gateway_rules.yml") -Force
                Write-Host "✅ Alert rules copied" -ForegroundColor Green
            }
            
        }
        catch {
            Write-Host "❌ Failed to install Prometheus: $_" -ForegroundColor Red
            exit 1
        }
    }
}

# === Alertmanager 설치 ===
if (-not $SkipAlertmanager) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host " Installing Alertmanager" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    
    $alertmanagerExe = Join-Path $InstallPath "alertmanager\alertmanager.exe"
    
    if (Test-Path $alertmanagerExe) {
        Write-Host "✅ Alertmanager already installed" -ForegroundColor Green
    }
    else {
        try {
            # 다운로드
            $url = "https://github.com/prometheus/alertmanager/releases/download/v$AlertmanagerVersion/alertmanager-$AlertmanagerVersion.windows-amd64.zip"
            $zipFile = Join-Path $InstallPath "alertmanager.zip"
            
            Write-Host "📥 Downloading Alertmanager $AlertmanagerVersion..." -ForegroundColor Yellow
            Invoke-WebRequest -Uri $url -OutFile $zipFile -UseBasicParsing
            Write-Host "✅ Download complete" -ForegroundColor Green
            
            # 압축 해제
            Write-Host "📦 Extracting..." -ForegroundColor Yellow
            Expand-Archive -Path $zipFile -DestinationPath $InstallPath -Force
            
            # 파일 이동
            $extractedDir = Join-Path $InstallPath "alertmanager-$AlertmanagerVersion.windows-amd64"
            $targetDir = Join-Path $InstallPath "alertmanager"
            
            if (Test-Path $targetDir) {
                Remove-Item $targetDir -Recurse -Force
            }
            
            Move-Item $extractedDir $targetDir
            Remove-Item $zipFile -Force
            
            Write-Host "✅ Alertmanager installed" -ForegroundColor Green
            
        }
        catch {
            Write-Host "❌ Failed to install Alertmanager: $_" -ForegroundColor Red
            exit 1
        }
    }
    
    # 설정 파일 복사
    $alertmanagerConfig = Join-Path $AlertsPath "alertmanager.yml"
    if (Test-Path $alertmanagerConfig) {
        Copy-Item $alertmanagerConfig -Destination (Join-Path $InstallPath "alertmanager\alertmanager.yml") -Force
        Write-Host "✅ Alertmanager configuration copied" -ForegroundColor Green
    }
}

# === 환경 변수 확인 ===
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Environment Check" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if ($env:SLACK_WEBHOOK_URL) {
    Write-Host "✅ SLACK_WEBHOOK_URL is configured" -ForegroundColor Green
}
else {
    Write-Host "⚠️  SLACK_WEBHOOK_URL not set" -ForegroundColor Yellow
    Write-Host "   Alerts will not be sent to Slack" -ForegroundColor Yellow
    Write-Host "   Set with: [Environment]::SetEnvironmentVariable('SLACK_WEBHOOK_URL', 'https://hooks.slack.com/...', 'User')" -ForegroundColor Gray
}

# === 시작 스크립트 생성 ===
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Creating Startup Scripts" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Prometheus 시작 스크립트
$prometheusStartScript = @"
# Prometheus 시작 스크립트
`$prometheusPath = "$InstallPath\prometheus"
`$logPath = "$InstallPath\logs"

if (-not (Test-Path `$logPath)) {
    New-Item -ItemType Directory -Force -Path `$logPath | Out-Null
}

Write-Host "🚀 Starting Prometheus..." -ForegroundColor Green
Start-Process -FilePath "`$prometheusPath\prometheus.exe" ``
    -ArgumentList "--config.file=`$prometheusPath\prometheus.yml", ``
                  "--storage.tsdb.path=`$prometheusPath\data", ``
                  "--web.listen-address=:9090" ``
    -WorkingDirectory `$prometheusPath ``
    -WindowStyle Hidden

Write-Host "✅ Prometheus started on http://localhost:9090" -ForegroundColor Green
"@

$startPrometheusPath = Join-Path $InstallPath "start_prometheus.ps1"
Set-Content -Path $startPrometheusPath -Value $prometheusStartScript -Encoding UTF8
Write-Host "✅ Created: $startPrometheusPath" -ForegroundColor Green

# Alertmanager 시작 스크립트
$alertmanagerStartScript = @"
# Alertmanager 시작 스크립트
`$alertmanagerPath = "$InstallPath\alertmanager"
`$logPath = "$InstallPath\logs"

if (-not (Test-Path `$logPath)) {
    New-Item -ItemType Directory -Force -Path `$logPath | Out-Null
}

Write-Host "🚀 Starting Alertmanager..." -ForegroundColor Green
Start-Process -FilePath "`$alertmanagerPath\alertmanager.exe" ``
    -ArgumentList "--config.file=`$alertmanagerPath\alertmanager.yml", ``
                  "--storage.path=`$alertmanagerPath\data", ``
                  "--web.listen-address=:9093" ``
    -WorkingDirectory `$alertmanagerPath ``
    -WindowStyle Hidden

Write-Host "✅ Alertmanager started on http://localhost:9093" -ForegroundColor Green
"@

$startAlertmanagerPath = Join-Path $InstallPath "start_alertmanager.ps1"
Set-Content -Path $startAlertmanagerPath -Value $alertmanagerStartScript -Encoding UTF8
Write-Host "✅ Created: $startAlertmanagerPath" -ForegroundColor Green

# 전체 시작 스크립트
$startAllScript = @"
# 전체 모니터링 스택 시작
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Starting Monitoring Stack" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Prometheus
& "$startPrometheusPath"
Start-Sleep -Seconds 3

# Alertmanager
& "$startAlertmanagerPath"
Start-Sleep -Seconds 2

# Gateway Exporter 확인
`$exporterRunning = Get-NetTCPConnection -LocalPort 9108 -ErrorAction SilentlyContinue
if (`$exporterRunning) {
    Write-Host "✅ Gateway Exporter is running on port 9108" -ForegroundColor Green
} else {
    Write-Host "⚠️  Gateway Exporter not running - start it manually" -ForegroundColor Yellow
    Write-Host "   cd $GatewayPath\scripts" -ForegroundColor Gray
    Write-Host "   .\start_gateway.ps1" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Monitoring Stack URLs" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Prometheus:    http://localhost:9090" -ForegroundColor Yellow
Write-Host "Alertmanager:  http://localhost:9093" -ForegroundColor Yellow
Write-Host "Gateway:       http://localhost:9108/metrics" -ForegroundColor Yellow
Write-Host ""
"@

$startAllPath = Join-Path $InstallPath "start_monitoring_stack.ps1"
Set-Content -Path $startAllPath -Value $startAllScript -Encoding UTF8
Write-Host "✅ Created: $startAllPath" -ForegroundColor Green

# === 서비스 시작 ===
if ($StartServices) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host " Starting Services" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    
    & $startAllPath
}

# === 완료 ===
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Setup Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📂 Installation Path:" -ForegroundColor Yellow
Write-Host "   $InstallPath" -ForegroundColor Gray
Write-Host ""
Write-Host "🚀 To start the monitoring stack:" -ForegroundColor Yellow
Write-Host "   & `"$startAllPath`"" -ForegroundColor Gray
Write-Host ""
Write-Host "🔗 Access URLs:" -ForegroundColor Yellow
Write-Host "   Prometheus:    http://localhost:9090" -ForegroundColor Gray
Write-Host "   Alertmanager:  http://localhost:9093" -ForegroundColor Gray
Write-Host "   Gateway:       http://localhost:9108/metrics" -ForegroundColor Gray
Write-Host ""
Write-Host "📝 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Set SLACK_WEBHOOK_URL environment variable (for alerts)" -ForegroundColor Gray
Write-Host "   2. Start Gateway Exporter if not running" -ForegroundColor Gray
Write-Host "   3. Import Grafana dashboard (optional)" -ForegroundColor Gray
Write-Host ""
