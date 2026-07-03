@echo off
chcp 65001 >nul
title Desinstalar ComfyUI Social Media Suite
cd /d "%~dp0"

echo.
echo  ============================================================
echo   DESINSTALAR ComfyUI Social Media Suite
echo  ============================================================
echo.
echo  Esto eliminara:
echo    - ComfyUI (carpeta completa)
echo    - Entorno virtual Python (venv)
echo    - Modelos descargados
echo    - Workflows copiados a ComfyUI
echo.
echo  NO se eliminara:
echo    - Este repositorio (scripts, workflows originales, docs)
echo    - Python, Git u otros programas del sistema
echo.
set /p CONFIRM="Estas seguro? (s/N): "
if /i not "!CONFIRM!"=="s" (
    echo  Operacion cancelada.
    pause
    exit /b 0
)

echo.
echo  Eliminando ComfyUI...
if exist "ComfyUI" rmdir /S /Q "ComfyUI"

echo  Eliminando entorno virtual...
if exist "venv" rmdir /S /Q "venv"

echo.
echo  Desinstalacion completa.
echo  Para reinstalar: ejecuta install.bat
pause
