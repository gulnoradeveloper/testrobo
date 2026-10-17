@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
if not exist logs mkdir logs
if not exist ".venv\Scripts\python.exe" (
    echo Avval BOGIMTAHLIL.bat ni bir marta ishga tushiring.
    pause
    exit /b 1
)
echo Sun'iy intellekt kutubxonalari o'rnatilmoqda: PyTorch CPU, ~250 MB, internet kerak...
".venv\Scripts\python.exe" -m pip install -r backend\requirements-ai.txt --extra-index-url https://download.pytorch.org/whl/cpu > logs\ai_install.log 2>&1
if errorlevel 1 goto fail
echo.
echo Tayyor. Endi BOGIMTAHLIL.bat ni ishga tushiring.
if not exist artifacts\model.pt echo DIQQAT: artifacts\model.pt hali yo'q - Colab natijasini bogimtahlil papkasiga nusxalang.
pause
exit /b 0

:fail
echo XATO: o'rnatib bo'lmadi. Oxirgi xabarlar - to'liq matn logs\ai_install.log da:
powershell -NoProfile -Command "Get-Content -Tail 25 logs\ai_install.log"
echo Agar Python 3.14 uchun PyTorch topilmasa, Python 3.12 ni o'rnatib, .venv papkasini o'chirib, qayta urinib ko'ring.
pause
exit /b 1
