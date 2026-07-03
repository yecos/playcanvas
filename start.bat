@echo off
chcp 65001 >nul
title ComfyUI Social Media Suite
cd /d "%~dp0"

REM ============================================================
REM  Lanzador de ComfyUI Social Media Suite (Windows)
REM ============================================================

if not exist "venv\Scripts\activate.bat" (
    echo  ERROR: No se encontro el entorno virtual.
    echo  Ejecuta install.bat primero.
    pause
    exit /b 1
)

if not exist "ComfyUI\main.py" (
    echo  ERROR: No se encontro ComfyUI.
    echo  Ejecuta install.bat primero.
    pause
    exit /b 1
)

REM ---- Leer argumentos de lanzamiento ----
set "LAUNCH_ARGS="
if exist "config\launch_args.txt" (
    for /f "usebackq tokens=*" %%a in ("config\launch_args.txt") do (
        set "line=%%a"
        if not "!line:~0,1!"=="#" set "LAUNCH_ARGS=!LAUNCH_ARGS! %%a"
    )
)

echo.
echo  ============================================================
echo   Iniciando ComfyUI Social Media Suite...
echo  ============================================================
echo   Argumentos: !LAUNCH_ARGS!
echo   URL: http://127.0.0.1:8188
echo  ============================================================
echo.

call venv\Scripts\activate.bat
cd ComfyUI

REM ---- Abrir navegador cuando ComfyUI responda (poll cada 2s, max 60s) ----
start "" /b cmd /c "powershell -Command \"for ($i=0; $i -lt 30; $i++) { try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8188/system_stats' -UseBasicParsing -TimeoutSec 2; if ($r.StatusCode -eq 200) { Start-Process 'http://127.0.0.1:8188'; break } } catch {}; Start-Sleep -Seconds 2 }\""

python main.py !LAUNCH_ARGS!

pause
