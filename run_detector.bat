@echo off
setlocal enabledelayedexpansion

REM Change to the script directory
cd /d "%~dp0"

echo ============================================
echo   Drowsiness Detector - Real-time Monitor
echo ============================================
echo.

REM Check if the virtual environment exists
if not exist "rabia\Scripts\activate.bat" (
    echo Error: Virtual environment not found!
    echo Please run: python -m venv rabia
    echo Then run: rabia\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

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
