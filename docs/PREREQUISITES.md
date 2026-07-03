# Prerrequisitos del Sistema

Esta guía explica qué necesita tu PC para ejecutar el ComfyUI Social Suite, y cómo el sistema los verifica e instala automáticamente.

---

## 🚀 Flujo Automático Recomendado

```bash
# Windows
bootstrap.bat

# Linux/macOS
chmod +x bootstrap.sh
./bootstrap.sh
```

El `bootstrap` hace TODO automáticamente:
1. Verifica cada prerrequisito
2. Si falta, lo descarga e instala silenciosamente
3. Vuelve a verificar
4. Si todo OK, ejecuta `install.bat` / `install.sh` para instalar el Suite completo
5. Al final, arranca todos los servicios con `start_all`

**No necesitas instalar nada manualmente.** Solo ejecuta `bootstrap` y espera.

---

## 📋 Lista Completa de Prerrequisitos

### Críticos (sin estos no funciona)

| # | Componente | Versión mínima | Cómo lo instala el bootstrap |
|---|------------|-----------------|------------------------------|
| 1 | **Python** | 3.10, 3.11 o 3.12 | Descarga instalador oficial de python.org y ejecuta silenciosamente con `PrependPath=1` |
| 2 | **Git** | cualquiera reciente | Descarga Git for Windows installer / `apt install git` |
| 3 | **pip** | incluido con Python | Se instala con Python |
| 4 | **Espacio disco** | 50 GB libres | (verificación, no se puede instalar) |
| 5 | **Internet** | acceso a github.com, huggingface.co, civitai.com, pypi.org | (verificación) |
| 6 | **Puertos libres** | 8188, 8189, 8080 | (verificación, debes liberarlos si ocupados) |
| 7 | **Permisos escritura** | en el directorio del proyecto | (verificación) |

### Recomendados (mejoran rendimiento)

| # | Componente | Versión mínima | Cómo lo instala el bootstrap |
|---|------------|-----------------|------------------------------|
| 8 | **GPU NVIDIA** | RTX 3060 12GB (ideal) | (verificación; descarga driver desde nvidia.com) |
| 9 | **Driver NVIDIA** | 525+ | (verificación; enlace a nvidia.com) |
| 10 | **RAM** | 16 GB (mínimo 8) | (verificación) |
| 11 | **FFmpeg** | cualquiera | `apt install ffmpeg` / `brew install ffmpeg` / descarga manual Windows |
| 12 | **Build essentials** | gcc + make (Linux) / VC++ Redist (Windows) | `apt install build-essential` / descarga VC++ Redist |

---

## 🔍 Verificación Detallada (`scripts/check_prerequisites.py`)

El script ejecuta **13 verificaciones**:

1. **Sistema operativo** — Windows 10+, Linux, macOS
2. **Python** — versión 3.10/3.11/3.12
3. **Git** — instalado y accesible
4. **pip** — funcional
5. **GPU NVIDIA** — nombre, VRAM, driver
6. **Espacio en disco** — al menos 30GB libres
7. **RAM** — al menos 8GB (16GB recomendado)
8. **FFmpeg** — para procesar videos
9. **Build tools** — gcc/make o VC++ Redist
10. **Conectividad internet** — GitHub, HuggingFace, CivitAI, PyPI, PyTorch
11. **Puertos disponibles** — 8188, 8189, 8080
12. **Permisos de escritura** — en el directorio del proyecto
13. **Variables de entorno** — detección de PYTHONPATH/PYTHONHOME/HTTP_PROXY problemáticos

### Uso del verificador

```bash
# Verificación normal (output formateado)
python scripts/check_prerequisites.py

# Output JSON (para integración con otras herramientas)
python scripts/check_prerequisites.py --json

# Con sugerencias de auto-fix
python scripts/check_prerequisites.py --fix
```

### Códigos de salida

| Code | Significado |
|------|-------------|
| 0 | Todos los checks OK (o solo warnings) |
| 1 | Hay fallos críticos, no se puede continuar |

---

## 🛠️ Bootstrap: Instalación Automática

### Windows (`bootstrap.bat`)

Hace lo siguiente:

1. **Verifica Python** (prueba `python` y `py launcher`)
   - Si no encuentra 3.10/3.11/3.12 → descarga `python-3.11.9-amd64.exe` desde python.org y ejecuta `/quiet InstallAllUsers=0 PrependPath=1`
2. **Verifica Git**
   - Si no lo encuentra → descarga `Git-2.45.0-64-bit.exe` desde git-for-windows.github.io y ejecuta `/VERYSILENT`
3. **Verifica VC++ Redistributable x64** (vía registro de Windows)
   - Si no está → descarga desde `aka.ms/vs/17/release/vc_redist.x64.exe` y ejecuta `/install /quiet`
4. **Verifica Driver NVIDIA** (vía `nvidia-smi`)
   - Si no responde → muestra advertencia + enlace a nvidia.com
   - Si la versión es < 525 → muestra advertencia
5. **Verifica PowerShell Execution Policy**
   - Si está en `Restricted` → cambia a `RemoteSigned` para el usuario actual
6. **Al final** → llama automáticamente a `install.bat`

### Linux/macOS (`bootstrap.sh`)

Detecta la distro automáticamente y:

1. **Verifica Python** (prueba `python3.12`, `python3.11`, `python3.10`, `python3`, `python`)
   - Si no encuentra versión compatible:
     - Ubuntu/Debian: añade PPA deadsnakes, instala `python3.11 python3.11-venv python3.11-dev python3-pip`
     - Fedora: instala `python3.11 python3-devel`
     - Arch: instala `python`
     - macOS: instala `python@3.11` vía Homebrew
2. **Verifica Git**
   - Si no lo encuentra → instala con `apt` / `dnf` / `pacman` / `zypper` / `brew`
3. **Verifica build essentials** (gcc, make)
   - Si faltan:
     - Ubuntu/Debian: `apt install build-essential python3-dev`
     - Fedora: `dnf install gcc gcc-c++ make`
     - Arch: `pacman -S base-devel`
     - macOS: `xcode-select --install`
4. **Verifica Driver NVIDIA** (vía `nvidia-smi`)
   - Si no está → muestra instrucciones específicas por distro
5. **Verifica FFmpeg**
   - Si no está → instala con el gestor de paquetes
6. **Al final** → llama automáticamente a `./install.sh`

---

## ⚠️ Casos Especiales

### "No tengo GPU NVIDIA"
El sistema funcionará en **modo CPU** (10-50x más lento). Para uso ocasional está bien, pero para generar contenido regularmente, una GPU NVIDIA es muy recomendable.

**GPUs compatibles** (con 12GB VRAM, recomendadas):
- RTX 3060 12GB
- RTX 4060 Ti 12GB
- RTX 4070 12GB
- RTX 4070 Ti 16GB
- RTX 4080 16GB
- RTX 4090 24GB

### "Tengo 8GB VRAM o menos"
Edita `config/launch_args.txt` y descomenta:
```
--lowvram
--force-fp16
```
El sistema funcionará pero más lento y sin soporte para SDXL completo.

### "Estoy en macOS"
Sin CUDA, ComfyUI usará MPS (Metal Performance Shaders). Funciona en M1/M2/M3 pero más lento que NVIDIA. El bootstrap lo detecta y adapta automáticamente.

### "Estoy detrás de un proxy corporativo"
El verificador detecta `HTTP_PROXY`/`HTTPS_PROXY` y avisa. Para que pip los use:
```bash
# Linux/macOS
export HTTP_PROXY=http://proxy.empresa.com:8080
export HTTPS_PROXY=http://proxy.empresa.com:8080

# Windows
set HTTP_PROXY=http://proxy.empresa.com:8080
set HTTPS_PROXY=http://proxy.empresa.com:8080
```

### "Los puertos están ocupados"
Si otro proceso usa 8188/8189/8080:
- Windows: `netstat -ano | findstr :8188` → mata el proceso con `taskkill /pid <PID> /f`
- Linux: `lsof -i :8188` → mata con `kill -9 <PID>`

O cambia los puertos editando `start_all.bat` / `start_all.sh`.

### "La descarga de Python falla"
Si tu red bloquea python.org, descarga manualmente:
- Python: https://www.python.org/downloads/release/python-3119/
- Git: https://git-scm.com/download/win
- VC++ Redist: https://aka.ms/vs/17/release/vc_redist.x64.exe

---

## 📊 Ver Manualmente Cada Prerrequisito

Si prefieres verificar manualmente (sin el script):

### Windows
```cmd
:: Python
python --version
:: o
py --version

:: Git
git --version

:: Driver NVIDIA
nvidia-smi

:: Espacio disco
wmic logicaldisk get size,freespace,caption

:: FFmpeg
ffmpeg -version
```

### Linux
```bash
# Python
python3 --version

# Git
git --version

# Driver NVIDIA
nvidia-smi

# Espacio disco
df -h .

# RAM
free -h

# FFmpeg
ffmpeg -version

# Build essentials
gcc --version
make --version
```

### macOS
```bash
# Python (via brew)
python3 --version

# Git
git --version

# Espacio disco
df -h .

# RAM
sysctl hw.memsize

# FFmpeg
ffmpeg -version
```

---

## ✅ Verificación Post-Instalación

Después del `install.bat` / `install.sh`, el sistema ejecuta automáticamente `scripts/post_install.py` que verifica:

1. ComfyUI instalado
2. Venv con paquetes base
3. PyTorch + CUDA funcional
4. Custom nodes esenciales
5. Modelos requeridos descargados
6. Workflows UI + API Format
7. Tema de marca aplicado
8. Configuración inicializada
9. Scripts auxiliares importan correctamente

Si todos los checks pasan, el sistema arranca automáticamente con `start_all.bat` / `start_all.sh`.

---

## 🆘 Troubleshooting del Bootstrap

### "PowerShell no puede descargar archivos"
Error: `Invoke-WebRequest : The request was aborted: Could not create SSL/TLS channel`

Solución:
```powershell
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
```
Y vuelve a ejecutar `bootstrap.bat`.

### "El instalador de Python no se ejecuta"
- Asegúrate de ejecutar como administrador
- Si tu antivirus bloquea el instalador, añade una excepción
- Descarga manualmente desde https://www.python.org/downloads/

### "El PATH no se actualiza tras instalar Python/Git"
- Cierra y reabre la terminal
- O reinicia Windows
- O ejecuta `refreshenv` (si tienes Chocolatey)

### "sudo: command not found" (Linux)
- Estás en un contenedor sin sudo. Usa `apt-get install` directamente como root.
- O entra como root: `su -`

### "PPA deadsnakes no disponible" (Ubuntu)
- Solo Ubuntu 22.04+ soporta el PPA. En Ubuntu 20.04, compila Python 3.11 manualmente o actualiza el SO.
- Alternativa: usa pyenv (`curl https://pyenv.run | bash`)

---

## 🔗 Enlaces Útiles

- **Python oficial**: https://www.python.org/downloads/
- **Git for Windows**: https://git-scm.com/download/win
- **VC++ Redistributable**: https://aka.ms/vs/17/release/vc_redist.x64.exe
- **Driver NVIDIA**: https://www.nvidia.com/Download/index.aspx
- **FFmpeg**: https://ffmpeg.org/download.html
- **CUDA Toolkit** (opcional, ComfyUI no lo requiere directamente):
  https://developer.nvidia.com/cuda-downloads

---

## 💡 Resumen

**Para el 90% de los casos, solo necesitas:**

```bash
# Windows
bootstrap.bat

# Linux/macOS
./bootstrap.sh
```

Y el sistema hace todo: verificar prerrequisitos → instalar los faltantes → instalar ComfyUI Suite → aplicar tema → validar → arrancar servicios → abrir navegador.
