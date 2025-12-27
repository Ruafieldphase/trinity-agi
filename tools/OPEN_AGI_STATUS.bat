@echo off
setlocal
set "WS=%~dp0.."

set "OPS=%WS%\outputs\bridge\human_ops_summary_latest.txt"
set "MSG=%WS%\outputs\bridge\agi_message_latest.txt"
set "AURA=%WS%\outputs\aura_pixel_state.json"

if exist "%OPS%" start "" notepad.exe "%OPS%"
if exist "%MSG%" start "" notepad.exe "%MSG%"
if exist "%AURA%" start "" notepad.exe "%AURA%"

if not exist "%OPS%" if not exist "%MSG%" (
  start "" notepad.exe "%WS%\outputs\bridge"
)
