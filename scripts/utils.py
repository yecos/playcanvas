"""
utils.py - Funciones compartidas para los scripts de instalacion
ComfyUI Social Media Suite
"""
import os
import sys
import subprocess
import shutil
import json
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# ---- Constantes ----
ROOT_DIR = Path(__file__).resolve().parent.parent
COMFYUI_DIR = ROOT_DIR / "ComfyUI"
CUSTOM_NODES_DIR = COMFYUI_DIR / "custom_nodes"
MODELS_DIR = COMFYUI_DIR / "models"
WORKFLOWS_DIR = ROOT_DIR / "workflows"
CONFIG_DIR = ROOT_DIR / "config"

# Códigos de color ANSI
class Color:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

# En Windows, activar soporte ANSI via colorama si esta disponible
if sys.platform.startswith('win'):
    try:
        import colorama
        colorama.init()
    except ImportError:
        # Si colorama no esta instalado, intentar activar VT processing nativo
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except Exception:
            pass


def cprint(msg, color=None):
    """Imprime con color."""
    if color:
        print(f"{color}{msg}{Color.END}")
    else:
        print(msg)


def info(msg):
    cprint(f"  [INFO] {msg}", Color.CYAN)


def ok(msg):
    cprint(f"  [OK]   {msg}", Color.GREEN)


def warn(msg):
    cprint(f"  [WARN] {msg}", Color.YELLOW)


def error(msg):
    cprint(f"  [ERROR] {msg}", Color.RED)


def step(n, total, msg):
    cprint(f"\n  [{n}/{total}] {msg}", Color.BOLD)


def run(cmd, cwd=None, check=True, capture=False):
    """Ejecuta un comando del sistema."""
    if isinstance(cmd, str):
        cmd = cmd.split()
    try:
        result = subprocess.run(
            cmd, cwd=cwd, check=check,
            capture_output=capture, text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        if capture:
            error(f"Comando fallo: {' '.join(cmd)}")
            error(f"stdout: {e.stdout}")
            error(f"stderr: {e.stderr}")
        raise


def is_windows():
    return sys.platform.startswith('win')


def is_linux():
    return sys.platform.startswith('linux')


def is_mac():
    return sys.platform == 'darwin'


def python_executable():
    """Devuelve la ruta al python del venv o al del sistema."""
    if is_windows():
        venv_py = ROOT_DIR / "venv" / "Scripts" / "python.exe"
    else:
        venv_py = ROOT_DIR / "venv" / "bin" / "python"
    if venv_py.exists():
        return str(venv_py)
    return sys.executable


def pip_executable():
    """Devuelve la ruta al pip del venv."""
    if is_windows():
        venv_pip = ROOT_DIR / "venv" / "Scripts" / "pip.exe"
    else:
        venv_pip = ROOT_DIR / "venv" / "bin" / "pip"
    if venv_pip.exists():
        return str(venv_pip)
    return "pip"


def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def download_file(url, dest, headers=None, retries=3):
    """
    Descarga un archivo con barra de progreso y soporte REAL de resume.
    Devuelve True si tuvo exito.
    """
    from tqdm import tqdm

    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Tamano ya descargado (para resume)
    existing_size = dest.stat().st_size if dest.exists() else 0

    for attempt in range(1, retries + 1):
        try:
            req = Request(url)
            if headers:
                for k, v in headers.items():
                    req.add_header(k, v)

            # Si tenemos un archivo parcial, anadir Range header para resumir
            if existing_size > 0:
                req.add_header("Range", f"bytes={existing_size}-")

            with urlopen(req, timeout=60) as response:
                # Verificar si el servidor soporta resume (206 Partial Content)
                supports_resume = response.status == 206
                total_header = response.headers.get('Content-Length', 0)
                if supports_resume:
                    total = int(total_header) + existing_size
                else:
                    # El servidor no soporta resume, empezar desde 0
                    total = int(total_header)
                    existing_size = 0

                chunk_size = 1024 * 1024  # 1MB
                mode = 'ab' if (supports_resume and existing_size > 0) else 'wb'

                with open(dest, mode) as f, tqdm(
                    total=total,
                    unit='B',
                    unit_scale=True,
                    unit_divisor=1024,
                    desc=dest.name,
                    initial=existing_size,
                ) as pbar:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        pbar.update(len(chunk))
            return True
        except (URLError, HTTPError, ConnectionError, TimeoutError) as e:
            warn(f"Intento {attempt}/{retries} fallo para {dest.name}: {e}")
            if attempt == retries:
                return False
            # Actualizar existing_size por si acaso se descargo algo
            existing_size = dest.stat().st_size if dest.exists() else 0
    return False


def file_exists_with_size(path, min_size_mb=1):
    """Verifica si un archivo existe y tiene tamano minimo."""
    p = Path(path)
    if not p.exists():
        return False
    return p.stat().st_size >= min_size_mb * 1024 * 1024


def get_gpu_info():
    """Devuelve info de la GPU NVIDIA si esta disponible."""
    try:
        result = run("nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader",
                     capture=True, check=False)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def get_python_version():
    """Devuelve la version de Python como tupla (major, minor, patch)."""
    return sys.version_info[:3]


def check_python_version():
    """Verifica que la version de Python sea compatible (3.10 o 3.11)."""
    v = get_python_version()
    if v[0] != 3 or v[1] not in (10, 11, 12):
        return False, f"{v[0]}.{v[1]}.{v[2]}"
    return True, f"{v[0]}.{v[1]}.{v[2]}"


def git_clone(url, dest, depth=1):
    """Clona un repo Git."""
    cmd = ["git", "clone"]
    if depth:
        cmd.append(f"--depth={depth}")
    cmd.extend([url, str(dest)])
    run(cmd, check=False)


def git_pull(dest):
    """Hace git pull en un directorio."""
    run(["git", "-C", str(dest), "pull"], check=False)


def ensure_dir(path):
    """Crea un directorio si no existe."""
    Path(path).mkdir(parents=True, exist_ok=True)


def banner(title):
    """Imprime un banner."""
    width = 60
    cprint("=" * width, Color.BLUE)
    cprint(title.center(width), Color.BOLD)
    cprint("=" * width, Color.BLUE)
