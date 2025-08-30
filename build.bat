@echo off
echo CryptoTradeSimulator Build Commands
echo.
echo Available commands:
echo   build install     - Install Python dependencies
echo   build frontend    - Start the frontend development server
echo   build backend     - Start the backend PyQt5 application
echo   build clean       - Clean up generated files
echo.
if "%1"=="install" (
    echo Installing Python dependencies...
    cd src
    pip install -r requirements.txt
) else if "%1"=="frontend" (
    echo Starting frontend server...
    cd frontend
    npm start
) else if "%1"=="backend" (
    echo Starting backend application...
    cd src
    python main.py
) else if "%1"=="clean" (
    echo Cleaning up...
    del /s *.pyc
    for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
    echo Clean complete
) else if "%1"=="" (
    echo Please specify a command: install, frontend, backend, or clean
) else (
    echo Unknown command: %1
)
