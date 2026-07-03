@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
title ComfyUI Social Media Suite - Instalador
color 0B

REM ============================================================
REM  ComfyUI Social Media Suite - Instalador Windows
REM  Optimizado para NVIDIA RTX 3060 12GB
REM ============================================================

cd /d "%~dp0"

echo.
echo  ============================================================
echo   COMFYUI SOCIAL MEDIA SUITE - INSTALADOR PARA WINDOWS
echo   Optimizado para NVIDIA RTX 3060 12GB
echo  ============================================================
echo.
echo  Este instalador configurara todo lo necesario para usar
echo  ComfyUI como herramienta profesional de creacion de
echo  contenido para redes sociales.
echo.
echo  Proceso:
echo    1. Verificacion del sistema
echo    2. Clonado de ComfyUI
echo    3. Entorno virtual Python
echo    4. Instalacion de PyTorch + CUDA
echo    5. ComfyUI-Manager
echo    6. Custom nodes esenciales
echo    7. Descarga de modelos (^~20GB^)
echo    8. Workflows preconfigurados
echo.
echo  Tiempo estimado: 30-90 minutos segun conexion.
echo.
pause

REM ---- 0. Verificar Python ----
echo.
echo  [0/8] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python no esta instalado o no esta en el PATH.
    echo  Descargalo desde: https://www.python.org/downloads/
    echo  Asegurate de marcar "Add Python to PATH" al instalar.
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo  OK: Python !PYVER! detectado.

REM ---- Verificar Git ----
echo  Verificando Git...
git --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Git no esta instalado.
    echo  Descargalo desde: https://git-scm.com/download/win
    pause
    exit /b 1
)
echo  OK: Git detectado.

REM ---- Verificar NVIDIA ----
echo  Verificando GPU NVIDIA...
nvidia-smi >nul 2>&1
if errorlevel 1 (
    echo  ADVERTENCIA: No se detecto GPU NVIDIA o drivers incompletos.
    echo  ComfyUI funcionara en modo CPU (MUY lento).
    set /p CONFIRM="Continuar de todos modos? (s/N): "
    if /i not "!CONFIRM!"=="s" exit /b 1
) else (
    echo  OK: GPU NVIDIA detectada.
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
)

REM ---- 1. ComfyUI Check System (Python script) ----
echo.
echo  [1/8] Verificacion detallada del sistema...
python scripts\check_system.py
if errorlevel 1 (
    echo.
    echo  ERROR: Verificacion del sistema fallida.
    pause
    exit /b 1
)

REM ---- 2. Clonar ComfyUI ----
echo.
echo  [2/8] Clonando ComfyUI...
if exist "ComfyUI" (
    echo  La carpeta ComfyUI ya existe. Omitiendo clonado.
    echo  Si quieres reinstalar, borra la carpeta ComfyUI primero.
) else (
    git clone https://github.com/comfyanonymous/ComfyUI.git
    if errorlevel 1 (
        echo  ERROR: No se pudo clonar ComfyUI.
        pause
        exit /b 1
    )
)
echo  OK: ComfyUI listo.

REM ---- 3. Entorno virtual ----
echo.
echo  [3/8] Creando entorno virtual Python...
if exist "venv" (
    echo  Entorno virtual ya existe. Omitiendo.
) else (
    python -m venv venv
    if errorlevel 1 (
        echo  ERROR: No se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
)
call venv\Scripts\activate.bat
python -m pip install --upgrade pip wheel setuptools
echo  OK: Entorno virtual activado.

REM ---- 4. PyTorch + CUDA ----
echo.
echo  [4/8] Instalando PyTorch con soporte CUDA 12.1...
echo  Esto puede tardar varios minutos...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
if errorlevel 1 (
    echo  ERROR: Fallo la instalacion de PyTorch.
    echo  Intentando version CPU...
    pip install torch torchvision torchaudio
)
echo  OK: PyTorch instalado.

REM ---- ComfyUI requirements ----
echo.
echo  Instalando dependencias de ComfyUI...
pip install -r ComfyUI\requirements.txt
pip install -r requirements.txt
echo  OK: Dependencias base instaladas.

REM ---- Dependencias del orquestador de publicacion ----
echo.
echo  Instalando dependencias del orquestador (auto_publish)...
pip install -r requirements_extended.txt
if errorlevel 1 (
    echo  ADVERTENCIA: Algunas dependencias extendidas fallaron.
    echo  El orquestador auto_publish.py puede no funcionar completo.
    echo  Puedes instalarlas mas tarde: pip install -r requirements_extended.txt
) else (
    echo  OK: Dependencias del orquestador instaladas.
)

REM ---- 5. ComfyUI-Manager ----
echo.
echo  [5/8] Instalando ComfyUI-Manager...
if exist "ComfyUI\custom_nodes\ComfyUI-Manager" (
    echo  ComfyUI-Manager ya existe. Omitiendo.
) else (
    git clone https://github.com/comfy-org/ComfyUI-Manager.git ComfyUI\custom_nodes\ComfyUI-Manager
    if errorlevel 1 (
        echo  ADVERTENCIA: No se pudo clonar ComfyUI-Manager.
    )
)
echo  OK: ComfyUI-Manager listo.

REM ---- 6. Custom nodes ----
echo.
echo  [6/8] Instalando custom nodes esenciales...
python scripts\install_custom_nodes.py
echo  OK: Custom nodes instalados.

REM ---- 7. Descarga de modelos ----
echo.
echo  [7/8] Descargando modelos (~20GB)...
echo  Este paso es el mas largo. Se mostrara progreso.
echo  Si falla, puedes reanudar ejecutando:
echo    python scripts\download_models.py --retry
echo.
set /p DL="Descargar modelos ahora? (S/n): "
if /i not "!DL!"=="n" (
    python scripts\download_models.py
)

REM ---- 8. Workflows ----
echo.
echo  [8/8] Copiando workflows preconfigurados...
if not exist "ComfyUI\user\default\workflows" mkdir "ComfyUI\user\default\workflows"
xcopy /Y /E workflows\*.json "ComfyUI\user\default\workflows\" >nul
echo  OK: Workflows copiados a ComfyUI\user\default\workflows\

REM ---- Final ----
echo.
echo  ============================================================
echo   INSTALACION COMPLETA
echo  ============================================================
echo.
echo  Para iniciar ComfyUI:
echo    1. Haz doble clic en start.bat
echo    2. Se abrira el navegador en http://127.0.0.1:8188
echo.
echo  Para actualizar:
echo    Doble clic en update.bat
echo.
echo  Para desinstalar:
echo    Doble clic en uninstall.bat
echo.
echo  Documentacion en la carpeta docs\
echo.
pause
exit /b 0
