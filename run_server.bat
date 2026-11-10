@echo off
echo ===================================================
echo   Cat Care - Restarting API Server on Port 8080
echo ===================================================
echo.

echo 1. Stopping any old uvicorn processes...
taskkill /F /IM uvicorn.exe /T >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq uvicorn*" >nul 2>&1
echo Done.
echo.

echo 2. Starting new API Server on port 8080...
echo (Please keep this window open)
echo.
uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload
