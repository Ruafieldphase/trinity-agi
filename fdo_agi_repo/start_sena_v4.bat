@echo off
REM Hey Sena v4 LLM-Powered Launcher
REM Start the voice assistant with full LLM capabilities

cd /d D:\nas_backup\fdo_agi_repo

echo.
echo ============================================================
echo   Starting Hey Sena v4 (LLM-Powered AGI)
echo ============================================================
echo.
echo NEW: Answer ANY question with Gemini Flash LLM!
echo.

REM Set UTF-8 encoding
chcp 65001 > nul

REM Check API key
if not defined GEMINI_API_KEY (
    if exist .env (
        echo [INFO] Loading API key from .env file...
    ) else (
        echo [WARNING] GEMINI_API_KEY not set!
        echo [INFO] LLM features will be disabled.
        echo [INFO] Only rule-based responses will work.
        echo.
        pause
    )
)

REM Activate virtual environment if exists
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

REM Run Hey Sena v4
python hey_sena_v4_llm.py

pause
