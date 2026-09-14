@echo off
setlocal enabledelayedexpansion

title NetSentinel Demo Launcher

echo ===================================================
echo           NetSentinel Demo Launcher
echo ===================================================
echo.

cd /d "%~dp0"

:: Check port 8001
set PORT_8001_IN_USE=0
netstat -ano | findstr /R /C:":8001 .*LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    set PORT_8001_IN_USE=1
)

:: Check port 3000
set PORT_3000_IN_USE=0
netstat -ano | findstr /R /C:":3000 .*LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    set PORT_3000_IN_USE=1
)

if %PORT_8001_IN_USE% equ 1 (
    echo [INFO] Port 8001 is already in use.
    echo Backend may already be running or another service is listening on 8001.
    echo Skipping backend spawn to prevent conflicts.
    echo.
) else (
    echo [1/3] Starting Django backend on 127.0.0.1:8001...
    start "NetSentinel Backend" powershell -NoExit -Command "$host.UI.RawUI.WindowTitle = 'NetSentinel Backend'; Set-Location -Path '%~dp0'; .\.venv-backend\Scripts\python.exe backend/manage.py runserver 127.0.0.1:8001"
    timeout /t 3 /nobreak >nul
)

if %PORT_3000_IN_USE% equ 1 (
    echo [INFO] Port 3000 is already in use.
    echo Frontend may already be running or another service is listening on 3000.
    echo Skipping frontend spawn to prevent conflicts.
    echo.
) else (
    echo [2/3] Starting Next.js frontend on http://127.0.0.1:3000...
    start "NetSentinel Frontend" powershell -NoExit -Command "$host.UI.RawUI.WindowTitle = 'NetSentinel Frontend'; Set-Location -Path '%~dp0frontend'; npm run dev -- -p 3000"
    timeout /t 5 /nobreak >nul
)

echo [3/3] Launching web browser at http://127.0.0.1:3000...
start http://127.0.0.1:3000

echo.
echo ===================================================
echo NetSentinel Demo has been started!
echo Frontend: http://127.0.0.1:3000
echo Backend:  http://127.0.0.1:8001
echo Keep the backend and frontend terminal windows open.
echo ===================================================
echo.
pause
