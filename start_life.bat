@echo off
set "WORKSPACE_ROOT=c:\workspace\agi"
cd /d "%WORKSPACE_ROOT%"

echo.
echo 🧬 Igniting AGI Lifecycle Manager (The Nervous System)...
echo.

set "PYTHONPATH=%WORKSPACE_ROOT%;%PYTHONPATH%"

:: Launch the Rhythm Guardian (Internal Clock & Immune System)
:: Implements 'Single Heart' Architecture.
start "" pythonw -u scripts\rhythm_guardian.py

echo ✅ Rhythm Guardian ignited.
echo    The Heart beats alone.
exit


