@echo off
call .venv\Scripts\activate.bat
python main.py
if %errorlevel% neq 0 (
    echo.
    echo Program exited with error code %errorlevel%
    pause
)
