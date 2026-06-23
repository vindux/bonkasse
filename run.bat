@echo off
call .venv\Scripts\activate.bat

:loop
python main.py
if %errorlevel% neq 0 (
    echo.
    echo Bonkasse crashed ^(exit code %errorlevel%^). Restarting in 3 seconds...
    echo Press Ctrl+C now to stop instead.
    timeout /t 3 >nul
    goto loop
)

echo.
echo Bonkasse closed normally.
