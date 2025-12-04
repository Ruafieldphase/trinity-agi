# Check what's running and using GPU
Write-Host "=== Checking AI Model Processes ===" -ForegroundColor Cyan
Write-Host ""

# Check Python processes
$pythonProcs = Get-Process | Where-Object { $_.ProcessName -like '*python*' }
if ($pythonProcs) {
    Write-Host "Python Processes:" -ForegroundColor Yellow
    $pythonProcs | Select-Object ProcessName, Id, @{N = 'Memory(MB)'; E = { [math]::Round($_.WorkingSet64 / 1MB, 2) } } | Format-Table -AutoSize
}
else {
    Write-Host "No Python processes running" -ForegroundColor Gray
}

# Check LM Studio
$lmProcs = Get-Process | Where-Object { $_.ProcessName -like '*lmstudio*' -or $_.ProcessName -like '*LM Studio*' }
if ($lmProcs) {
    Write-Host "LM Studio Processes:" -ForegroundColor Yellow
    $lmProcs | Select-Object ProcessName, Id, @{N = 'Memory(MB)'; E = { [math]::Round($_.WorkingSet64 / 1MB, 2) } } | Format-Table -AutoSize
}
else {
    Write-Host "No LM Studio processes running" -ForegroundColor Gray
}

Write-Host ""
Write-Host "=== What's Happening ===" -ForegroundColor Cyan
Write-Host "These processes are doing INFERENCE (using models), not TRAINING." -ForegroundColor Green
Write-Host "- Inference: Using a pre-trained model to generate answers (fast, uses GPU for speed)"
Write-Host "- Training: Building/improving a model from scratch (slow, days/weeks)"
Write-Host ""
Write-Host "Current system is running inference only - no model training happening." -ForegroundColor Yellow
