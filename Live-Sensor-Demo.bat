@echo off
title NetSentinel Live Sensor Demo
cd /d "%~dp0"

echo ===================================================
echo          NetSentinel Live Sensor Demo
echo ===================================================
echo Running live packet and OS counter sensor inspection...
echo Interface: Ethernet 3 (5 samples)
echo.

.\.venv\Scripts\python.exe -m sensor.cli counters --interface "Ethernet 3" --samples 5

echo.
echo ===================================================
echo Sensor run finished.
echo ===================================================
echo.
pause
