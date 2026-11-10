@echo off
chcp 65001 >nul 2>&1
echo.
echo ============================================================
echo   Cat Care -- Startup Script
echo ============================================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

:: Activate .venv if exists
if exist ".venv\Scripts\activate.bat" (
    echo [OK] Activating virtual environment...
    call ".venv\Scripts\activate.bat"
) else (
    echo [WARN] No .venv found -- using global Python
)

:: Install dependencies
echo.
echo [INFO] Installing dependencies...
pip install -r requirements.txt -q
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

:: Create .env if not exists
if not exist ".env" (
    echo [WARN] .env not found -- copying from .env.example
    copy ".env.example" ".env" >nul
    echo [INFO] Please edit DATABASE_URL in .env before using real database
)

echo.
echo ============================================================
echo   Select what to run:
echo   [1] Streamlit Dashboard  (http://localhost:8501)
echo   [2] FastAPI Backend      (http://localhost:8000)
echo   [3] Setup Database       (first time only)
echo   [4] Alembic Migration
echo   [5] Exit
echo ============================================================
echo.

set /p choice="Enter number (1-5): "

if "%choice%"=="1" goto :streamlit
if "%choice%"=="2" goto :fastapi
if "%choice%"=="3" goto :setup_db
if "%choice%"=="4" goto :migrate
if "%choice%"=="5" goto :end
echo [WARN] Invalid choice
goto :end

:streamlit
echo.
echo [INFO] Starting Streamlit Dashboard...
echo [INFO] URL: http://localhost:8501
echo.
streamlit run dashboard/dashboard.py
goto :end

:fastapi
echo.
echo [INFO] Starting FastAPI Backend...
echo [INFO] URL:  http://localhost:8000
echo [INFO] Docs: http://localhost:8000/docs
echo.
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
goto :end

:setup_db
echo.
set /p pg_pass="Enter postgres superuser password: "
python setup_db.py %pg_pass%
goto :end

:migrate
echo.
echo [INFO] Running Alembic migrations...
if exist ".venv\Scripts\alembic.exe" (
    ".venv\Scripts\alembic.exe" upgrade head
) else (
    alembic upgrade head
)
echo [OK] Migration complete
pause
goto :end

:end
echo.
echo Goodbye!
pause
