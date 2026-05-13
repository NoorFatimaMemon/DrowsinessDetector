@echo off
setlocal enabledelayedexpansion

REM Change to the script directory
cd /d "%~dp0"

echo ============================================
echo   Drowsiness Detector - Real-time Monitor
echo ============================================
echo.

REM Check if the virtual environment exists
if exist "rabia\Scripts\activate.bat" (
    echo Virtual environment found.
    goto :RUN
)

REM Virtual environment not found — create it
echo Virtual environment not found.
echo Creating Python virtual environment...
python -m venv rabia
if !ERRORLEVEL! neq 0 (
    echo [ERROR] Failed to create virtual environment.
    echo Make sure Python 3.9+ is installed and on your PATH.
    pause
    exit /b 1
)
echo Virtual environment created successfully.

echo Installing dependencies from requirements.txt...
rabia\Scripts\pip.exe install -r requirements.txt
if !ERRORLEVEL! neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)
echo Dependencies installed successfully.
echo.

:RUN
echo Activating virtual environment...
call rabia\Scripts\activate.bat

echo Starting Drowsiness Detector...
echo.

REM Run the detector
python "src\drowsinessDetector.py" %*

echo.
echo Drowsiness Detector has exited.
echo.
echo Check the following directories for results:
echo   - snapshots\     (captured images)
echo   - events\        (JSON event logs)
echo   - logs\          (detailed logs)
echo.
pause