@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0.."
if not exist .venv\Scripts\activate.bat (
    echo Avval windows\1_ornatish.bat ni ishga tushiring.
    pause
    exit /b 1
)
echo Backend: http://127.0.0.1:8000/api/docs
start "Bo'g'imTahlil backend" cmd /k "set PYTHONUTF8=1 && call .venv\Scripts\activate.bat && cd backend && uvicorn app.main:app --port 8000"
echo Frontend: http://localhost:5173
start "Bo'g'imTahlil frontend" cmd /k "cd frontend && npm run dev"
timeout /t 6 >nul
start http://localhost:5173
