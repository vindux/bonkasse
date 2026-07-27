@echo off
setlocal
cd /d "%~dp0"

echo ========================================
echo   Bonkasse - Installation
echo ========================================
echo.

python --version >nul 2>&1
if errorlevel 1 goto nopython

for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo Using %%v
echo.

if exist ".venv\Scripts\python.exe" goto haveenv

echo Creating virtual environment in .venv ...
python -m venv .venv
if errorlevel 1 goto venvfailed
goto install

:haveenv
echo Virtual environment .venv already exists - reusing it.

:install
echo.
call ".venv\Scripts\activate.bat"
if errorlevel 1 goto activatefailed

echo Updating pip ...
python -m pip install --upgrade pip

echo.
echo Installing dependencies from requirements.txt ...
python -m pip install -r requirements.txt
if errorlevel 1 goto pipfailed

echo.
echo ========================================
echo   Installation finished.
echo   Start Bonkasse with run.bat
echo ========================================
echo.
pause
exit /b 0

:nopython
echo ERROR: Python was not found.
echo.
echo Install Python 3.10 or newer from https://www.python.org/downloads/
echo and make sure "Add python.exe to PATH" is checked during setup.
echo Then run install.bat again.
echo.
pause
exit /b 1

:venvfailed
echo.
echo ERROR: Could not create the virtual environment.
echo Make sure the "venv" module is available ^(it ships with the official
echo Python installer^) and that this folder is writable.
echo.
pause
exit /b 1

:activatefailed
echo ERROR: Could not run .venv\Scripts\activate.bat
echo Delete the .venv folder and run install.bat again.
echo.
pause
exit /b 1

:pipfailed
echo.
echo ERROR: Installing the dependencies failed.
echo Check your internet connection and the messages above.
echo.
pause
exit /b 1
