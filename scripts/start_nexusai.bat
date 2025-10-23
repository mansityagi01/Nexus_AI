@echo off
REM NexusAI Application Startup Script (Windows)
REM Coordinates MCP server and Flask server startup with health checks

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."

REM Default configuration
set "VALIDATE_ONLY=false"
set "SKIP_BUILD=false"

REM Parse command line arguments
:parse_args
if "%~1"=="" goto :start_app
if "%~1"=="--validate-only" (
    set "VALIDATE_ONLY=true"
    shift
    goto :parse_args
)
if "%~1"=="--skip-build" (
    set "SKIP_BUILD=true"
    shift
    goto :parse_args
)
shift
goto :parse_args

:start_app
echo Starting NexusAI application...

REM Change to project root
cd /d "%PROJECT_ROOT%"

REM Load environment variables if .env exists
if exist ".env" (
    echo Loading environment variables from .env...
    for /f "usebackq tokens=1,2 delims==" %%a in (".env") do (
        if not "%%a"=="" if not "%%b"=="" (
            set "%%a=%%b"
        )
    )
)

REM Set default values if not set
if not defined MCP_HOST set "MCP_HOST=127.0.0.1"
if not defined MCP_PORT set "MCP_PORT=8080"
if not defined FLASK_HOST set "FLASK_HOST=127.0.0.1"
if not defined FLASK_PORT set "FLASK_PORT=5000"
if not defined FLASK_DEBUG set "FLASK_DEBUG=false"

REM Validate environment
echo Validating environment...

REM Check required environment variables
if not defined GEMINI_API_KEY (
    echo Error: GEMINI_API_KEY environment variable is required
    echo Please set it in your .env file
    exit /b 1
)

if not defined SECRET_KEY (
    echo Error: SECRET_KEY environment variable is required
    echo Please set it in your .env file
    exit /b 1
)

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    exit /b 1
)

REM Check Python dependencies
python -c "import flask, flask_socketio, google.generativeai" >nul 2>&1
if errorlevel 1 (
    echo Error: Missing Python dependencies
    echo Please run: pip install -r requirements.txt
    exit /b 1
)

echo Environment validation passed

REM If validate-only flag is set, exit here
if "%VALIDATE_ONLY%"=="true" (
    echo Environment validation completed successfully
    exit /b 0
)

REM Build frontend if not skipped
if "%SKIP_BUILD%"=="false" (
    if exist "frontend\package.json" (
        echo Checking frontend build...
        if not exist "backend\web\static\index.html" (
            echo Building frontend...
            cd /d "%PROJECT_ROOT%\frontend"
            call npm install
            if errorlevel 1 (
                echo Warning: Failed to install frontend dependencies
            ) else (
                call npm run build
                if errorlevel 1 (
                    echo Warning: Frontend build failed
                )
            )
            cd /d "%PROJECT_ROOT%"
        ) else (
            echo Frontend already built
        )
    )
)

REM Create log directory
if not exist "logs" mkdir logs

REM Start MCP server in background
echo Starting MCP server on %MCP_HOST%:%MCP_PORT%...
start "MCP Server" /min python backend\tools\security_mcp_server.py --host %MCP_HOST% --port %MCP_PORT%

REM Wait for MCP server to be ready
echo Waiting for MCP server to be ready...
set "MCP_READY=false"
set "WAIT_COUNT=0"

:wait_mcp
if %WAIT_COUNT% geq 30 (
    echo Error: MCP server failed to start within 30 seconds
    taskkill /f /fi "WindowTitle eq MCP Server*" >nul 2>&1
    exit /b 1
)

REM Check if MCP port is listening
netstat -an | findstr ":%MCP_PORT%" | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
    set "MCP_READY=true"
    goto :mcp_ready
)

timeout /t 1 /nobreak >nul
set /a WAIT_COUNT+=1
goto :wait_mcp

:mcp_ready
echo MCP server is ready

REM Start Flask server
echo Starting Flask server on %FLASK_HOST%:%FLASK_PORT%...
echo Dashboard will be available at: http://%FLASK_HOST%:%FLASK_PORT%
echo.
echo Press Ctrl+C to stop all services
echo.

REM Set Flask environment variables
set "FLASK_HOST=%FLASK_HOST%"
set "FLASK_PORT=%FLASK_PORT%"
set "FLASK_DEBUG=%FLASK_DEBUG%"

REM Start Flask server (this will block)
python backend\web\main.py

REM Cleanup on exit
echo.
echo Shutting down services...
taskkill /f /fi "WindowTitle eq MCP Server*" >nul 2>&1
echo Services stopped

endlocal