@echo off
chcp 65001 > nul
title Hey Sena - Starting...
echo ============================================================
echo Starting Hey Sena Voice Assistant
echo ============================================================
echo.
echo System is starting...
echo Say "Hey Sena" or "세나야" to activate
echo Say "종료" or "Stop listening" to exit
echo.
echo ============================================================
echo.

cd /d D:\nas_backup\fdo_agi_repo
python hey_sena_v2.py

pause
