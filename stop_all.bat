@echo off
chcp 65001 >nul
title Deteniendo ComfyUI Social Suite
cd /d "%~dp0"

echo.
echo  ============================================================
echo   DETENIENDO TODOS LOS SERVICIOS
echo  ============================================================
echo.

REM ---- Matar procesos por titulo de ventana ----
echo  Cerrando ComfyUI...
taskkill /fi "WINDOWTITLE eq ComfyUI-Suite*" /f >nul 2>&1

echo  Cerrando Queue Worker...
taskkill /fi "WINDOWTITLE eq QueueWorker-Suite*" /f >nul 2>&1

echo  Cerrando Webhook Server...
taskkill /fi "WINDOWTITLE eq WebhookServer-Suite*" /f >nul 2>&1

echo  Cerrando Telegram Bot...
taskkill /fi "WINDOWTITLE eq TelegramBot-Suite*" /f >nul 2>&1

echo  Cerrando Dashboard...
taskkill /fi "WINDOWTITLE eq Dashboard-Suite*" /f >nul 2>&1

REM ---- Backup: matar por puerto si siguen vivos ----
echo.
echo  Verificando puertos (8188, 8189, 8080)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8188 " ^| findstr "LISTENING"') do (
    taskkill /pid %%a /f >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8189 " ^| findstr "LISTENING"') do (
    taskkill /pid %%a /f >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8080 " ^| findstr "LISTENING"') do (
    taskkill /pid %%a /f >nul 2>&1
)

echo.
echo  Todos los servicios detenidos.
echo.
pause
exit /b 0
