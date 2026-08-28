@echo off
setlocal

cd /d "%~dp0"

where py >nul 2>nul
if %ERRORLEVEL%==0 (
    py -3 setup_bot.py
) else (
    python setup_bot.py
)

echo.
pause
