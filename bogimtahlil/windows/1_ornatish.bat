@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0.."
echo === Bo'g'imTahlil: o'rnatish ===

where py >nul 2>nul && (set PY=py -3) || (set PY=python)
if not exist .venv (
    echo Virtual muhit yaratilmoqda...
    %PY% -m venv .venv || goto :error
)
call .venv\Scripts\activate.bat || goto :error
python -m pip install --upgrade pip || goto :error
echo Python kutubxonalari o'rnatilmoqda (PyTorch CPU ~1 GB, bir necha daqiqa)...
pip install -r backend\requirements-dev.txt -r ai\requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu || goto :error

where npm >nul 2>nul && (
    echo Frontend kutubxonalari o'rnatilmoqda...
    pushd frontend && call npm install && popd
) || echo OGOHLANTIRISH: Node.js topilmadi - https://nodejs.org dan o'rnating (20 yoki yangiroq).

python ai\scripts\check_env.py
echo.
echo Tayyor. Dasturni ishga tushirish: windows\2_ishga_tushirish.bat
pause
exit /b 0

:error
echo XATO yuz berdi. Yuqoridagi xabarni o'qing.
pause
exit /b 1
