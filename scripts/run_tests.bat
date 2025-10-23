@echo off
REM Test runner batch script for Windows

echo Running NexusAI Test Suite...

REM Change to project root
cd /d "%~dp0\.."

REM Run tests with Python
python scripts\run_tests.py %*

if %ERRORLEVEL% NEQ 0 (
    echo Tests failed with exit code %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
) else (
    echo All tests passed!
)