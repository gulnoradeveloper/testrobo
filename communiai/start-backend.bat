@echo off
setlocal
REM CommuniAI backend - Windows uchun ishga tushirish.
REM Talab: Python 3.12, 3.13, 3.14 yoki 3.15 (https://www.python.org/downloads/)
cd /d "%~dp0backend"

REM --- Python ni topish (eng mos versiya birinchi) ---
set "PY="
if defined PY_FORCE set "PY=py -%PY_FORCE%"
for %%V in (3.13 3.12 3.14 3.15) do (
  if not defined PY (
    py -%%V -c "import sys" >nul 2>nul && set "PY=py -%%V"
  )
)
if not defined PY (
  python -c "import sys; sys.exit(0 if sys.version_info[:2] >= (3, 12) else 1)" >nul 2>nul && set "PY=python"
)
if not defined PY goto :nopython
echo Python: & %PY% --version

REM --- Virtual muhit (avvalgi muvaffaqiyatsiz urinishdan qolgan bo'lsa qayta yaratiladi) ---
if exist .venv\Scripts\python.exe (
  .venv\Scripts\python.exe -c "import fastapi, pydantic_core, uvicorn, sqlalchemy" >nul 2>nul
  if errorlevel 1 (
    echo Eski/buzilgan virtual muhit o'chirilmoqda...
    rmdir /s /q .venv
  )
)
if not exist .venv\Scripts\python.exe (
  echo Virtual muhit yaratilmoqda...
  %PY% -m venv .venv
  if errorlevel 1 goto :error
)

echo Kutubxonalar o'rnatilmoqda (birinchi marta 2-5 daqiqa, internet kerak)...
.venv\Scripts\python.exe -m pip install --upgrade pip >nul
REM Faqat tayyor paketlar (wheel): kompilyator (Rust/C++) talab qilinmaydi.
.venv\Scripts\python.exe -m pip install --only-binary=:all: -r requirements.txt
if errorlevel 1 goto :error

if not exist .env copy ..\.env.example .env >nul
.venv\Scripts\python.exe run_local.py
pause
goto :eof

:nopython
echo.
echo XATOLIK: mos Python topilmadi (3.12 yoki yangiroq kerak).
echo https://www.python.org/downloads/ dan Python 3.13 ni o'rnating va
echo o'rnatishda "Add python.exe to PATH" belgisini qo'ying.
pause
goto :eof

:error
echo.
echo XATOLIK yuz berdi. Yuqoridagi xabarni o'qing yoki ekran rasmini yuboring.
pause
