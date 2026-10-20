@echo off
setlocal
REM CommuniAI backend - Windows uchun ishga tushirish.
REM Talab: Python 3.11+ (https://www.python.org/downloads/ - o'rnatishda "Add python.exe to PATH" ni belgilang)
cd /d "%~dp0backend"

set "PY=python"
where python >nul 2>nul
if errorlevel 1 (
  where py >nul 2>nul
  if errorlevel 1 goto :nopython
  set "PY=py -3"
)

if not exist .venv\Scripts\python.exe (
  echo Virtual muhit yaratilmoqda...
  %PY% -m venv .venv
  if errorlevel 1 goto :error
)
call .venv\Scripts\activate.bat
if errorlevel 1 goto :error

echo Kutubxonalar o'rnatilmoqda (birinchi marta 2-5 daqiqa, internet kerak)...
python -m pip install --upgrade pip >nul
python -m pip install -r requirements.txt
if errorlevel 1 goto :error

if not exist .env copy ..\.env.example .env >nul
python run_local.py
pause
goto :eof

:nopython
echo.
echo XATOLIK: Python topilmadi. https://www.python.org/downloads/ dan o'rnating
echo va o'rnatishda "Add python.exe to PATH" belgisini qo'ying.
pause
goto :eof

:error
echo.
echo XATOLIK yuz berdi. Yuqoridagi xabarni o'qing.
pause
