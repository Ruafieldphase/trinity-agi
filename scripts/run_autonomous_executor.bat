@echo off
cd /d "C:\workspace\agi"
"C:\workspace\agi\fdo_agi_repo\.venv\Scripts\python.exe" "C:\workspace\agi\scripts\autonomous_goal_executor.py" > "C:\workspace\agi\outputs\logs\autonomous_executor_%date:~0,10%.log" 2>&1
