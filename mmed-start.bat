@echo off
chcp 65001 >nul
echo =============================
echo   M-MED API - Zapusk servera
echo =============================

cd C:\mmed-api

echo [1/3] Zapusk FastAPI servera...
start "M-MED API" cmd /k "cd C:\mmed-api && uvicorn main:app --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak >nul

echo [2/3] Zapusk Ngrok...
start "M-MED Ngrok" cmd /k "cd C:\mmed-api && ngrok.exe http 8000"

echo [3/3] Ozhidanie ngrok (15 sek)...
timeout /t 15 /nobreak >nul

echo [4/4] Obnovlenie sayta na Netlify...
python C:\mmed-api\auto-deploy.py

echo Vseservisy zapusheny!
