@echo off
title Instagram Reels Bot
cls

echo ========================================
echo    Instagram Reels Bot
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python not found. Install Python 3.7+ and add to PATH.
    pause
    exit /b 1
)

REM Run launcher
python run_bot.py
pause