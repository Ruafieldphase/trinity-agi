# Gitko Extension - 자동 테스트 스크립트
# F5 실행 전 빠른 검증용

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  Gitko Extension - Quick Test      " -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

$ErrorCount = 0
$WarningCount = 0

# 1. 디렉토리 확인
Write-Host "📁 1. 디렉토리 구조 확인..." -ForegroundColor Yellow
if (!(Test-Path "src")) {
    Write-Host "  ❌ src/ 폴더 없음" -ForegroundColor Red
    $ErrorCount++
} else {
    $tsFiles = (Get-ChildItem -Path "src" -Filter "*.ts" | Measure-Object).Count
    Write-Host "  ✅ src/ 폴더 존재 ($tsFiles TypeScript 파일)" -ForegroundColor Green
}

if (!(Test-Path "package.json")) {
    Write-Host "  ❌ package.json 없음" -ForegroundColor Red
    $ErrorCount++
} else {
    Write-Host "  ✅ package.json 존재" -ForegroundColor Green
}

# 2. 패키지 확인
Write-Host "`n📦 2. npm 패키지 확인..." -ForegroundColor Yellow
if (!(Test-Path "node_modules")) {
    Write-Host "  ⚠️  node_modules 없음 - npm install 필요" -ForegroundColor Yellow
    $WarningCount++
} else {
    Write-Host "  ✅ node_modules 존재" -ForegroundColor Green
}

# 3. 컴파일 확인
Write-Host "`n🔨 3. 컴파일 상태 확인..." -ForegroundColor Yellow
if (!(Test-Path "out")) {
    Write-Host "  ⚠️  out/ 폴더 없음 - 컴파일 필요" -ForegroundColor Yellow
    $WarningCount++
} else {
    $jsFiles = (Get-ChildItem -Path "out" -Filter "*.js" -Recurse | Measure-Object).Count
    if ($jsFiles -eq 0) {
        Write-Host "  ❌ 컴파일된 파일 없음" -ForegroundColor Red
        $ErrorCount++
    } else {
        Write-Host "  ✅ 컴파일 완료 ($jsFiles JavaScript 파일)" -ForegroundColor Green
    }
}

# 4. TypeScript 에러 확인
Write-Host "`n🔍 4. TypeScript 컴파일 테스트..." -ForegroundColor Yellow
try {
    $compileOutput = npm run compile 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ TypeScript 컴파일 성공" -ForegroundColor Green
    } else {
        Write-Host "  ❌ TypeScript 컴파일 실패" -ForegroundColor Red
        $ErrorCount++
    }
} catch {
    Write-Host "  ❌ 컴파일 실행 실패: $_" -ForegroundColor Red
    $ErrorCount++
}

# 5. 핵심 파일 확인
Write-Host "`n📝 5. 핵심 파일 존재 확인..." -ForegroundColor Yellow
$requiredFiles = @(
    "src/extension.ts",
    "src/logger.ts",
    "src/performanceMonitor.ts",
    "src/activityTracker.ts",
    "src/devUtils.ts"
)

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "  ✅ $file" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $file 없음" -ForegroundColor Red
        $ErrorCount++
    }
}

# 6. package.json 검증
Write-Host "`n📋 6. package.json 검증..." -ForegroundColor Yellow
try {
    $package = Get-Content "package.json" | ConvertFrom-Json
    
    Write-Host "  📌 이름: $($package.name)" -ForegroundColor White
    Write-Host "  📌 버전: $($package.version)" -ForegroundColor White
    Write-Host "  📌 명령어: $($package.contributes.commands.Count)개" -ForegroundColor White
    
    if ($package.version -match "^\d+\.\d+\.\d+$") {
        Write-Host "  ✅ 버전 형식 올바름" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  버전 형식 확인 필요: $($package.version)" -ForegroundColor Yellow
        $WarningCount++
    }
} catch {
    Write-Host "  ❌ package.json 파싱 실패" -ForegroundColor Red
    $ErrorCount++
}

# 7. 설정 파일 확인
Write-Host "`n⚙️  7. VS Code 설정 확인..." -ForegroundColor Yellow
if (Test-Path ".vscode/launch.json") {
    Write-Host "  ✅ launch.json 존재" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  launch.json 없음 - F5 실행 불가" -ForegroundColor Yellow
    $WarningCount++
}

if (Test-Path ".vscode/tasks.json") {
    Write-Host "  ✅ tasks.json 존재" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  tasks.json 없음" -ForegroundColor Yellow
    $WarningCount++
}

# 8. 메모리 사용량 확인
Write-Host "`n💾 8. 프로젝트 크기 확인..." -ForegroundColor Yellow
$totalSize = 0
Get-ChildItem -Path "." -Recurse -File -Exclude "node_modules",".git","out" -ErrorAction SilentlyContinue | ForEach-Object {
    $totalSize += $_.Length
}
$sizeMB = [math]::Round($totalSize / 1MB, 2)
Write-Host "  📊 프로젝트 크기: $sizeMB MB (node_modules 제외)" -ForegroundColor White

# 최종 결과
Write-Host "`n=====================================" -ForegroundColor Cyan
Write-Host "  테스트 결과                        " -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

if ($ErrorCount -eq 0 -and $WarningCount -eq 0) {
    Write-Host "✅ 모든 테스트 통과!" -ForegroundColor Green
    Write-Host "`n다음 단계: F5 키를 눌러 Extension Development Host를 실행하세요" -ForegroundColor Cyan
    exit 0
} elseif ($ErrorCount -eq 0) {
    Write-Host "⚠️  $WarningCount 개의 경고가 있지만 실행 가능" -ForegroundColor Yellow
    Write-Host "`n다음 단계: F5 키를 눌러 Extension Development Host를 실행하세요" -ForegroundColor Cyan
    exit 0
} else {
    Write-Host "❌ $ErrorCount 개의 에러 발견" -ForegroundColor Red
    if ($WarningCount -gt 0) {
        Write-Host "⚠️  $WarningCount 개의 경고 발견" -ForegroundColor Yellow
    }
    Write-Host "`n수정이 필요합니다:" -ForegroundColor Red
    Write-Host "  1. npm install (node_modules 없는 경우)" -ForegroundColor White
    Write-Host "  2. npm run compile (컴파일 에러 해결)" -ForegroundColor White
    exit 1
}
