#!/usr/bin/env pwsh
# Gitko Agent Extension - Workspace Organization Script
# 작업: 문서 정리, 테스트 구조화, 스크립트 정리

Write-Host "🚀 Starting workspace organization..." -ForegroundColor Cyan

# 1. 디렉토리 생성
Write-Host "`n📁 Creating directory structure..." -ForegroundColor Yellow
$directories = @(
    "docs",
    "docs/archive",
    "docs/releases",
    "tests",
    "scripts",
    "scripts/setup"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  ✅ Created: $dir" -ForegroundColor Green
    } else {
        Write-Host "  ⏭️  Exists: $dir" -ForegroundColor Gray
    }
}

# 2. 구버전 완료 보고서 아카이빙
Write-Host "`n📦 Archiving old completion reports..." -ForegroundColor Yellow
$archiveFiles = @(
    "COMPLETION_REPORT_v0.2.0.md",
    "COMPLETION_REPORT_v0.2.1.md",
    "FINAL_SUMMARY.md",
    "FINAL_ENHANCEMENTS.md"
)

foreach ($file in $archiveFiles) {
    if (Test-Path $file) {
        Move-Item $file "docs/archive/" -Force
        Write-Host "  ✅ Archived: $file" -ForegroundColor Green
    }
}

# 3. 릴리스 노트 정리
Write-Host "`n📋 Organizing release notes..." -ForegroundColor Yellow
$releaseFiles = @(
    "RELEASE_NOTES_v0.2.0.md",
    "RELEASE_NOTES_v0.2.1.md",
    "RELEASE_NOTES_v0.3.0.md"
)

foreach ($file in $releaseFiles) {
    if (Test-Path $file) {
        Move-Item $file "docs/releases/" -Force
        Write-Host "  ✅ Moved: $file" -ForegroundColor Green
    }
}

# 4. 최신 릴리스 노트는 루트에 유지 (심볼릭 링크 대신 복사)
if (Test-Path "RELEASE_NOTES_v0.3.1.md") {
    Copy-Item "RELEASE_NOTES_v0.3.1.md" "RELEASE_NOTES.md" -Force
    Move-Item "RELEASE_NOTES_v0.3.1.md" "docs/releases/" -Force
    Write-Host "  ✅ Created RELEASE_NOTES.md (latest)" -ForegroundColor Green
}

# 5. 최신 완료 보고서 유지
if (Test-Path "COMPLETION_REPORT_v0.3.0.md") {
    Copy-Item "COMPLETION_REPORT_v0.3.0.md" "COMPLETION_REPORT.md" -Force
    Move-Item "COMPLETION_REPORT_v0.3.0.md" "docs/archive/" -Force
    Write-Host "  ✅ Created COMPLETION_REPORT.md (latest)" -ForegroundColor Green
}

# 6. 가이드 문서 정리
Write-Host "`n📚 Organizing guide documents..." -ForegroundColor Yellow
$guideFiles = @(
    "DEPLOYMENT_CHECKLIST.md",
    "RELEASE_CHECKLIST.md",
    "SETUP_GUIDE.md",
    "USAGE_EXAMPLES.md",
    "AUTOMATIC_AGENT_GUIDE.md",
    "CHEATSHEET.md"
)

foreach ($file in $guideFiles) {
    if (Test-Path $file) {
        Move-Item $file "docs/" -Force
        Write-Host "  ✅ Moved: $file" -ForegroundColor Green
    }
}

# 7. QUICKSTART 중복 해결
Write-Host "`n🔧 Resolving QUICKSTART duplicates..." -ForegroundColor Yellow
if ((Test-Path "QUICKSTART.md") -and (Test-Path "QUICK_START.md")) {
    # 둘 다 있으면 QUICKSTART.md를 메인으로
    Remove-Item "QUICK_START.md" -Force
    Write-Host "  ✅ Removed duplicate: QUICK_START.md" -ForegroundColor Green
}

# 8. 테스트 파일 이동
Write-Host "`n🧪 Organizing test files..." -ForegroundColor Yellow
$testFiles = @(
    "test_integration.ps1",
    "test_integration_simple.py",
    "test-extension.ps1"
)

foreach ($file in $testFiles) {
    if (Test-Path $file) {
        Move-Item $file "tests/" -Force
        Write-Host "  ✅ Moved: $file" -ForegroundColor Green
    }
}

# 9. 스크립트 정리
Write-Host "`n⚙️  Organizing scripts..." -ForegroundColor Yellow

# Setup 스크립트
$setupScripts = @(
    "install_tesseract.ps1",
    "install_tesseract_admin.ps1",
    "install_tesseract_choco.ps1",
    "install_tesseract_manual.ps1",
    "install_tesseract_winget.ps1",
    "configure_tesseract.ps1"
)

foreach ($file in $setupScripts) {
    if (Test-Path $file) {
        Move-Item $file "scripts/setup/" -Force
        Write-Host "  ✅ Moved to setup: $file" -ForegroundColor Green
    }
}

# 일반 스크립트
$generalScripts = @(
    "troubleshoot.ps1",
    "project-stats.ps1"
)

foreach ($file in $generalScripts) {
    if (Test-Path $file) {
        Move-Item $file "scripts/" -Force
        Write-Host "  ✅ Moved: $file" -ForegroundColor Green
    }
}

# Python 스크립트
$pythonScripts = @(
    "auto_resume_session.py",
    "reload_vscode_with_ocr.py"
)

foreach ($file in $pythonScripts) {
    if (Test-Path $file) {
        Move-Item $file "scripts/" -Force
        Write-Host "  ✅ Moved: $file" -ForegroundColor Green
    }
}

# 10. .gitignore 개선
Write-Host "`n🚫 Updating .gitignore..." -ForegroundColor Yellow
$gitignoreContent = @"

# Python
__pycache__/
*.pyc
*.pyo
.pytest_cache/
*.egg-info/

# VS Code Extension
out/
dist/
*.vsix

# Logs
*.log

# Temporary files
.gitko-session-state.json
temp_*

# OS
.DS_Store
Thumbs.db
"@

if (Test-Path ".gitignore") {
    Add-Content -Path ".gitignore" -Value $gitignoreContent
    Write-Host "  ✅ Updated .gitignore" -ForegroundColor Green
} else {
    Set-Content -Path ".gitignore" -Value $gitignoreContent
    Write-Host "  ✅ Created .gitignore" -ForegroundColor Green
}

# 11. requirements.txt 생성
Write-Host "`n📦 Creating requirements.txt..." -ForegroundColor Yellow
$requirementsContent = @"
# Python dependencies for Gitko Agent Extension
# For auto-resume session and integration tests

# Core
requests>=2.31.0
python-dotenv>=1.0.0

# Testing (optional)
pytest>=7.4.0
pytest-asyncio>=0.21.0
"@

Set-Content -Path "requirements.txt" -Value $requirementsContent
Write-Host "  ✅ Created requirements.txt" -ForegroundColor Green

# 12. 요약 출력
Write-Host "`n✨ Organization complete!" -ForegroundColor Cyan
Write-Host "`n📊 Summary:" -ForegroundColor Yellow
Write-Host "  • Created directory structure (docs/, tests/, scripts/)" -ForegroundColor White
Write-Host "  • Archived old completion reports → docs/archive/" -ForegroundColor White
Write-Host "  • Organized release notes → docs/releases/" -ForegroundColor White
Write-Host "  • Moved guides → docs/" -ForegroundColor White
Write-Host "  • Organized tests → tests/" -ForegroundColor White
Write-Host "  • Organized scripts → scripts/" -ForegroundColor White
Write-Host "  • Updated .gitignore" -ForegroundColor White
Write-Host "  • Created requirements.txt" -ForegroundColor White

Write-Host "`n📁 New structure:" -ForegroundColor Yellow
Write-Host @"
  gitko-agent-extension/
  ├── docs/
  │   ├── archive/       (구버전 보고서)
  │   ├── releases/      (릴리스 노트)
  │   └── *.md          (가이드)
  ├── scripts/
  │   ├── setup/        (설치 스크립트)
  │   └── *.ps1, *.py
  ├── tests/
  │   └── test_*.ps1, test_*.py
  ├── src/
  ├── README.md
  ├── COMPLETION_REPORT.md (최신)
  └── RELEASE_NOTES.md (최신)
"@ -ForegroundColor White

Write-Host "`n✅ Done! Workspace is now organized." -ForegroundColor Green
