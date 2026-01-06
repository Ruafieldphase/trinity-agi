# VS Code Copilot Performance Analysis
# Copilot 응답 속도 저하 원인 분석 및 해결


. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot
Write-Host "`n=== VS Code Copilot Performance Analysis ===" -ForegroundColor Cyan
Write-Host "Analyzing workspace complexity impact on Copilot..." -ForegroundColor Yellow

$workspace = "$WorkspaceRoot"

# 1. Workspace 크기 분석
Write-Host "`n[1/6] Workspace Size Analysis" -ForegroundColor Cyan
$totalFiles = (Get-ChildItem $workspace -Recurse -File -ErrorAction SilentlyContinue).Count
$pythonFiles = (Get-ChildItem $workspace -Recurse -Filter "*.py" -File -ErrorAction SilentlyContinue).Count
$mdFiles = (Get-ChildItem $workspace -Recurse -Filter "*.md" -File -ErrorAction SilentlyContinue).Count
$totalSize = [Math]::Round(((Get-ChildItem $workspace -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB), 2)

Write-Host "  Total files: $totalFiles"
Write-Host "  Python files: $pythonFiles"
Write-Host "  Markdown files: $mdFiles"
Write-Host "  Total size: ${totalSize} MB"

if ($totalFiles -gt 5000) {
    Write-Host "  ⚠️  WARNING: Very large workspace (>5000 files)" -ForegroundColor Red
    Write-Host "     Copilot needs to index all files for context"
}

# 2. Git 상태 (인덱싱 부하)
Write-Host "`n[2/6] Git Repository Status" -ForegroundColor Cyan
try {
    Push-Location $workspace
    $untrackedCount = (git ls-files --others --exclude-standard 2>$null).Count
    $modifiedCount = (git diff --name-only 2>$null).Count
    Pop-Location
    
    Write-Host "  Untracked files: $untrackedCount"
    Write-Host "  Modified files: $modifiedCount"
    
    if ($untrackedCount -gt 1000) {
        Write-Host "  ⚠️  WARNING: Many untracked files (>1000)" -ForegroundColor Red
        Write-Host "     VS Code continuously watches these"
    }
} catch {
    Write-Host "  Git check skipped"
}

# 3. node_modules / .venv 크기 (VS Code 인덱싱)
Write-Host "`n[3/6] Heavy Directories Check" -ForegroundColor Cyan

$heavyDirs = @(
    @{Path="node_modules"; Exclude=$true},
    @{Path=".venv"; Exclude=$true},
    @{Path="LLM_Unified\.venv"; Exclude=$true},
    @{Path="fdo_agi_repo\.venv"; Exclude=$true},
    @{Path="outputs"; Exclude=$false},
    @{Path="memory"; Exclude=$false}
)

foreach ($dir in $heavyDirs) {
    $fullPath = Join-Path $workspace $dir.Path
    if (Test-Path $fullPath) {
        $size = [Math]::Round(((Get-ChildItem $fullPath -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB), 2)
        $fileCount = (Get-ChildItem $fullPath -Recurse -File -ErrorAction SilentlyContinue).Count
        
        $status = if ($dir.Exclude) { "✅ Should be excluded" } else { "⚠️  Indexed" }
        Write-Host "  $($dir.Path): ${size} MB ($fileCount files) - $status"
        
        if ($size -gt 500 -and -not $dir.Exclude) {
            Write-Host "    🔴 This directory should be excluded from indexing!" -ForegroundColor Red
        }
    }
}

# 4. .vscodeignore 확인
Write-Host "`n[4/6] VS Code Ignore Configuration" -ForegroundColor Cyan
$vscodeIgnore = Join-Path $workspace ".vscodeignore"
$gitignore = Join-Path $workspace ".gitignore"

if (Test-Path $vscodeIgnore) {
    Write-Host "  ✅ .vscodeignore exists"
} else {
    Write-Host "  ❌ .vscodeignore NOT found" -ForegroundColor Red
    Write-Host "     VS Code will index everything!"
}

# 5. settings.json 확인
Write-Host "`n[5/6] VS Code Settings Check" -ForegroundColor Cyan
$settingsPath = Join-Path $workspace ".vscode\settings.json"

if (Test-Path $settingsPath) {
    $settings = Get-Content $settingsPath -Raw | ConvertFrom-Json -ErrorAction SilentlyContinue
    
    $excludeKeys = @(
        "files.exclude",
        "search.exclude",
        "files.watcherExclude"
    )
    
    foreach ($key in $excludeKeys) {
        if ($settings.PSObject.Properties.Name -contains $key) {
            Write-Host "  ✅ $key configured"
        } else {
            Write-Host "  ⚠️  $key NOT configured" -ForegroundColor Yellow
        }
    }
    
    # Copilot 설정 확인
    if ($settings.PSObject.Properties.Name -contains "github.copilot.advanced") {
        Write-Host "  ℹ️  Copilot advanced settings found"
    }
} else {
    Write-Host "  ⚠️  .vscode/settings.json NOT found" -ForegroundColor Yellow
}

# 6. Extension Host 메모리 사용량 추정
Write-Host "`n[6/6] VS Code Process Analysis" -ForegroundColor Cyan

$codeProcs = Get-Process -Name "Code*" -ErrorAction SilentlyContinue
if ($codeProcs) {
    $totalMem = [Math]::Round((($codeProcs | Measure-Object -Property WorkingSet -Sum).Sum / 1MB), 2)
    Write-Host "  VS Code processes: $($codeProcs.Count)"
    Write-Host "  Total memory: ${totalMem} MB"
    
    if ($totalMem -gt 2000) {
        Write-Host "  ⚠️  High memory usage (>2GB)" -ForegroundColor Yellow
        Write-Host "     Extension Host may be overloaded"
    }
}

# === 결론 및 권장사항 ===
Write-Host "`n=== Root Cause Analysis ===" -ForegroundColor Cyan

$issues = @()

if ($totalFiles -gt 5000) {
    $issues += "Workspace too large ($totalFiles files)"
}

if ($untrackedCount -gt 1000) {
    $issues += "Many untracked files ($untrackedCount)"
}

if (-not (Test-Path $vscodeIgnore)) {
    $issues += "Missing .vscodeignore"
}

if ($issues.Count -gt 0) {
    Write-Host "🔴 Performance Issues Detected:" -ForegroundColor Red
    $issues | ForEach-Object { Write-Host "  - $_" }
    
    Write-Host "`n=== Recommended Fixes ===" -ForegroundColor Green
    Write-Host ""
    Write-Host "1️⃣  Create/Update .vscodeignore:" -ForegroundColor Cyan
    Write-Host "   powershell $WorkspaceRoot\scripts\create_vscodeignore.ps1"
    Write-Host ""
    Write-Host "2️⃣  Update VS Code settings.json:" -ForegroundColor Cyan
    Write-Host "   powershell $WorkspaceRoot\scripts\optimize_vscode_settings.ps1"
    Write-Host ""
    Write-Host "3️⃣  Disable Copilot for heavy files:" -ForegroundColor Cyan
    Write-Host "   Add to settings: 'github.copilot.enable': {'*': true, 'jsonl': false}"
    Write-Host ""
    Write-Host "4️⃣  Restart VS Code Extension Host:" -ForegroundColor Cyan
    Write-Host "   Ctrl+Shift+P → 'Developer: Restart Extension Host'"
    Write-Host ""
    
    Write-Host "Expected Improvement: 50-80% faster Copilot responses" -ForegroundColor Green
} else {
    Write-Host "✅ No obvious configuration issues" -ForegroundColor Green
    Write-Host ""
    Write-Host "Possible causes:"
    Write-Host "  - Copilot server congestion (external)"
    Write-Host "  - Network latency"
    Write-Host "  - Too many open files in editor"
    Write-Host "  - Other VS Code extensions competing"
}

Write-Host ""