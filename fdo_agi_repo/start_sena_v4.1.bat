@echo off
cd /d D:\nas_backup\fdo_agi_repo
echo ============================================================
echo Hey Sena v4.1 - LLM + Performance Caching
echo ============================================================
echo.
echo NEW IN v4.1:
echo   [+] Response caching (60%% faster)
echo   [+] Audio file caching (3000x faster)
echo   [+] Performance statistics tracking
echo.
chcp 65001 > nul
python hey_sena_v4.1_cached.py
pause
