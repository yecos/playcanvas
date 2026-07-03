@echo off
REM ============================================================
REM  Instala ComfyUI Social Suite como Tarea Programada Windows
REM  Para auto-start en boot del sistema
REM ============================================================
chcp 65001 >nul
title Instalar ComfyUI Social Suite como Tarea Programada
cd /d "%~dp0\.."

echo.
echo  ============================================================
echo   INSTALACION DE TAREA PROGRAMADA WINDOWS
echo  ============================================================
echo.

REM Necesita permisos de admin
net session >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Necesitas permisos de administrador.
    echo  Click derecho en este .bat -> Ejecutar como administrador.
    pause
    exit /b 1
)

set "TASK_NAME=ComfyUI_Social_Suite"
set "PROJECT_DIR=%CD%"
set "START_BAT=%PROJECT_DIR%\start_all.bat"

echo  Proyecto:   %PROJECT_DIR%
echo  Tarea:      %TASK_NAME%
echo.

REM Crear tarea programada que se ejecuta al iniciar el sistema
schtasks /create /tn "%TASK_NAME%" /tr "%START_BAT%" /sc onstart /ru SYSTEM /rl HIGHEST /f
if errorlevel 1 (
    echo  ERROR: No se pudo crear la tarea programada.
    pause
    exit /b 1
)

echo.
echo  Tarea creada correctamente.
echo.
set /p RUN_NOW="Ejecutar la tarea ahora para probar? (S/n): "
if /i not "!RUN_NOW!"=="n" (
    schtasks /run /tn "%TASK_NAME%"
    timeout /t 5 /nobreak >nul
    schtasks /query /tn "%TASK_NAME%" /v /fo list | findstr /i "status"
)

echo.
echo  ============================================================
echo   TAREA PROGRAMADA INSTALADA
echo  ============================================================
echo.
echo  Comandos utiles (en cmd como admin):
echo    schtasks /run /tn "%TASK_NAME%"           REM iniciar ahora
echo    schtasks /end /tn "%TASK_NAME%"           REM detener
echo    schtasks /query /tn "%TASK_NAME%" /v      REM ver estado
echo    schtasks /delete /tn "%TASK_NAME%" /f     REM eliminar tarea
echo.
pause
exit /b 0
