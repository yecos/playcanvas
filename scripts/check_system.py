"""
check_system.py - Verifica que el sistema cumple los requisitos
ComfyUI Social Media Suite
"""
import sys
import os
import shutil
import subprocess
from pathlib import Path

# Permite importar utils desde el mismo directorio
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import (
    cprint, info, ok, warn, error, banner,
    is_windows, is_linux, is_mac,
    get_gpu_info, check_python_version, run,
    ROOT_DIR
)


def check_os():
    """Verifica el sistema operativo."""
    info("Sistema operativo detectado:")
    if is_windows():
        ok("Windows")
        return True
    elif is_linux():
        ok("Linux")
        return True
    elif is_mac():
        warn("macOS (sin soporte CUDA, modo CPU lento)")
        return True
    else:
        warn(f"Sistema no soportado oficialmente: {sys.platform}")
        return True


def check_python():
    """Verifica la version de Python."""
    valid, version = check_python_version()
    if not valid:
        error(f"Python {version} no es compatible.")
        error("Instala Python 3.10 o 3.11 desde: https://www.python.org/downloads/")
        return False
    ok(f"Python {version}")
    return True


def check_git():
    """Verifica que Git este instalado."""
    if shutil.which("git"):
        result = run("git --version", capture=True, check=False)
        ok(result.stdout.strip())
        return True
    error("Git no esta instalado.")
    error("  Windows:  https://git-scm.com/download/win")
    error("  Linux:    sudo apt install git")
    return False


def check_nvidia():
    """Verifica la GPU NVIDIA."""
    gpu = get_gpu_info()
    if not gpu:
        warn("No se detecto GPU NVIDIA. ComfyUI funcionara en modo CPU (MUY lento).")
        return False
    ok(f"GPU NVIDIA: {gpu}")

    # Extraer VRAM
    try:
        parts = gpu.split(',')
        vram_str = parts[1].strip() if len(parts) > 1 else ""
        if "MiB" in vram_str:
            vram_mb = int(''.join(filter(str.isdigit, vram_str.split()[0])))
            if vram_mb < 8000:
                warn(f"VRAM {vram_mb}MB puede ser insuficiente para SDXL.")
                warn("Considera editar config/launch_args.txt y anadir --lowvram")
            elif vram_mb >= 11000 and vram_mb <= 13000:
                ok(f"VRAM {vram_mb}MB - perfecto para RTX 3060 12GB (configuracion optimizada)")
            else:
                ok(f"VRAM {vram_mb}MB")
    except Exception:
        pass
    return True


def check_cuda():
    """Verifica el driver CUDA."""
    if not shutil.which("nvidia-smi"):
        return False
    result = run("nvidia-smi --query-gpu=driver_version --format=csv,noheader",
                 capture=True, check=False)
    if result.returncode == 0:
        driver = result.stdout.strip()
        ok(f"Driver NVIDIA: {driver}")
        # Driver 525+ soporta CUDA 12.1
        try:
            major = int(driver.split('.')[0])
            if major < 525:
                warn(f"Driver {driver} puede ser antiguo. Recomendado >= 525.")
                warn("Actualiza desde: https://www.nvidia.com/Download/index.aspx")
        except Exception:
            pass
    return True


def check_disk_space():
    """Verifica espacio en disco."""
    usage = shutil.disk_usage(ROOT_DIR)
    free_gb = usage.free / (1024 ** 3)
    if free_gb < 30:
        error(f"Solo {free_gb:.1f}GB libres. Se necesitan al menos 30GB.")
        return False
    elif free_gb < 60:
        warn(f"Solo {free_gb:.1f}GB libres. Recomendado 100GB+ para todos los modelos.")
    else:
        ok(f"Espacio libre: {free_gb:.1f}GB")
    return True


def check_ram():
    """Verifica RAM disponible."""
    try:
        import psutil
        ram_gb = psutil.virtual_memory().total / (1024 ** 3)
        if ram_gb < 16:
            warn(f"RAM {ram_gb:.1f}GB - recomendado 16GB+")
        else:
            ok(f"RAM: {ram_gb:.1f}GB")
        return True
    except ImportError:
        # psutil no esencial
        return True


def main():
    banner("VERIFICACION DEL SISTEMA")

    all_ok = True
    all_ok &= check_os()
    all_ok &= check_python()
    all_ok &= check_git()
    has_nvidia = check_nvidia()
    if has_nvidia:
        check_cuda()
    all_ok &= check_disk_space()
    check_ram()

    print()
    if all_ok:
        ok("Sistema listo para instalar ComfyUI Social Suite")
        return 0
    else:
        error("Sistema no cumple los requisitos minimos.")
        error("Corrige los errores arriba y vuelve a ejecutar install.bat/install.sh")
        return 1


if __name__ == "__main__":
    sys.exit(main())
