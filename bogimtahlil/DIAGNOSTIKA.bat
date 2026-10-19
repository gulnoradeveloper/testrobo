@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" diagnostika.py
) else (
    py -3 diagnostika.py 2>nul || python diagnostika.py
)
if exist logs\diagnostika.txt start notepad logs\diagnostika.txt
pause
