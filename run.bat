@echo off
setlocal
cd /d "%~dp0"

rem Use the virtual environment if there is one, otherwise fall back to a
rem global installation. If neither is available, explain how to install.
if exist ".venv\Scripts\activate.bat" goto activate

python --version >nul 2>&1
if errorlevel 1 goto nopython

python -c "import fastapi, uvicorn, jinja2, sqlalchemy, escpos, bcrypt" >nul 2>&1
if errorlevel 1 goto nodeps

echo No .venv found - using the globally installed Python packages.
goto loop

:activate
call ".venv\Scripts\activate.bat"

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
exit /b 0

:nopython
echo.
echo ERROR: Python was not found.
echo.
echo Install Python 3.10 or newer from https://www.python.org/downloads/
echo and make sure "Add python.exe to PATH" is checked during setup.
echo Afterwards run install.bat in this folder.
echo.
pause
exit /b 1

:nodeps
echo.
echo ERROR: Bonkasse is not installed yet.
echo.
echo There is no virtual environment ^(.venv folder^) in:
echo   %~dp0
echo and the required packages are not installed globally either.
echo.
echo To install everything, double-click install.bat in this folder.
echo.
echo Or do it manually in this folder:
echo   python -m venv .venv
echo   .venv\Scripts\activate.bat
echo   pip install -r requirements.txt
echo.
echo Then start Bonkasse again with run.bat.
echo.
pause
exit /b 1
