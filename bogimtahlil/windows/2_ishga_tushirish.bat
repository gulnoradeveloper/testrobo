@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0.."
if not exist .venv\Scripts\activate.bat (
    echo Avval windows\1_ornatish.bat ni ishga tushiring.
    pause
    exit /b 1
)
echo ============================================================
echo  Bo'g'imTahlil ishga tushmoqda...
echo  Brauzerda oching:  http://127.0.0.1:8000
echo  To'xtatish: shu oynada Ctrl+C
echo ============================================================
start "" cmd /c "timeout /t 8 >nul && start http://127.0.0.1:8000"
call .venv\Scripts\activate.bat
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
echo.
echo Server to'xtadi. Yuqoridagi xabarni o'qing (masalan, 8000-port band bo'lishi mumkin).
pause
