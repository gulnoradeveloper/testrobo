@echo off
rem Faqat interfeysni o'zgartirayotgan dasturchilar uchun (Node.js kerak). Oddiy foydalanish: 2_ishga_tushirish.bat
chcp 65001 >nul
cd /d "%~dp0..\frontend"
if not exist node_modules call npm install
call npm run dev
pause
