@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0.."
call .venv\Scripts\activate.bat || (echo Avval windows\1_ornatish.bat ni ishga tushiring & pause & exit /b 1)
python -m pytest
pushd frontend && call npm test && popd
pause
