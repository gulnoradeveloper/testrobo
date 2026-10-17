@echo off
chcp 65001 >nul
setlocal
set PYTHONUTF8=1
cd /d "%~dp0"
if not exist logs mkdir logs
title Bo'g'imTahlil 1.0

rem --- Python topish: avval "py" ishga tushirgich, keyin "python" ---
set "PY="
py -3 --version >nul 2>nul && set "PY=py -3"
if not defined PY python --version >nul 2>nul && set "PY=python"
if not defined PY goto nopython

if not exist ".venv\Scripts\python.exe" (
    echo [1/3] Virtual muhit yaratilmoqda...
    %PY% -m venv .venv
    if errorlevel 1 goto failvenv
)

if not exist ".venv\installed-v2.ok" (
    echo [2/3] Kutubxonalar o'rnatilmoqda - birinchi marta 1-5 daqiqa, internet kerak...
    ".venv\Scripts\python.exe" -m pip install --upgrade pip > logs\install.log 2>&1
    ".venv\Scripts\python.exe" -m pip install -r backend\requirements.txt >> logs\install.log 2>&1
    if errorlevel 1 goto failinstall
    echo ok> ".venv\installed-v2.ok"
)

echo [3/3] Server ishga tushmoqda...
".venv\Scripts\python.exe" start.py
echo.
echo Server to'xtadi. Xato bo'lsa, yuqoridagi xabarni yoki logs\server.log faylini yuboring.
pause
exit /b 0

:nopython
echo XATO: Python topilmadi.
echo https://www.python.org/downloads/ dan Python 3.11 yoki 3.12 ni o'rnating.
echo O'rnatishda "Add python.exe to PATH" belgisini qo'ying, so'ng shu faylni qayta ishga tushiring.
pause
exit /b 1

:failvenv
echo XATO: virtual muhit yaratilmadi. .venv papkasini o'chirib, qayta urinib ko'ring.
pause
exit /b 1

:failinstall
echo XATO: kutubxonalarni o'rnatib bo'lmadi. Internet aloqasini tekshiring.
echo Oxirgi xabarlar - to'liq matn logs\install.log faylida:
powershell -NoProfile -Command "Get-Content -Tail 25 logs\install.log"
pause
exit /b 1
