@echo off
REM ContentGuard Deployment Script for Windows
REM This script helps deploy ContentGuard components

setlocal enabledelayedexpansion

echo ╔════════════════════════════════════════════════════════════╗
echo ║         ContentGuard Deployment Script (Windows)           ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

:menu
echo.
echo What would you like to deploy?
echo.
echo 1) Setup Environment (install dependencies, create directories)
echo 2) Start API Server (FastAPI backend)
echo 3) Start Dashboard (Streamlit)
echo 4) Package Extension (create ZIP for Chrome Web Store)
echo 5) Full Setup (setup + start API)
echo 6) Check System Requirements
echo 7) Exit
echo.

set /p choice="Enter your choice [1-7]: "

if "%choice%"=="1" goto setup
if "%choice%"=="2" goto start_api
if "%choice%"=="3" goto start_dashboard
if "%choice%"=="4" goto package_extension
if "%choice%"=="5" goto full_setup
if "%choice%"=="6" goto check_requirements
if "%choice%"=="7" goto exit
goto invalid_choice

:setup
echo.
echo [INFO] Setting up environment...
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.9+
    goto menu
) else (
    echo [OK] Python found
)

REM Check pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip not found. Please install pip
    goto menu
) else (
    echo [OK] pip found
)

REM Create directories
echo [INFO] Creating necessary directories...
if not exist "data\processed" mkdir data\processed
if not exist "models\bert\final_model" mkdir models\bert\final_model
if not exist "logs" mkdir logs
echo [OK] Directories created

REM Install dependencies
echo [INFO] Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    goto menu
)
echo [OK] Dependencies installed

REM Initialize database
echo [INFO] Initializing database...
python -c "from api.database.db import init_db; init_db()"
if errorlevel 1 (
    echo [WARNING] Database initialization failed (may already exist)
) else (
    echo [OK] Database initialized
)

echo.
echo [SUCCESS] Environment setup complete!
echo.
echo Next steps:
echo   1. Start API: deploy.bat (choose option 2)
echo   2. Start Dashboard: deploy.bat (choose option 3)
echo   3. Load extension in browser (see docs\DEPLOYMENT_GUIDE.md)
echo.
pause
goto menu

:start_api
echo.
echo [INFO] Starting API server...
echo [INFO] API will be available at: http://localhost:8000
echo [INFO] API docs will be available at: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
goto menu

:start_dashboard
echo.
echo [INFO] Starting Streamlit dashboard...
echo [INFO] Dashboard will be available at: http://localhost:8501
echo.
echo Press Ctrl+C to stop the dashboard
echo.
streamlit run dashboard\app.py
goto menu

:package_extension
echo.
echo [INFO] Packaging browser extension...
cd extension
if exist "..\contentguard-extension.zip" del "..\contentguard-extension.zip"
powershell -command "Compress-Archive -Path * -DestinationPath ..\contentguard-extension.zip -Force"
cd ..
if exist "contentguard-extension.zip" (
    echo [OK] Extension packaged: contentguard-extension.zip
) else (
    echo [ERROR] Failed to package extension
)
echo.
pause
goto menu

:full_setup
call :setup
echo.
echo Press any key to start API server...
pause >nul
goto start_api

:check_requirements
echo.
echo [INFO] Checking system requirements...
echo.

REM Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found
) else (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do echo [OK] Python %%i found
)

REM pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip not found
) else (
    for /f "tokens=2" %%i in ('pip --version 2^>^&1') do echo [OK] pip %%i found
)

REM Git
git --version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Git not found (optional)
) else (
    for /f "tokens=3" %%i in ('git --version 2^>^&1') do echo [OK] Git %%i found
)

REM Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Node.js not found (optional)
) else (
    for /f %%i in ('node --version 2^>^&1') do echo [OK] Node.js %%i found
)

REM Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Docker not found (optional)
) else (
    for /f "tokens=3" %%i in ('docker --version 2^>^&1') do echo [OK] Docker %%i found
)

echo.
echo [SUCCESS] System requirements check complete
echo.
pause
goto menu

:invalid_choice
echo [ERROR] Invalid choice. Please enter 1-7.
goto menu

:exit
echo [INFO] Goodbye!
exit /b 0
