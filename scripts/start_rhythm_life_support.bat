@echo off
REM ========================================
REM AGI Rhythm Life Support System (Windows)
REM ========================================
REM This script starts the rhythm_think.py in the background
REM and the sync_rhythm_from_linux.py to keep Windows/Linux in sync.
REM 
REM Add this to Windows Startup or Task Scheduler for auto-start.
REM ========================================

cd /d C:\workspace\agi

echo [%date% %time%] Starting AGI Rhythm Life Support... >> logs\rhythm_autostart.log

REM Start rhythm_think.py in background (hidden window)
start /B pythonw scripts\rhythm_think.py >> logs\rhythm_think.log 2>&1

REM Wait 5 seconds then start sync
timeout /t 5 /nobreak > nul

REM Start rhythm sync from Linux (runs periodically)
start /B pythonw scripts\sync_rhythm_from_linux.py >> logs\rhythm_sync.log 2>&1

echo [%date% %time%] AGI Rhythm Life Support started. >> logs\rhythm_autostart.log
