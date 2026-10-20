@echo off
REM CommuniAI backend — Windows uchun bir martalik ishga tushirish.
REM Talab: Python 3.11+ (https://www.python.org/downloads/ — o'rnatishda "Add python.exe to PATH" ni belgilang)
cd /d "%~dp0backend"
if not exist .venv (
  echo Virtual muhit yaratilmoqda...
  python -m venv .venv || goto :error
)
call .venv\Scripts\activate.bat || goto :error
echo Kutubxonalar o'rnatilmoqda (birinchi marta bir necha daqiqa)...
python -m pip install --upgrade pip >nul
pip install -r requirements.txt || goto :error
if not exist .env copy ..\.env.example .env >nul
python run_local.py
goto :eof
:error
echo.
echo XATOLIK: yuqoridagi xabarni o'qing. Python o'rnatilganini tekshiring: python --version
pause
