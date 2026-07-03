@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
title ComfyUI Social Suite - Inicio Automatico
color 0B

REM ============================================================
REM  ComfyUI Social Suite - Arranque Automatico de TODOS los servicios
REM  Inicia:
REM    1. ComfyUI (generacion de imagenes/video)
REM    2. Queue Worker (cola con reintentos)
REM    3. Webhook Server (event-driven publishing)
REM    4. Telegram Bot (control remoto, opcional)
REM    5. Dashboard web (estado, opcional)
REM ============================================================

cd /d "%~dp0"

echo.
echo  ============================================================
echo   COMFYUI SOCIAL SUITE - ARRANQUE AUTOMATICO
echo  ============================================================
echo.
echo  Iniciando todos los servicios...
echo.

REM ---- Verificar que ComfyUI esta instalado ----
if not exist "ComfyUI\main.py" (
    echo  ERROR: ComfyUI no esta instalado.
    echo  Ejecuta install.bat primero.
    pause
    exit /b 1
)

if not exist "venv\Scripts\activate.bat" (
    echo  ERROR: Entorno virtual no existe.
    echo  Ejecuta install.bat primero.
    pause
    exit /b 1
)

REM ---- Crear carpeta de logs y PIDs ----
if not exist "logs" mkdir "logs"
if not exist "run" mkdir "run"

REM ---- Matar procesos previos si existen ----
echo  [0/5] Deteniendo servicios previos si existen...
call stop_all.bat >nul 2>&1
timeout /t 2 /nobreak >nul

REM ---- Activar venv ----
call venv\Scripts\activate.bat

REM ---- Leer launch_args (solo lineas que no empiezan con #) ----
set "LAUNCH_ARGS="
for /f "usebackq eol=# tokens=*" %%a in ("config\launch_args.txt") do (
    set "ARG=%%a"
    if not "!ARG!"=="" set "LAUNCH_ARGS=!LAUNCH_ARGS! !ARG!"
)

REM ---- 1. Iniciar ComfyUI ----
echo.
echo  [1/5] Iniciando ComfyUI en http://127.0.0.1:8188 ...
echo  Argumentos: !LAUNCH_ARGS!
start "ComfyUI-Suite" /min cmd /c "cd ComfyUI && python main.py !LAUNCH_ARGS! > ..\logs\comfyui.log 2>&1"
echo   Proceso iniciado. Log: logs\comfyui.log

REM ---- Esperar a que ComfyUI responda (max 120 seg) ----
echo  Esperando a que ComfyUI responda (max 120s)...
set /a WAIT=0
:wait_comfy
python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8188/system_stats', timeout=2)" >nul 2>&1
if errorlevel 1 (
    set /a WAIT+=2
    if !WAIT! geq 120 (
        echo  ERROR: ComfyUI no respondio en 120 segundos.
        echo.
        echo  === ULTIMAS 30 LINEAS DEL LOG ===
        if exist "logs\comfyui.log" (
            powershell -Command "Get-Content logs\comfyui.log -Tail 30" 2>nul
        ) else (
            echo  Log no existe. ComfyUI no llego a arrancar.
        )
        echo  ===================================
        echo.
        echo  Posibles causas:
        echo    1. --front-end-version bloqueado por firewall
        echo       Solucion: edita config\launch_args.txt y comenta la linea --front-end-version
        echo    2. Custom node con error
        echo       Solucion: revisa el log arriba
        echo    3. Modelo corrupto
        echo       Solucion: borra ComfyUI\models\checkpoints\*.safetensors corruptos
        echo.
        pause
        exit /b 1
    )
    timeout /t 2 /nobreak >nul
    goto wait_comfy
)
echo  OK: ComfyUI responde. Listo en !WAIT! segundos.

REM ---- Abrir navegador ----
start http://127.0.0.1:8188

REM ---- 2. Iniciar Queue Worker ----
echo.
echo  [2/5] Iniciando Queue Worker (cola con reintentos)...
start "QueueWorker-Suite" /min cmd /c "python scripts\queue_manager.py worker --poll-interval 10 > logs\queue_worker.log 2>&1"
echo   Worker iniciado. Log: logs\queue_worker.log

REM ---- 3. Iniciar Webhook Server ----
echo.
echo  [3/5] Iniciando Webhook Server en http://127.0.0.1:8189 ...
start "WebhookServer-Suite" /min cmd /c "python scripts\webhook_server.py --port 8189 > logs\webhook_server.log 2>&1"
echo   Webhook server iniciado. Log: logs\webhook_server.log

REM ---- 4. Iniciar Telegram Bot (opcional, si hay token) ----
set "TG_TOKEN="
if exist ".env" (
    for /f "tokens=1,2 delims==" %%a in (.env) do (
        if "%%a"=="TELEGRAM_BOT_TOKEN" set "TG_TOKEN=%%b"
    )
)
if not "!TG_TOKEN!"=="" (
    echo.
    echo  [4/5] Iniciando Telegram Bot...
    start "TelegramBot-Suite" /min cmd /c "python scripts\bot_telegram.py > logs\telegram_bot.log 2>&1"
    echo   Bot iniciado. Log: logs\telegram_bot.log
) else (
    echo.
    echo  [4/5] Telegram Bot: SKIPPED (TELEGRAM_BOT_TOKEN no configurado)
)

REM ---- 5. Iniciar Dashboard (opcional, si flask instalado) ----
python -c "import flask" >nul 2>&1
if not errorlevel 1 (
    echo.
    echo  [5/5] Iniciando Dashboard en http://127.0.0.1:8080 ...
    start "Dashboard-Suite" /min cmd /c "python scripts\dashboard.py > logs\dashboard.log 2>&1"
    echo   Dashboard iniciado. Log: logs\dashboard.log
    timeout /t 3 /nobreak >nul
    start http://127.0.0.1:8080
) else (
    echo.
    echo  [5/5] Dashboard: SKIPPED (flask no instalado)
)

REM ---- Final ----
echo.
echo  ============================================================
echo   TODOS LOS SERVICIOS INICIADOS
echo  ============================================================
echo.
echo  ComfyUI:         http://127.0.0.1:8188
echo  Webhook Server:  http://127.0.0.1:8189
echo  Dashboard:       http://127.0.0.1:8080
echo.
echo  Logs en:         logs\
echo.
echo  Para detener todo:   stop_all.bat
echo  Para estado:         python scripts\dashboard.py
echo.
echo  Esta ventana puede cerrarse. Los servicios siguen corriendo.
echo.
pause
exit /b 0
