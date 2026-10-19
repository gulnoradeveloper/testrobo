@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
echo ============================================================
echo  Microsoft Visual C++ Redistributable 2015-2022 x64 o'rnatish
echo  PyTorch ishlashi uchun kerak. Manba: Microsoft rasmiy sayti
echo ============================================================
set "VC=%TEMP%\vc_redist.x64.exe"
echo Yuklab olinmoqda: https://aka.ms/vs/17/release/vc_redist.x64.exe
powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol='Tls12'; Invoke-WebRequest -UseBasicParsing -Uri 'https://aka.ms/vs/17/release/vc_redist.x64.exe' -OutFile $env:TEMP'\vc_redist.x64.exe'"
if not exist "%VC%" goto fail
echo O'rnatilmoqda - Windows ruxsat so'rasa, "Ha" ni bosing...
"%VC%" /install /passive /norestart
echo.
echo Tayyor. Endi KOMPYUTERNI QAYTA ISHGA TUSHIRING, so'ng BOGIMTAHLIL.bat ni oching.
pause
exit /b 0

:fail
echo XATO: faylni yuklab bo'lmadi. Brauzerda oching va o'rnating:
echo https://aka.ms/vs/17/release/vc_redist.x64.exe
pause
exit /b 1
