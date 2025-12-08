@echo off
echo Starting AGI Unified Frontend Backend Services...
echo.

:: Set Vertex AI environment variables for FSD real mode
set GOOGLE_CLOUD_PROJECT=naeda-genesis
set GOOGLE_CLOUD_LOCATION=us-central1

cd /d c:\workspace\agi\services

echo Starting Consciousness API (port 8100)...
start /B C:\Python313\python.exe -u consciousness_api.py > consciousness.log 2>&1
timeout /t 2 /nobreak >nul

echo Starting Unconscious Stream (port 8101)...
start /B C:\Python313\python.exe -u unconscious_stream.py > unconscious.log 2>&1
timeout /t 2 /nobreak >nul

echo Starting Background Self API (port 8102)...
start /B C:\Python313\python.exe -u background_self_api.py > background_self.log 2>&1
timeout /t 2 /nobreak >nul

echo Starting Unified Aggregator (port 8104)...
start /B C:\Python313\python.exe -u unified_aggregator.py > unified_aggregator.log 2>&1
timeout /t 2 /nobreak >nul

echo Starting FSD Controller API (port 8105)...
start /B C:\Python313\python.exe -u fsd_server.py > outputs\fsd_server.log 2>&1
timeout /t 2 /nobreak >nul

echo Starting Lua Flow Collector (daemon)...
start /B C:\Python313\python.exe -u lua_flow_collector.py --daemon > outputs\lua_flow_collector.log 2>&1
timeout /t 1 /nobreak >nul

echo Starting Resonance Learning System (Lymphatic)...
cd /d c:\workspace\agi\body
start /B C:\Python313\python.exe -u lymphatic_system.py > lymphatic.log 2>&1
timeout /t 1 /nobreak >nul

echo Starting Slack Interface (Body)...
start /B C:\Python313\python.exe -u slack_interface.py > slack.log 2>&1
timeout /t 1 /nobreak >nul

echo Starting Conscious Mind (Koa)...
cd /d c:\workspace\agi\mind
start /B C:\Python313\python.exe -u koa_conscious.py > koa.log 2>&1
cd /d c:\workspace\agi\services
timeout /t 2 /nobreak >nul

echo Starting Fractal MCP Server (port 50000)...
cd /d c:\workspace\agi
start /B C:\Python313\python.exe -u fdo_agi_repo/lumen_mcp_server.py --port 50000 --transport sse --path /mcp > outputs/mcp_server.log 2>&1
timeout /t 2 /nobreak >nul

echo Starting Fractal Daemon...
start /B powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File scripts/autonomous_goal_loop_daemon.ps1 > outputs/fractal_daemon.log 2>&1
timeout /t 2 /nobreak >nul

echo Generating Context Anchor...
C:\Python313\python.exe scripts/generate_context_anchor.py


echo.
echo All backend services started!
echo.
echo Services running on:
echo   - Consciousness: http://localhost:8100
echo   - Unconscious:   http://localhost:8101
echo   - Background:    http://localhost:8102
echo   - Aggregator:    http://localhost:8104
echo   - FSD:           http://localhost:8105
echo.
echo Press any key to view aggregator status...
pause >nul

curl http://localhost:8104/unified
