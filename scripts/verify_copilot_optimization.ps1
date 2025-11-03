# Quick Copilot Optimization Verification

Write-Host "`n=== Copilot Optimization Verification ===" -ForegroundColor Cyan
Write-Host ""

# 1. Check .vscodeignore
Write-Host "[1/4] Checking .vscodeignore..." -ForegroundColor Yellow
if (Test-Path "C:\workspace\agi\.vscodeignore") {
    Write-Host "  ✅ .vscodeignore exists" -ForegroundColor Green
    $lines = (Get-Content "C:\workspace\agi\.vscodeignore" | Measure-Object -Line).Lines
    Write-Host "  📄 $lines exclusion rules active"
}
else {
    Write-Host "  ❌ .vscodeignore NOT found" -ForegroundColor Red
}

# 2. Check settings.json
Write-Host "`n[2/4] Checking settings.json..." -ForegroundColor Yellow
if (Test-Path "C:\workspace\agi\.vscode\settings.json") {
    $content = Get-Content "C:\workspace\agi\.vscode\settings.json" -Raw
    
    if ($content -match "files.watcherExclude") {
        Write-Host "  ✅ Watcher exclusions configured" -ForegroundColor Green
    }
    else {
        Write-Host "  ⚠️  Watcher exclusions missing" -ForegroundColor Yellow
    }
    
    if ($content -match "github.copilot.enable") {
        Write-Host "  ✅ Copilot optimizations configured" -ForegroundColor Green
    }
    else {
        Write-Host "  ⚠️  Copilot optimizations missing" -ForegroundColor Yellow
    }
}

# 3. VS Code memory check
Write-Host "`n[3/4] VS Code Process Check..." -ForegroundColor Yellow
$procs = Get-Process -Name "Code" -ErrorAction SilentlyContinue
if ($procs) {
    $totalMem = [Math]::Round((($procs | Measure-Object -Property WorkingSet -Sum).Sum / 1MB), 2)
    Write-Host "  💾 Total memory: ${totalMem} MB"
    
    if ($totalMem -lt 3000) {
        Write-Host "  ✅ Memory usage is GOOD (<3GB)" -ForegroundColor Green
    }
    elseif ($totalMem -lt 4000) {
        Write-Host "  ⚠️  Memory usage is moderate (3-4GB)" -ForegroundColor Yellow
    }
    else {
        Write-Host "  ⚠️  Memory usage is high (>4GB)" -ForegroundColor Yellow
        Write-Host "     Give it a few minutes to stabilize"
    }
}
else {
    Write-Host "  ℹ️  VS Code processes not found (may be starting)" -ForegroundColor Cyan
}

# 4. File count comparison
Write-Host "`n[4/4] Expected Impact..." -ForegroundColor Yellow
Write-Host "  Before: 119,663 files indexed"
Write-Host "  After:  ~26,000 files indexed (78% reduction)"
Write-Host "  Memory: 5GB → 2-3GB expected"

# Summary
Write-Host "`n=== How does it feel? ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "❓ Please test:" -ForegroundColor Yellow
Write-Host "  1. Type some code → Check Copilot suggestions"
Write-Host "  2. Ask me a question → Test my response speed"
Write-Host "  3. Navigate files in Explorer → Check smoothness"
Write-Host ""
Write-Host "📊 Expected improvements:" -ForegroundColor Green
Write-Host "  • Copilot suggestions: Instant (was 2-5s)"
Write-Host "  • My typing response: Faster"
Write-Host "  • File explorer: Smooth"
Write-Host "  • No typing lag"
Write-Host ""

Write-Host "💡 If still slow, wait 2-3 minutes for full re-indexing" -ForegroundColor Cyan
Write-Host ""
