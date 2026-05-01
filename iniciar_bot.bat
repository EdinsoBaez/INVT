@echo off
title Inventario Bot - WhatsApp
set PATH=C:\Program Files\nodejs;C:\Program Files\Git\cmd;%PATH%

echo.
echo ============================================
echo   Inventario Pro - Bot de WhatsApp
echo ============================================
echo.
echo [1/2] Iniciando API de inventario (puerto 5000)...
start "API Inventario" /min C:\Users\baeze\AppData\Local\Programs\Python\Python312\python.exe "%~dp0api.py"

timeout /t 2 /nobreak >nul

echo [2/2] Iniciando bot de WhatsApp...
echo.
echo Escanea el codigo QR con tu telefono:
echo WhatsApp ^> Dispositivos vinculados ^> Vincular dispositivo
echo.
cd "%~dp0bot"
"C:\Program Files\nodejs\node.exe" bot.js
pause
