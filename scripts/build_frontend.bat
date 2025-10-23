@echo off
REM Frontend build script for NexusAI (Windows)
REM Handles Svelte compilation to Flask static directory

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
set "FRONTEND_DIR=%PROJECT_ROOT%\frontend"
set "STATIC_DIR=%PROJECT_ROOT%\backend\web\static"

REM Default mode is production
set "BUILD_MODE=production"
set "CLEAN_BUILD=false"
set "SKIP_INSTALL=false"

REM Parse command line arguments
:parse_args
if "%~1"=="" goto :start_build
if "%~1"=="--mode" (
    set "BUILD_MODE=%~2"
    shift
    shift
    goto :parse_args
)
if "%~1"=="--clean" (
    set "CLEAN_BUILD=true"
    shift
    goto :parse_args
)
if "%~1"=="--skip-install" (
    set "SKIP_INSTALL=true"
    shift
    goto :parse_args
)
shift
goto :parse_args

:start_build
echo Starting frontend build process...

REM Change to project root
cd /d "%PROJECT_ROOT%"

REM Check and install dependencies
if "%SKIP_INSTALL%"=="false" (
    if not exist "%FRONTEND_DIR%\node_modules" (
        echo Installing frontend dependencies...
        cd /d "%FRONTEND_DIR%"
        call npm install
        if errorlevel 1 (
            echo Error: Failed to install dependencies
            exit /b 1
        )
        cd /d "%PROJECT_ROOT%"
    ) else (
        echo Frontend dependencies already installed
    )
)

REM Clean static directory if requested
if "%CLEAN_BUILD%"=="true" (
    echo Cleaning static directory...
    if exist "%STATIC_DIR%" (
        rmdir /s /q "%STATIC_DIR%"
    )
    mkdir "%STATIC_DIR%" 2>nul
)

REM Build frontend
echo Building frontend in %BUILD_MODE% mode...
cd /d "%FRONTEND_DIR%"

if "%BUILD_MODE%"=="development" (
    call npm run build:dev
) else (
    call npm run build:prod
)

if errorlevel 1 (
    echo Error: Frontend build failed
    exit /b 1
)

echo Frontend build completed successfully!

REM Verify build output
if not exist "%STATIC_DIR%\index.html" (
    echo Error: index.html not found in static directory
    exit /b 1
)

echo Build verification passed
echo Frontend build process completed successfully!

endlocal