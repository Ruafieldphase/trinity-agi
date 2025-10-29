@echo off
REM Daily Health Check Runner for Windows Task Scheduler
REM Runs every day at 9:00 AM to check AGI system health

cd /d D:\nas_backup\fdo_agi_repo
python scripts\daily_health_check.py >> logs\health_check.log 2>&1

REM Exit code will be 0 (HEALTHY), 1 (WARNING), or 2 (CRITICAL)
exit /b %ERRORLEVEL%
