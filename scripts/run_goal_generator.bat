@echo off
setlocal
cd /d "C:\workspace\agi"
set PYTHONIOENCODING=utf-8
echo [%date% %time%] Starting autonomous goal generator...
"C:\workspace\agi\fdo_agi_repo\.venv\Scripts\python.exe" "C:\workspace\agi\scripts\autonomous_goal_generator.py" --hours 24 2>&1
echo [%date% %time%] Goal generator completed with exit code: %ERRORLEVEL%
exit /b %ERRORLEVEL%
