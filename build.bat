@echo off
REM Build script for Monitor-AI Assistant using PyInstaller
REM Usage: build.bat [clean] [debug]
REM Options:
REM   clean - Remove previous build artifacts
REM   debug - Build with debug symbols and verbose logging

setlocal enabledelayedexpansion

REM Color codes (using echo with special characters)
set "INFO=[INFO]"
set "SUCCESS=[SUCCESS]"
set "ERROR=[ERROR]"
set "WARNING=[WARNING]"

echo.
echo ========================================
echo Monitor-AI Assistant - Build Pipeline
echo ========================================
echo.

REM Check for arguments
set CLEAN=0
set DEBUG=0

if "%1"=="clean" set CLEAN=1
if "%2"=="clean" set CLEAN=1
if "%1"=="debug" set DEBUG=1
if "%2"=="debug" set DEBUG=1

REM Get current directory
cd /d "%~dp0"

REM Check PyInstaller
echo %INFO% Checking PyInstaller installation...
python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo %ERROR% PyInstaller not found. Installing...
    pip install pyinstaller
    if errorlevel 1 (
        echo %ERROR% Failed to install PyInstaller
        exit /b 1
    )
)
echo %SUCCESS% PyInstaller found

REM Check model file
if not exist "models\mistral-7b-instruct.Q4_0.ggmlv3.bin" (
    echo %ERROR% Model file not found at models\mistral-7b-instruct.Q4_0.ggmlv3.bin
    echo %INFO% Please download the model first
    exit /b 1
)
echo %SUCCESS% Model file verified

REM Clean previous builds
if %CLEAN%==1 (
    echo %INFO% Cleaning previous builds...
    if exist "build" (
        rmdir /s /q "build" >nul 2>&1
        echo %SUCCESS% Removed build\ directory
    )
    if exist "dist" (
        rmdir /s /q "dist" >nul 2>&1
        echo %SUCCESS% Removed dist\ directory
    )
)

REM Determine log level
set LOG_LEVEL=INFO
if %DEBUG%==1 set LOG_LEVEL=DEBUG

REM Build command
echo %INFO% Starting build process...
if %DEBUG%==1 (
    echo %INFO% Debug mode enabled
    python -m PyInstaller MonitorAI.spec ^
        --distpath dist ^
        --buildpath build ^
        --specpath . ^
        --noconfirm ^
        --onefile ^
        --log-level %LOG_LEVEL%
) else (
    python -m PyInstaller MonitorAI.spec ^
        --distpath dist ^
        --buildpath build ^
        --specpath . ^
        --noconfirm ^
        --onefile ^
        --log-level %LOG_LEVEL%
)

if errorlevel 1 (
    echo %ERROR% Build failed with exit code %errorlevel%
    exit /b 1
)

echo %SUCCESS% Build completed successfully!

REM Check output
if exist "dist\MonitorAI.exe" (
    for %%A in ("dist\MonitorAI.exe") do set "SIZE=%%~zA"
    set /a SIZE_MB=SIZE / 1048576
    echo %SUCCESS% Executable created: dist\MonitorAI.exe ^(!SIZE_MB! MB^)
) else (
    echo %ERROR% Output file not found
    exit /b 1
)

echo.
echo ========================================
echo Build Summary
echo ========================================
echo %SUCCESS% Build type: Single-file executable
echo %SUCCESS% Output: dist\MonitorAI.exe
echo.
echo %INFO% Next steps:
echo   1. Test: dist\MonitorAI.exe
echo   2. Verify model loading and OCR
echo   3. Package for distribution
echo.
echo %SUCCESS% Build pipeline completed!
echo.

exit /b 0
