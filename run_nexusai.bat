@echo off
REM NexusAI Application Runner (Windows)
REM Main entry point for starting the complete NexusAI application

setlocal

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8 or later
    pause
    exit /b 1
)

REM Run the Python startup coordinator
python "%PROJECT_ROOT%\scripts\start_nexusai.py" %*

endlocal