<#
.SYNOPSIS
    Slack Bot 테스트 스크립트

.DESCRIPTION
    Slack Bot의 주요 기능을 테스트합니다.

.PARAMETER TestType
    테스트 타입: all, client, commands, notifications

.EXAMPLE
    .\test_slack_bot.ps1
    .\test_slack_bot.ps1 -TestType client
#>

[CmdletBinding()]
param(
    [ValidateSet("all", "client", "commands", "notifications")]
    [string]$TestType = "all"
)

$ErrorActionPreference = "Stop"

# 스크립트 위치
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir
$SlackBotDir = Join-Path $RootDir "slack_bot"
$VenvDir = Join-Path (Split-Path -Parent $RootDir) ".venv"
$PythonExe = Join-Path $VenvDir "Scripts\python.exe"

Write-Host "🧪 ION API Slack Bot 테스트" -ForegroundColor Cyan
Write-Host ""

# 환경 변수 로드
$EnvFile = Join-Path $RootDir ".env.slack"
if (Test-Path $EnvFile) {
    Get-Content $EnvFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith("#")) {
            if ($line -match "^(.+?)=(.+)$") {
                $key = $matches[1].Trim()
                $value = $matches[2].Trim()
                [Environment]::SetEnvironmentVariable($key, $value, "Process")
            }
        }
    }
}
else {
    Write-Host "⚠️  환경 변수 파일이 없습니다. 일부 테스트가 실패할 수 있습니다." -ForegroundColor Yellow
    Write-Host ""
}

# Python 테스트 스크립트 생성
$TestScript = @"
import sys
import os

# 경로 추가
sys.path.insert(0, r'$SlackBotDir')
sys.path.insert(0, r'$RootDir')

from slack_bot.slack_client import SlackClient
from slack_bot.slack_commands import CommandHandler
from slack_bot.slack_notifications import NotificationHandler, create_test_alert

def test_client():
    """Slack Client 테스트"""
    print("🔍 Slack Client 테스트...")
    
    try:
        client = SlackClient()
        print("✅ SlackClient 초기화 성공")
        
        # 토큰 검증
        if client.token and client.token.startswith("xoxb-"):
            print(f"✅ Bot Token: {client.token[:15]}...")
        else:
            print("⚠️  Bot Token이 올바르지 않습니다")
        
        return True
    except Exception as e:
        print(f"❌ SlackClient 오류: {e}")
        return False

def test_commands():
    """명령어 핸들러 테스트"""
    print("🔍 명령어 핸들러 테스트...")
    
    try:
        client = SlackClient()
        handler = CommandHandler(client)
        print("✅ CommandHandler 초기화 성공")
        
        # 명령어 파싱 테스트
        cmd, args = handler.parse_command("deploy canary 50%")
        assert cmd == "deploy", f"Expected 'deploy', got '{cmd}'"
        assert args == ["canary", "50%"], f"Expected ['canary', '50%'], got {args}"
        print("✅ 명령어 파싱 테스트 통과")
        
        # help 명령어 테스트
        response = handler.handle_help([], "C12345", "U12345")
        assert "text" in response, "Response should have 'text' key"
        print("✅ Help 명령어 테스트 통과")
        
        return True
    except Exception as e:
        print(f"❌ 명령어 핸들러 오류: {e}")
        return False

def test_notifications():
    """알림 핸들러 테스트"""
    print("🔍 알림 핸들러 테스트...")
    
    try:
        client = SlackClient()
        handler = NotificationHandler(client)
        print("✅ NotificationHandler 초기화 성공")
        
        # 테스트 알림 생성
        alert = create_test_alert(
            alert_name="TestAlert",
            severity="warning",
            summary="Test alert for Slack Bot",
            description="This is a test"
        )
        print("✅ 테스트 알림 생성 성공")
        
        # 알림 데이터 검증
        assert alert["status"] == "firing", "Alert status should be 'firing'"
        assert alert["labels"]["alertname"] == "TestAlert", "Alert name mismatch"
        print("✅ 알림 데이터 검증 통과")
        
        return True
    except Exception as e:
        print(f"❌ 알림 핸들러 오류: {e}")
        return False

# 테스트 실행
test_type = "$TestType"

results = {}

if test_type in ["all", "client"]:
    results["client"] = test_client()
    print()

if test_type in ["all", "commands"]:
    results["commands"] = test_commands()
    print()

if test_type in ["all", "notifications"]:
    results["notifications"] = test_notifications()
    print()

# 결과 요약
print("=" * 50)
print("📊 테스트 결과 요약")
print("=" * 50)

total = len(results)
passed = sum(1 for v in results.values() if v)
failed = total - passed

for test_name, result in results.items():
    status = "✅ 통과" if result else "❌ 실패"
    print(f"{test_name.ljust(20)}: {status}")

print("=" * 50)
print(f"전체: {total}개 / 통과: {passed}개 / 실패: {failed}개")

if failed > 0:
    sys.exit(1)
else:
    print("✅ 모든 테스트 통과!")
    sys.exit(0)
"@

# 임시 Python 스크립트 저장
$TempScript = Join-Path $env:TEMP "test_slack_bot.py"
$TestScript | Out-File -FilePath $TempScript -Encoding UTF8 -Force

# Python 테스트 실행
Write-Host "🔍 테스트 실행 중..." -ForegroundColor Cyan
Write-Host ""

& $PythonExe $TempScript

$ExitCode = $LASTEXITCODE

# 임시 파일 삭제
Remove-Item $TempScript -Force -ErrorAction SilentlyContinue

exit $ExitCode
