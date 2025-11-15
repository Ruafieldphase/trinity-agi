# Gitko Extension - 자동 문제 해결 스크립트
# 문제 자동 진단 및 해결 제안

param(
    [switch]$Fix,  # 자동 수정 시도
    [switch]$Verbose  # 상세 출력
)

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  Gitko Extension Troubleshooter   " -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

$issues = @()
$fixes = @()

# 1. Extension 파일 확인
Write-Host "🔍 1. Extension 파일 검사..." -ForegroundColor Yellow

$requiredFiles = @(
    "package.json",
    "src/extension.ts",
    "out/extension.js"
)

foreach ($file in $requiredFiles) {
    if (!(Test-Path $file)) {
        $issues += "❌ 필수 파일 없음: $file"
        if ($file -eq "out/extension.js") {
            $fixes += "npm run compile"
        }
    } else {
        if ($Verbose) {
            Write-Host "  ✅ $file" -ForegroundColor Green
        }
    }
}

if ($issues.Count -eq 0) {
    Write-Host "  ✅ 모든 필수 파일 존재" -ForegroundColor Green
}

# 2. Node Modules 확인
Write-Host "`n📦 2. npm 패키지 검사..." -ForegroundColor Yellow

if (!(Test-Path "node_modules")) {
    $issues += "❌ node_modules 없음"
    $fixes += "npm install"
    Write-Host "  ❌ node_modules 폴더 없음" -ForegroundColor Red
} else {
    $packageJson = Get-Content "package.json" | ConvertFrom-Json
    $requiredDeps = @("axios")
    
    foreach ($dep in $requiredDeps) {
        if (!(Test-Path "node_modules/$dep")) {
            $issues += "❌ 패키지 없음: $dep"
            $fixes += "npm install"
        }
    }
    
    if ($issues -notcontains "❌ 패키지 없음*") {
        Write-Host "  ✅ 필수 패키지 설치됨" -ForegroundColor Green
    }
}

# 3. TypeScript 컴파일 상태
Write-Host "`n🔨 3. TypeScript 컴파일 검사..." -ForegroundColor Yellow

if (Test-Path "out") {
    $tsFiles = (Get-ChildItem -Path "src" -Filter "*.ts" | Measure-Object).Count
    $jsFiles = (Get-ChildItem -Path "out" -Filter "*.js" -Recurse | Measure-Object).Count
    
    if ($jsFiles -eq 0) {
        $issues += "❌ 컴파일된 파일 없음"
        $fixes += "npm run compile"
        Write-Host "  ❌ JavaScript 파일 없음 - 컴파일 필요" -ForegroundColor Red
    } elseif ($jsFiles -lt $tsFiles) {
        $issues += "⚠️ 일부 파일만 컴파일됨 ($jsFiles/$tsFiles)"
        $fixes += "npm run rebuild"
        Write-Host "  ⚠️ 불완전한 컴파일: $jsFiles/$tsFiles" -ForegroundColor Yellow
    } else {
        Write-Host "  ✅ 컴파일 완료: $jsFiles JavaScript 파일" -ForegroundColor Green
    }
} else {
    $issues += "❌ out 폴더 없음"
    $fixes += "npm run compile"
    Write-Host "  ❌ out 폴더 없음 - 컴파일 필요" -ForegroundColor Red
}

# 4. VS Code 설정 확인
Write-Host "`n⚙️  4. VS Code 설정 검사..." -ForegroundColor Yellow

if (!(Test-Path ".vscode")) {
    $issues += "⚠️ .vscode 폴더 없음"
    Write-Host "  ⚠️ .vscode 폴더 없음 - F5 실행 불가" -ForegroundColor Yellow
} else {
    if (!(Test-Path ".vscode/launch.json")) {
        $issues += "⚠️ launch.json 없음"
        Write-Host "  ⚠️ launch.json 없음" -ForegroundColor Yellow
    }
    if (!(Test-Path ".vscode/tasks.json")) {
        $issues += "⚠️ tasks.json 없음"
        Write-Host "  ⚠️ tasks.json 없음" -ForegroundColor Yellow
    }
    
    if ((Test-Path ".vscode/launch.json") -and (Test-Path ".vscode/tasks.json")) {
        Write-Host "  ✅ VS Code 설정 완료" -ForegroundColor Green
    }
}

# 5. Python 환경 확인 (선택적)
Write-Host "`n🐍 5. Python 환경 검사..." -ForegroundColor Yellow

try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Python 설치됨: $pythonVersion" -ForegroundColor Green
    } else {
        $issues += "⚠️ Python 실행 불가"
        Write-Host "  ⚠️ Python 실행 실패" -ForegroundColor Yellow
    }
} catch {
    $issues += "⚠️ Python 없음"
    Write-Host "  ⚠️ Python이 PATH에 없음 (Agent 기능 제한)" -ForegroundColor Yellow
}

# 6. 포트 사용 확인
Write-Host "`n🌐 6. 네트워크 포트 검사..." -ForegroundColor Yellow

$port = 8091
try {
    $connection = Test-NetConnection -ComputerName localhost -Port $port -InformationLevel Quiet -WarningAction SilentlyContinue
    if ($connection) {
        Write-Host "  ✅ 포트 $port 사용 가능 (HTTP Server 실행 중)" -ForegroundColor Green
    } else {
        Write-Host "  ℹ️  포트 $port 닫힘 (HTTP Poller 사용 불가)" -ForegroundColor Gray
    }
} catch {
    Write-Host "  ℹ️  포트 확인 불가" -ForegroundColor Gray
}

# 7. 메모리 사용량
Write-Host "`n💾 7. 시스템 리소스 검사..." -ForegroundColor Yellow

$vscodeProceses = Get-Process -Name "Code" -ErrorAction SilentlyContinue
if ($vscodeProceses) {
    $totalMemory = ($vscodeProceses | Measure-Object -Property WorkingSet64 -Sum).Sum / 1MB
    Write-Host "  📊 VS Code 메모리 사용: $([math]::Round($totalMemory, 2)) MB" -ForegroundColor White
    
    if ($totalMemory -gt 1000) {
        $issues += "⚠️ VS Code 메모리 사용량 높음"
        Write-Host "  ⚠️ 메모리 사용량이 높습니다 (재시작 권장)" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ℹ️  VS Code 실행 중 아님" -ForegroundColor Gray
}

# 최종 결과
Write-Host "`n=====================================" -ForegroundColor Cyan
Write-Host "  진단 결과                        " -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

if ($issues.Count -eq 0) {
    Write-Host "`n✅ 문제 없음! Extension 사용 가능" -ForegroundColor Green
    Write-Host "`n다음 단계:" -ForegroundColor Cyan
    Write-Host "  F5 키를 눌러 Extension Development Host 실행" -ForegroundColor White
    exit 0
}

# 문제 목록 출력
Write-Host "`n발견된 문제:" -ForegroundColor Yellow
foreach ($issue in $issues) {
    Write-Host "  $issue" -ForegroundColor $(if ($issue.StartsWith("❌")) { "Red" } else { "Yellow" })
}

# 해결 방법 제안
if ($fixes.Count -gt 0) {
    Write-Host "`n권장 해결 방법:" -ForegroundColor Cyan
    
    $uniqueFixes = $fixes | Select-Object -Unique
    $fixNum = 1
    foreach ($fix in $uniqueFixes) {
        Write-Host "  $fixNum. $fix" -ForegroundColor White
        $fixNum++
    }
    
    # 자동 수정
    if ($Fix) {
        Write-Host "`n🔧 자동 수정 시도 중..." -ForegroundColor Yellow
        
        foreach ($fix in $uniqueFixes) {
            Write-Host "`n실행: $fix" -ForegroundColor Cyan
            try {
                Invoke-Expression $fix
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "✅ 성공: $fix" -ForegroundColor Green
                } else {
                    Write-Host "❌ 실패: $fix" -ForegroundColor Red
                }
            } catch {
                Write-Host "❌ 에러: $_" -ForegroundColor Red
            }
        }
        
        Write-Host "`n🔄 재검사를 위해 스크립트를 다시 실행하세요" -ForegroundColor Cyan
    } else {
        Write-Host "`n자동 수정을 원하면: " -NoNewline -ForegroundColor Cyan
        Write-Host ".\troubleshoot.ps1 -Fix" -ForegroundColor Yellow
    }
}

# 추가 리소스
Write-Host "`n📚 추가 리소스:" -ForegroundColor Cyan
Write-Host "  - QUICKSTART.md: 빠른 시작 가이드" -ForegroundColor White
Write-Host "  - CHEATSHEET.md: 명령어 참조" -ForegroundColor White
Write-Host "  - README.md: 전체 문서" -ForegroundColor White

Write-Host "`n=====================================" -ForegroundColor Cyan

exit 1
