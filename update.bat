@echo off
chcp 65001 >nul
title Actualizar ComfyUI Social Media Suite
cd /d "%~dp0"

echo.
echo  ============================================================
echo   Actualizando ComfyUI Social Media Suite
echo  ============================================================
echo.

if not exist "venv\Scripts\activate.bat" (
    echo  ERROR: Ejecuta install.bat primero.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo  [1/4] Actualizando ComfyUI...
cd ComfyUI
git pull
cd ..

echo.
echo  [2/4] Actualizando ComfyUI-Manager...
cd ComfyUI\custom_nodes\ComfyUI-Manager
git pull
cd ..\..\..

echo.
echo  [3/4] Actualizando dependencias...
pip install -r ComfyUI\requirements.txt --upgrade
pip install -r requirements.txt --upgrade

echo.
echo  [4/4] Actualizando custom nodes...
python scripts\install_custom_nodes.py --update

echo.
echo  Actualizacion completa.
pause
