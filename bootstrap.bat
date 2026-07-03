@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
title ComfyUI Social Suite - Bootstrap (Verificador + Instalador de prerrequisitos)
color 0B

REM ============================================================
REM  ComfyUI Social Suite - BOOTSTRAP para Windows
REM  Verifica e instala automaticamente:
REM    1. Python 3.11
REM    2. Git
REM    3. Visual C++ Redistributable (x64)
REM    4. Driver NVIDIA (verificacion + enlace)
REM    5. permisos de ejecucion de scripts
REM  Despues ejecuta install.bat automaticamente.
REM ============================================================

cd /d "%~dp0"

echo.
echo  ============================================================
echo   COMFYUI SOCIAL SUITE - BOOTSTRAP WINDOWS
echo   Verificador e instalador automatico de prerrequisitos
echo  ============================================================
echo.

set "NEED_REBOOT=0"
set "BOOTSTRAP_OK=1"

REM ---- Funcion: ejecutar como admin si hace falta ----
net session >nul 2>&1
if errorlevel 1 (
    echo  AVISO: Algunas instalaciones pueden requerir permisos de admin.
    echo  Si fallan, ejecuta este .bat como administrador.
    echo.
)

REM ============================================================
REM 1. Verificar Python 3.10/3.11/3.12
REM ============================================================
echo  [1/5] Verificando Python...
set "PYTHON_OK=0"

REM Probar diferentes comandos
python --version >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYVER=%%i
    REM Verificar version 3.10-3.12
    for /f "tokens=1,2 delims=." %%a in ("!PYVER!") do (
        set "PYMAJOR=%%a"
        set "PYMINOR=%%b"
    )
    if "!PYMAJOR!"=="3" (
        if "!PYMINOR!"=="10" set "PYTHON_OK=1"
        if "!PYMINOR!"=="11" set "PYTHON_OK=1"
        if "!PYMINOR!"=="12" set "PYTHON_OK=1"
    )
)

REM Si python no funciona, probar py launcher
if "!PYTHON_OK!"=="0" (
    py --version >nul 2>&1
    if not errorlevel 1 (
        for /f "tokens=2" %%i in ('py --version 2^>^&1') do set PYVER=%%i
        for /f "tokens=1,2 delims=." %%a in ("!PYVER!") do (
            set "PYMAJOR=%%a"
            set "PYMINOR=%%b"
        )
        if "!PYMAJOR!"=="3" (
            if "!PYMINOR!"=="10" set "PYTHON_OK=1"
            if "!PYMINOR!"=="11" set "PYTHON_OK=1"
            if "!PYMINOR!"=="12" set "PYTHON_OK=1"
        )
    )
)

if "!PYTHON_OK!"=="1" (
    echo  OK: Python !PYVER! detectado.
) else (
    echo  Python 3.10/3.11/3.12 no encontrado. Instalando...
    call :install_python
    if errorlevel 1 (
        echo  ERROR: No se pudo instalar Python automaticamente.
        echo  Instala manualmente desde: https://www.python.org/downloads/release/python-3119/
        echo  Asegurate de marcar "Add Python to PATH" durante la instalacion.
        set "BOOTSTRAP_OK=0"
        goto end
    )
    set "NEED_REBOOT=1"
    REM Refrescar PATH
    call :refresh_path
)

REM ============================================================
REM 2. Verificar Git
REM ============================================================
echo.
echo  [2/5] Verificando Git...
git --version >nul 2>&1
if errorlevel 1 (
    echo  Git no encontrado. Instalando...
    call :install_git
    if errorlevel 1 (
        echo  ERROR: No se pudo instalar Git automaticamente.
        echo  Instala manualmente desde: https://git-scm.com/download/win
        set "BOOTSTRAP_OK=0"
        goto end
    )
    set "NEED_REBOOT=1"
    call :refresh_path
) else (
    for /f "tokens=*" %%i in ('git --version 2^>^&1') do set GITVER=%%i
    echo  OK: !GITVER!
)

REM ============================================================
REM 3. Verificar Visual C++ Redistributable (x64)
REM ============================================================
echo.
echo  [3/5] Verificando Visual C++ Redistributable x64...
set "VC_REDIST_OK=0"

REM Comprobar en el registro
reg query "HKLM\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\X64" /v Version >nul 2>&1
if not errorlevel 1 (
    set "VC_REDIST_OK=1"
)

if "!VC_REDIST_OK!"=="0" (
    echo  VC++ Redistributable no detectado. Instalando...
    call :install_vc_redist
    REM No es critico si falla, continuamos de todos modos
    echo  Continuando con el resto de la instalacion...
) else (
    echo  OK: VC++ Redistributable x64 instalado.
)

REM ============================================================
REM 4. Verificar driver NVIDIA
REM ============================================================
echo.
echo  [4/5] Verificando GPU NVIDIA...
nvidia-smi >nul 2>&1
if errorlevel 1 goto nvidia_missing

REM NVIDIA presente - extraer info
for /f "tokens=1,2 delims=," %%a in ('nvidia-smi --query-gpu^=name,memory.total --format^=csv^,noheader 2^>^&1') do (
    echo  OK: GPU: %%a, VRAM: %%b
    goto nvidia_check_driver
)

:nvidia_check_driver
for /f "tokens=*" %%a in ('nvidia-smi --query-gpu^=driver_version --format^=csv^,noheader 2^>^&1') do set "DRVVER=%%a"
if defined DRVVER (
    for /f "tokens=1 delims=." %%a in ("!DRVVER!") do set "DRVMAJOR=%%a"
    if !DRVMAJOR! LSS 525 (
        echo  ADVERTENCIA: Driver !DRVVER! puede ser antiguo ^(recomendado ^>= 525^).
        echo  Actualiza desde: https://www.nvidia.com/Download/index.aspx
    ) else (
        echo  OK: Driver NVIDIA !DRVVER!
    )
)
goto nvidia_done

:nvidia_missing
echo  ADVERTENCIA: nvidia-smi no responde.
echo  Posibles causas:
echo    - No tienes GPU NVIDIA instalada
echo    - Driver NVIDIA no instalado o muy antiguo
echo    - GPU integrada Intel/AMD activa en lugar de la NVIDIA
echo.
echo  ComfyUI funcionara en modo CPU ^(MUY lento, 10-50x mas lento^).
echo.
echo  Si tienes GPU NVIDIA, descarga el driver mas reciente desde:
echo    https://www.nvidia.com/Download/index.aspx
echo  Selecciona: GeForce -^> GeForce RTX 30 Series -^> RTX 3060 -^> Windows 11
echo.
echo  Continuando de todos modos en modo CPU...

:nvidia_done

REM ============================================================
REM 5. Verificar permisos de ejecucion de scripts PowerShell
REM ============================================================
echo.
echo  [5/5] Verificando permisos de PowerShell...
powershell -Command "Get-ExecutionPolicy" >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%a in ('powershell -Command "Get-ExecutionPolicy" 2^>^&1') do set PSEPOLICY=%%a
    if /i "!PSEPOLICY!"=="Restricted" (
        echo  PowerShell en modo Restricted. Cambiando a RemoteSigned...
        powershell -Command "Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force" >nul 2>&1
        if errorlevel 1 (
            echo  No se pudo cambiar automaticamente. Algunas funciones pueden fallar.
        ) else (
            echo  OK: PowerShell ahora permite scripts locales.
        )
    ) else (
        echo  OK: PowerShell policy = !PSEPOLICY!
    )
)

REM ============================================================
REM Final
REM ============================================================
:end
echo.
echo  ============================================================
if "!BOOTSTRAP_OK!"=="1" (
    echo   BOOTSTRAP COMPLETADO
    if "!NEED_REBOOT!"=="1" (
        echo.
        echo  AVISO: Se instalaron componentes que requieren reinicio.
        echo  Tras reiniciar, vuelve a ejecutar este .bat para continuar.
        echo.
        pause
        exit /b 2
    )
    echo.
    echo  Todos los prerrequisitos estan listos.
    echo  Procediendo con la instalacion del ComfyUI Social Suite...
    echo.
    timeout /t 3 /nobreak >nul
    call install.bat %*
) else (
    echo   BOOTSTRAP INCOMPLETO
    echo.
    echo  Resuelve los errores arriba y vuelve a ejecutar este .bat.
    echo.
    pause
    exit /b 1
)

REM ============================================================
REM Funciones auxiliares
REM ============================================================

:install_python
    echo  Descargando Python 3.11.9...
    set "PY_URL=https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
    set "PY_INSTALLER=%TEMP%\python-installer.exe"

    REM Probar con powershell (siempre disponible en Win10+)
    powershell -Command "Invoke-WebRequest -Uri '!PY_URL!' -OutFile '!PY_INSTALLER!' -UseBasicParsing" 2>nul
    if errorlevel 1 (
        REM Fallback con curl
        curl -L -o "!PY_INSTALLER!" "!PY_URL!" 2>nul
    )

    if not exist "!PY_INSTALLER!" (
        echo  No se pudo descargar Python.
        exit /b 1
    )

    echo  Instalando Python silenciosamente...
    REM /quiet - sin UI
    REM InstallAllUsers=0 - solo usuario actual (no requiere admin)
    REM PrependPath=1 - anadir al PATH
    REM Include_pip=1 - incluir pip
    "!PY_INSTALLER!" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1

    if errorlevel 1 (
        echo  Instalacion silenciosa fallo, intentando con UI minima...
        "!PY_INSTALLER!" /passive InstallAllUsers=0 PrependPath=1 Include_pip=1
    )

    del "!PY_INSTALLER!" >nul 2>&1
    exit /b 0

:install_git
    echo  Descargando Git for Windows...
    set "GIT_URL=https://github.com/git-for-windows/git/releases/download/v2.45.0.windows.1/Git-2.45.0-64-bit.exe"
    set "GIT_INSTALLER=%TEMP%\git-installer.exe"

    powershell -Command "Invoke-WebRequest -Uri '!GIT_URL!' -OutFile '!GIT_INSTALLER!' -UseBasicParsing" 2>nul
    if errorlevel 1 (
        curl -L -o "!GIT_INSTALLER!" "!GIT_URL!" 2>nul
    )

    if not exist "!GIT_INSTALLER!" (
        echo  No se pudo descargar Git.
        exit /b 1
    )

    echo  Instalando Git silenciosamente...
    "!GIT_INSTALLER!" /VERYSILENT /NORESTART /NOCANCEL /SP- /CLOSEAPPLICATIONS /RESTARTAPPLICATIONS

    del "!GIT_INSTALLER!" >nul 2>&1
    exit /b 0

:install_vc_redist
    echo  Descargando VC++ Redistributable desde Microsoft...
    set "VC_URL=https://aka.ms/vs/17/release/vc_redist.x64.exe"
    set "VC_INSTALLER=%TEMP%\vc_redist.x64.exe"

    REM Metodo 1: PowerShell
    echo  Intentando con PowerShell...
    powershell -Command "try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%VC_URL%' -OutFile '%VC_INSTALLER%' -UseBasicParsing -TimeoutSec 60 } catch { exit 1 }" 2>nul
    if exist "!VC_INSTALLER!" goto vc_install

    REM Metodo 2: curl
    echo  Reintentando con curl...
    curl -L --connect-timeout 30 -o "!VC_INSTALLER!" "!VC_URL!" 2>nul
    if exist "!VC_INSTALLER!" goto vc_install

    echo  No se pudo descargar automaticamente ^(posible firewall/antivirus^).
    echo  Descarga manual desde: https://aka.ms/vs/17/release/vc_redist.x64.exe
    echo  Ejecuta el .exe descargado y vuelve a correr bootstrap.bat
    exit /b 1

:vc_install
    echo  Instalando VC++ Redistributable...
    "!VC_INSTALLER!" /install /quiet /norestart
    if errorlevel 1 (
        echo  Instalacion silenciosa fallo, intentando con UI...
        "!VC_INSTALLER!" /install /passive /norestart
    )
    del "!VC_INSTALLER!" >nul 2>&1
    echo  OK: VC++ Redistributable instalado.
    exit /b 0

:refresh_path
    REM Refrescar PATH en la sesion actual
    for /f "usebackq tokens=2,*" %%a in (`reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v PATH 2^>nul`) do set "SYS_PATH=%%b"
    for /f "usebackq tokens=2,*" %%a in (`reg query "HKCU\Environment" /v PATH 2^>nul`) do set "USR_PATH=%%b"
    set "PATH=!SYS_PATH!;!USR_PATH!"
    REM Tambien recargar variables de Python
    set "PYTHONPATH="
    set "PYTHONHOME="
    exit /b 0
