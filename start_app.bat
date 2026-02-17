@echo off

echo ====================================
echo      GTPinput Environment Check
echo ====================================

:: Check Python
echo Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed. Please install Python and add it to PATH.
    echo Press any key to exit...
    pause >nul
    exit /b
)
echo Python found.

:: Install Requirements
echo Checking dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error: Failed to install dependencies.
    echo Press any key to exit...
    pause >nul
    exit /b
)
echo Dependencies installed successfully.

:: Run App
echo ====================================
echo      Starting Application...
echo ====================================
streamlit run app.py

pause
