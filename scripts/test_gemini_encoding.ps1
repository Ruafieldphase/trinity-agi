# Test script for Gemini CLI encoding on Windows
# This script tests the gemini_chat_simple.py wrapper with various Unicode inputs

Write-Host "=== Gemini CLI Encoding Test ===" -ForegroundColor Cyan
Write-Host ""

# Ensure UTF-8 encoding for this PowerShell session
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"

Write-Host "PowerShell encoding settings:" -ForegroundColor Yellow
Write-Host "  OutputEncoding: $([Console]::OutputEncoding.EncodingName)"
Write-Host "  PYTHONIOENCODING: $env:PYTHONIOENCODING"
Write-Host ""

# Test 1: Basic ASCII
Write-Host "Test 1: Basic ASCII text" -ForegroundColor Green
$test1 = "Hello, this is a simple test."
$result1 = $test1 | python scripts/gemini_chat_simple.py --stdin --max-tokens 100
Write-Host "  Input: $test1"
Write-Host "  Output length: $($result1.Length) chars"
Write-Host "  First 100 chars: $($result1.Substring(0, [Math]::Min(100, $result1.Length)))"
Write-Host ""

# Test 2: Unicode with emojis
Write-Host "Test 2: Unicode with common emojis" -ForegroundColor Green
$test2 = "Explain creativity in one sentence (use simple language)"
$result2 = $test2 | python scripts/gemini_chat_simple.py --stdin --max-tokens 100
Write-Host "  Input: $test2"
Write-Host "  Output length: $($result2.Length) chars"
Write-Host "  Output: $result2"
Write-Host ""

# Test 3: Check for encoding errors in output
Write-Host "Test 3: Korean text" -ForegroundColor Green
$test3 = "한글 테스트입니다"
$result3 = $test3 | python scripts/gemini_chat_simple.py --stdin --max-tokens 100
Write-Host "  Input: $test3"
Write-Host "  Output length: $($result3.Length) chars"
Write-Host "  Output: $result3"
Write-Host ""

Write-Host "=== Test Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "If you see garbled characters or errors above, try running:" -ForegroundColor Yellow
Write-Host "  chcp 65001" -ForegroundColor White
Write-Host "  `$OutputEncoding = [System.Text.Encoding]::UTF8" -ForegroundColor White
Write-Host "before running the pipeline." -ForegroundColor Yellow