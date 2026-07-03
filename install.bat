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
REM Modo automatico: si se pasa --yes, no preguntar
set "AUTO=YES"
if /i "%1"=="--yes" set "AUTO=YES"
if /i "%1"=="--force" set "AUTO=YES"
if /i "%1"=="--force" set "FORCE=YES"
if /i not "%1"=="--yes" (
    if /i not "%1"=="--force" (
        pause
    )
)

REM ---- 0. Verificar Python ----
echo.
echo  [0/8] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python no esta instalado o no esta en el PATH.
    echo  Ejecuta bootstrap.bat primero para instalar todos los prerrequisitos.
    echo  Descargalo y ejecuta:
    echo    bootstrap.bat
    pause
    exit /b 1
)

REM ---- Ejecutar check_prerequisites.py (a menos que --force) ----
if /i "!FORCE!"=="YES" (
    echo  SKIP: check_prerequisites omitido por --force
    goto skip_prereq_check
)
echo  Verificando prerrequisitos del sistema...
python scripts\check_prerequisites.py
REM Exit code 0 = OK o solo warnings (puede continuar)
REM Exit code 1 = fallos criticos (no puede continuar)
if errorlevel 1 (
    echo.
    echo  ERROR: Hay fallos criticos en los prerrequisitos.
    echo  Ejecuta bootstrap.bat para intentar auto-instalarlos.
    echo.
    echo  Si ya ejecutaste bootstrap y persiste, puedes forzar la instalacion con:
    echo    install.bat --force
    echo.
    pause
    exit /b 1
)
echo  OK: Prerrequisitos verificados ^(puede haber warnings, no criticos^).
:skip_prereq_check
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
if errorlevel 1 goto nvidia_not_found

REM NVIDIA presente - mostrar info
echo  OK: GPU NVIDIA detectada.
nvidia-smi --query-gpu^=name,memory.total --format^=csv,noheader 2>nul
goto nvidia_done

:nvidia_not_found
echo  ADVERTENCIA: No se detecto GPU NVIDIA o drivers incompletos.
echo  ComfyUI funcionara en modo CPU ^(MUY lento^).
if /i "!FORCE!"=="YES" (
    echo  Continuando por modo --force...
    goto nvidia_done
)
set "CONFIRM=N"
set /p "CONFIRM=Continuar de todos modos? (s/N): "
if /i not "!CONFIRM!"=="s" exit /b 1

:nvidia_done

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
    echo  ADVERTENCIA: Fallo instalacion CUDA, intentando version CPU...
    pip install torch torchvision torchaudio
)

REM Verificar que CUDA realmente funciona
echo  Verificando CUDA...
python -c "import torch; assert torch.cuda.is_available(), 'CUDA NO disponible. Reinstala driver NVIDIA.'; print(f'CUDA OK: {torch.cuda.get_device_name(0)}')"
if errorlevel 1 (
    echo  ADVERTENCIA: CUDA no disponible. ComfyUI funcionara en modo CPU (muy lento).
    echo  Solucion: actualiza driver NVIDIA desde https://www.nvidia.com/Download/index.aspx
    echo  Continuando de todos modos en modo CPU...
) else (
    echo  OK: CUDA verificado.
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
REM CivitAI token: leer de variable de entorno si existe, si no, saltar
if defined CIVITAI_TOKEN (
    echo  CIVITAI_TOKEN detectado en entorno.
) else (
    echo  NOTA: Juggernaut XL requiere token CivitAI (gratis).
    echo  Si falla la descarga, registrate en https://civitai.com,
    echo  crea API key y ejecuta: set CIVITAI_TOKEN=tu_token ^&^& python scripts\download_models.py --retry
)
REM Descarga automatica (sin prompt)
python scripts\download_models.py

REM ---- Copiar extra_model_paths.yaml a ComfyUI ----
if exist "config\extra_model_paths.yaml" (
    if not exist "ComfyUI\extra_model_paths.yaml" (
        copy /Y config\extra_model_paths.yaml ComfyUI\extra_model_paths.yaml >nul
        echo  OK: extra_model_paths.yaml copiado a ComfyUI
    )
)

REM ---- 8. Workflows ----
echo.
echo  [8/8] Copiando workflows preconfigurados...
if not exist "ComfyUI\user\default\workflows" mkdir "ComfyUI\user\default\workflows"
xcopy /Y /E workflows\*.json "ComfyUI\user\default\workflows\" >nul
echo  OK: Workflows copiados a ComfyUI\user\default\workflows\

REM ---- Convertir workflows a API Format ----
echo.
echo  Convirtiendo workflows a API Format (necesario para auto_publish)...
python scripts\convert_workflow_format.py --all
echo  OK: Workflows API Format generados.

REM ---- Inicializar configuracion del usuario ----
echo.
echo  Inicializando configuracion (.env, calendar.json)...
python scripts\init_config.py

REM ---- Aplicar tema de marca a ComfyUI ----
echo.
echo  Aplicando tema de marca a ComfyUI...
python scripts\apply_theme.py

REM ---- Validacion post-instalacion ----
echo.
echo  ============================================================
echo   VALIDACION POST-INSTALACION
echo  ============================================================
python scripts\post_install.py

REM ---- Preguntar si iniciar todo ahora ----
echo.
set /p START_NOW="Iniciar todos los servicios ahora? (S/n): "
if /i not "!START_NOW!"=="n" (
    echo.
    echo  Iniciando todos los servicios...
    call start_all.bat
    exit /b 0
)

REM ---- Final ----
echo.
echo  ============================================================
echo   INSTALACION COMPLETA
echo  ============================================================
echo.
echo  Para iniciar TODO automatico:
echo    Doble clic en start_all.bat
echo.
echo  Para detener todo:
echo    Doble clic en stop_all.bat
echo.
echo  Dashboard de estado:
echo    http://127.0.0.1:8080 (despues de iniciar)
echo.
echo  Documentacion en la carpeta docs\
echo.
pause
exit /b 0
