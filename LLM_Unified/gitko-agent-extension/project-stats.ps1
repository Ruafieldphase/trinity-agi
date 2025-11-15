# Gitko Extension - Project Statistics

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "  Gitko Extension - Project Stats  " -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Source files
Write-Host "📁 Source Files:" -ForegroundColor Yellow
$tsFiles = Get-ChildItem -Path "src" -Filter "*.ts" -Recurse
Write-Host "  TypeScript files: $($tsFiles.Count)" -ForegroundColor White

$totalLines = 0
foreach ($file in $tsFiles) {
    $lines = (Get-Content $file.FullName).Count
    $totalLines += $lines
    Write-Host ("    {0,-30} {1,5} lines" -f $file.Name, $lines) -ForegroundColor Gray
}
Write-Host "  Total lines: $totalLines" -ForegroundColor Green
Write-Host ""

# Compiled files
Write-Host "🔨 Compiled Files:" -ForegroundColor Yellow
if (Test-Path "out") {
    $jsFiles = Get-ChildItem -Path "out" -Filter "*.js" -Recurse
    $mapFiles = Get-ChildItem -Path "out" -Filter "*.js.map" -Recurse
    Write-Host "  JavaScript files: $($jsFiles.Count)" -ForegroundColor White
    Write-Host "  Source maps: $($mapFiles.Count)" -ForegroundColor White
} else {
    Write-Host "  No compiled files (run 'npm run compile')" -ForegroundColor Red
}
Write-Host ""

# Documentation
Write-Host "📚 Documentation:" -ForegroundColor Yellow
$mdFiles = Get-ChildItem -Path "." -Filter "*.md" -Exclude "node_modules"
Write-Host "  Markdown files: $($mdFiles.Count)" -ForegroundColor White

$docLines = 0
foreach ($file in $mdFiles) {
    $lines = (Get-Content $file.FullName).Count
    $docLines += $lines
}
Write-Host "  Total doc lines: $docLines" -ForegroundColor Green
Write-Host ""

# Package info
Write-Host "📦 Package Info:" -ForegroundColor Yellow
if (Test-Path "package.json") {
    $package = Get-Content "package.json" | ConvertFrom-Json
    Write-Host "  Name: $($package.name)" -ForegroundColor White
    Write-Host "  Version: $($package.version)" -ForegroundColor White
    Write-Host "  Description: $($package.description)" -ForegroundColor White
    
    $commands = $package.contributes.commands
    Write-Host "  Commands: $($commands.Count)" -ForegroundColor Green
}
Write-Host ""

# Dependencies
Write-Host "📚 Dependencies:" -ForegroundColor Yellow
if (Test-Path "package.json") {
    $package = Get-Content "package.json" | ConvertFrom-Json
    
    if ($package.dependencies) {
        Write-Host "  Production:" -ForegroundColor White
        $package.dependencies.PSObject.Properties | ForEach-Object {
            Write-Host "    - $($_.Name): $($_.Value)" -ForegroundColor Gray
        }
    }
    
    if ($package.devDependencies) {
        Write-Host "  Development:" -ForegroundColor White
        $depCount = ($package.devDependencies.PSObject.Properties | Measure-Object).Count
        Write-Host "    $depCount packages" -ForegroundColor Gray
    }
}
Write-Host ""

# Git status
Write-Host "🔧 Git Status:" -ForegroundColor Yellow
if (Test-Path ".git") {
    try {
        $status = git status --porcelain 2>$null
        if ($status) {
            $modified = ($status | Where-Object { $_ -match "^ M" }).Count
            $added = ($status | Where-Object { $_ -match "^A " }).Count
            $untracked = ($status | Where-Object { $_ -match "^\?\?" }).Count
            
            Write-Host "  Modified: $modified" -ForegroundColor $(if ($modified -gt 0) { "Yellow" } else { "Green" })
            Write-Host "  Added: $added" -ForegroundColor $(if ($added -gt 0) { "Yellow" } else { "Green" })
            Write-Host "  Untracked: $untracked" -ForegroundColor $(if ($untracked -gt 0) { "Yellow" } else { "Green" })
        } else {
            Write-Host "  Working tree clean ✅" -ForegroundColor Green
        }
    } catch {
        Write-Host "  Git not available" -ForegroundColor Gray
    }
} else {
    Write-Host "  Not a git repository" -ForegroundColor Gray
}
Write-Host ""

# Summary
Write-Host "📊 Summary:" -ForegroundColor Yellow
Write-Host "  Total TypeScript: $totalLines lines" -ForegroundColor Green
Write-Host "  Total Documentation: $docLines lines" -ForegroundColor Green
Write-Host "  Grand Total: $($totalLines + $docLines) lines" -ForegroundColor Cyan
Write-Host ""

# Size estimation
Write-Host "💾 Size Estimation:" -ForegroundColor Yellow
$totalSize = 0
Get-ChildItem -Path "." -Recurse -Exclude "node_modules",".git","out" | ForEach-Object {
    $totalSize += $_.Length
}
$sizeMB = [math]::Round($totalSize / 1MB, 2)
Write-Host "  Project size (excl. node_modules): $sizeMB MB" -ForegroundColor White
Write-Host ""

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "  Analysis Complete! ✨             " -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
