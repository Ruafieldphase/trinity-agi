@echo off
echo 🌉 Starting Background Self Bridge with Vertex AI (Windows Batch)...

set VERTEX_PROJECT_ID=naeda-genesis
set VERTEX_LOCATION=global
set GOOGLE_APPLICATION_CREDENTIALS=C:\workspace\original_data\Obsidian_Vault\Nas_Obsidian_Vault\naeda-genesis-5034a5936036.json

echo    Project: %VERTEX_PROJECT_ID%
echo    Location: %VERTEX_LOCATION%
echo    Credentials: %GOOGLE_APPLICATION_CREDENTIALS%
echo.

python scripts/linux/background_self_bridge.py
pause
