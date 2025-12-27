@echo off
setlocal
set "WS=%~dp0.."
set "FILE=%WS%\to_agi.txt"
if not exist "%FILE%" (
  echo.>"%FILE%"
)
start "" notepad.exe "%FILE%"
