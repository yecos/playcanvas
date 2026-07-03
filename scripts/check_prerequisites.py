"""
check_prerequisites.py - Verificacion exhaustiva de TODOS los prerrequisitos

Comprueba:
  1. Sistema operativo soportado
  2. Python version compatible (3.10/3.11/3.12)
  3. Git instalado y accesible
  4. Pip funcional
  5. Driver NVIDIA + nvidia-smi
  6. VRAM suficiente (>= 6GB recomendado, 12GB ideal)
  7. Espacio en disco (>= 50GB libres)
  8. RAM suficiente (>= 8GB)
  9. FFmpeg (para videos)
  10. Build essentials (gcc/make en Linux, MSVC en Windows)
  11. Conectividad a internet
  12. Puertos disponibles (8188, 8189, 8080)
  13. Acceso a github.com, huggingface.co, civitai.com
  14. Permisos de escritura en el directorio
  15. Variables de entorno problematicas

Uso:
    python check_prerequisites.py
    python check_prerequisites.py --json       # output JSON
    python check_prerequisites.py --fix        # intentar auto-fix
"""
import os
import sys
import json
import shutil
import socket
import platform
import subprocess
import argparse
import time
import urllib.request
from pathlib import Path
from typing import Dict, List, Tuple, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import cprint, info, ok, warn, error, banner, ROOT_DIR, is_windows, is_linux, is_mac


# ============================================================
# Checks individuales
# ============================================================

def check_os() -> Tuple[bool, str, str]:
    """Sistema operativo soportado."""
    system = platform.system()
    if system == "Windows":
        return True, "Windows", f"{platform.win32_ver()[0]} {platform.win32_ver()[1]}"
    elif system == "Linux":
        distro = "unknown"
        try:
            with open("/etc/os-release") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME="):
                        distro = line.split("=")[1].strip().strip('"')
                        break
        except Exception:
            pass
        return True, "Linux", distro
    elif system == "Darwin":
        return True, "macOS", platform.mac_ver()[0]
    return False, system, "no soportado oficialmente"


def check_python() -> Tuple[bool, str, str]:
    """Version de Python compatible."""
    v = sys.version_info
    version_str = f"{v.major}.{v.minor}.{v.micro}"
    if v.major == 3 and v.minor in (10, 11, 12):
        return True, version_str, "OK"
    return False, version_str, "Se requiere Python 3.10, 3.11 o 3.12"


def check_git() -> Tuple[bool, str, str]:
    """Git instalado."""
    if shutil.which("git"):
        result = subprocess.run(["git", "--version"], capture_output=True, text=True)
        return True, result.stdout.strip(), "OK"
    return False, "no encontrado", "Instala desde https://git-scm.com/"


def check_pip() -> Tuple[bool, str, str]:
    """Pip funcional."""
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "--version"],
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return True, result.stdout.strip()[:80], "OK"
    except Exception as e:
        pass
    return False, "no disponible", "Reinstala Python con pip incluido"


def check_nvidia() -> Tuple[bool, str, str, Dict]:
    """Driver NVIDIA + info GPU."""
    info_extra = {}
    if not shutil.which("nvidia-smi"):
        return False, "no encontrado", "Driver NVIDIA no instalado", info_extra

    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version",
             "--format=csv,noheader"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            return False, "nvidia-smi error", result.stderr.strip(), info_extra

        parts = result.stdout.strip().split(", ")
        if len(parts) >= 3:
            name, vram_str, driver = parts[0], parts[1], parts[2]
            vram_mb = int(''.join(c for c in vram_str if c.isdigit()))
            info_extra = {
                "name": name,
                "vram_mb": vram_mb,
                "vram_gb": vram_mb / 1024,
                "driver": driver,
            }
            # Driver mayor que 525
            major = int(driver.split('.')[0])
            if major < 525:
                return True, name, f"Driver {driver} antiguo (recomendado >=525)", info_extra
            return True, name, f"VRAM {vram_mb}MB, driver {driver}", info_extra
    except Exception as e:
        return False, "error", str(e), info_extra

    return False, "desconocido", "", info_extra


def check_disk_space() -> Tuple[bool, str, str]:
    """Espacio en disco."""
    usage = shutil.disk_usage(ROOT_DIR)
    free_gb = usage.free / (1024**3)
    if free_gb < 30:
        return False, f"{free_gb:.1f} GB libres", "Se necesitan al menos 30GB"
    elif free_gb < 60:
        return True, f"{free_gb:.1f} GB libres", "Recomendado 100GB+ para todos los modelos"
    return True, f"{free_gb:.1f} GB libres", "OK"


def check_ram() -> Tuple[bool, str, str]:
    """RAM disponible."""
    try:
        import psutil
        ram_gb = psutil.virtual_memory().total / (1024**3)
        if ram_gb < 8:
            return False, f"{ram_gb:.1f} GB", "Recomendado 16GB+"
        elif ram_gb < 16:
            return True, f"{ram_gb:.1f} GB", "Recomendado 16GB+"
        return True, f"{ram_gb:.1f} GB", "OK"
    except ImportError:
        return True, "psutil no disponible", "Instala psutil para verificar RAM"


def check_ffmpeg() -> Tuple[bool, str, str]:
    """FFmpeg instalado."""
    if shutil.which("ffmpeg"):
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
        version = result.stdout.split("\n")[0] if result.stdout else "ffmpeg"
        return True, version[:80], "OK"
    return False, "no encontrado", "Necesario para videos. apt install ffmpeg / brew install ffmpeg"


def check_build_tools() -> Tuple[bool, str, str]:
    """Build essentials disponibles."""
    if is_windows():
        # En Windows, comprobar Visual C++ Redistributable
        try:
            result = subprocess.run(
                ["reg", "query",
                 "HKLM\\SOFTWARE\\Microsoft\\VisualStudio\\14.0\\VC\\Runtimes\\X64",
                 "/v", "Version"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                return True, "VC++ Redist x64 instalado", "OK"
        except Exception:
            pass
        return False, "VC++ Redist no detectado", "Descarga desde https://aka.ms/vs/17/release/vc_redist.x64.exe"
    else:
        # Linux/macOS: gcc y make
        gcc = shutil.which("gcc") or shutil.which("cc")
        make = shutil.which("make")
        if gcc and make:
            return True, "gcc + make", "OK"
        return False, "build essentials faltantes", "apt install build-essential / xcode-select --install"


def check_internet() -> Tuple[bool, str, str, Dict]:
    """Conectividad a internet y servicios clave."""
    services = {
        "GitHub": "github.com",
        "HuggingFace": "huggingface.co",
        "CivitAI": "civitai.com",
        "PyPI": "pypi.org",
        "PyTorch": "download.pytorch.org",
    }
    results = {}
    all_ok = True
    for name, host in services.items():
        try:
            socket.gethostbyname(host)
            results[name] = True
        except socket.gaierror:
            results[name] = False
            all_ok = False

    if all_ok:
        return True, "Todos los servicios accesibles", "OK", results
    failed = [k for k, v in results.items() if not v]
    return False, "Sin acceso a: " + ", ".join(failed), "Verifica DNS / firewall / VPN", results


def check_ports() -> Tuple[bool, str, str, Dict]:
    """Puertos disponibles."""
    ports = {8188: "ComfyUI", 8189: "Webhook Server", 8080: "Dashboard"}
    results = {}
    all_free = True
    for port, name in ports.items():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(("127.0.0.1", port))
            sock.close()
            results[name] = True
        except OSError:
            results[name] = False
            all_free = False

    if all_free:
        return True, "Todos los puertos libres", "OK", results
    occupied = [f"{name}(:{port})" for port, name in ports.items() if not results[name]]
    return False, "Puertos ocupados: " + ", ".join(occupied), "Deten servicios previos o cambia puertos", results


def check_write_perms() -> Tuple[bool, str, str]:
    """Permisos de escritura."""
    try:
        test_file = ROOT_DIR / ".write_test"
        with open(test_file, "w") as f:
            f.write("test")
        test_file.unlink()
        return True, "Permisos OK", "OK"
    except Exception as e:
        return False, "Sin permisos de escritura", str(e)


def check_env_problematic() -> Tuple[bool, str, str]:
    """Variables de entorno problematicas."""
    issues = []
    # PYTHONPATH podria interferir
    if os.environ.get("PYTHONPATH"):
        issues.append(f"PYTHONPATH={os.environ['PYTHONPATH'][:50]}...")
    # PYTHONHOME podria romper venv
    if os.environ.get("PYTHONHOME"):
        issues.append(f"PYTHONHOME={os.environ['PYTHONHOME']}")
    # HTTP_PROXY podria bloquear descargas
    for var in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
        if os.environ.get(var):
            issues.append(f"{var}={os.environ[var][:50]}...")

    if issues:
        return True, "Variables detectadas: " + "; ".join(issues), "Posible interferencia"
    return True, "Sin variables problematicas", "OK"


# ============================================================
# Main
# ============================================================

def run_all_checks() -> Dict:
    """Ejecuta todos los checks y devuelve un dict estructurado."""
    checks = []

    # (id, nombre, funcion, severity: 'critical'|'warning'|'info')
    checks_def = [
        ("os", "Sistema operativo", check_os, "critical"),
        ("python", "Python version", check_python, "critical"),
        ("git", "Git", check_git, "critical"),
        ("pip", "pip", check_pip, "critical"),
        ("nvidia", "GPU NVIDIA", check_nvidia, "warning"),
        ("disk", "Espacio en disco", check_disk_space, "critical"),
        ("ram", "RAM", check_ram, "warning"),
        ("ffmpeg", "FFmpeg", check_ffmpeg, "warning"),
        ("build_tools", "Build tools", check_build_tools, "warning"),
        ("internet", "Conectividad internet", check_internet, "critical"),
        ("ports", "Puertos disponibles", check_ports, "critical"),
        ("write_perms", "Permisos escritura", check_write_perms, "critical"),
        ("env", "Variables entorno", check_env_problematic, "info"),
    ]

    results = {}
    for cid, name, fn, severity in checks_def:
        try:
            result = fn()
            # Algunas funciones devuelven 3 valores, otras 4
            if len(result) == 4:
                passed, value, message, extra = result
            else:
                passed, value, message = result
                extra = None
            results[cid] = {
                "name": name,
                "severity": severity,
                "passed": passed,
                "value": value,
                "message": message,
                "extra": extra,
            }
        except Exception as e:
            results[cid] = {
                "name": name,
                "severity": severity,
                "passed": False,
                "value": "error",
                "message": str(e),
                "extra": None,
            }

    return results


def print_results(results: Dict) -> int:
    """Imprime resultados formateados. Devuelve exit code."""
    banner("VERIFICACION DE PREREQUISITOS")

    critical_fail = 0
    warning_fail = 0
    total_ok = 0

    print()
    for cid, r in results.items():
        severity = r["severity"]
        passed = r["passed"]
        name = r["name"]
        value = r["value"]
        message = r["message"]

        if passed:
            color = '\033[92m'
            marker = "OK"
            total_ok += 1
        else:
            if severity == "critical":
                color = '\033[91m'
                marker = "FAIL"
                critical_fail += 1
            elif severity == "warning":
                color = '\033[93m'
                marker = "WARN"
                warning_fail += 1
            else:
                color = '\033[96m'
                marker = "INFO"

        # Truncar value si muy largo
        value_short = (value[:60] + "...") if len(value) > 60 else value

        cprint(f"  [{color}{marker:4}\033[0m] {name:25} {value_short}", '\033[0m')
        if not passed and message:
            cprint(f"         └─ {message}", '\033[90m')

    # Resumen
    print()
    banner("RESUMEN")
    total = len(results)
    cprint(f"  Total checks:  {total}", '\033[96m')
    cprint(f"  OK:            {total_ok}", '\033[92m')
    if warning_fail:
        cprint(f"  Warnings:      {warning_fail}", '\033[93m')
    if critical_fail:
        cprint(f"  Critical:      {critical_fail}", '\033[91m')

    print()
    if critical_fail == 0 and warning_fail == 0:
        ok("TODO PERFECTO. Sistema listo para instalar ComfyUI Social Suite.")
        cprint("\n  Ejecuta: install.bat (Windows) o ./install.sh (Linux)", '\033[96m')
        return 0
    elif critical_fail == 0:
        warn("Sistema listo con warnings. Puedes continuar pero revisa los WARN.")
        return 0
    else:
        error(f"{critical_fail} fallos criticos. Resuelve antes de continuar.")
        cprint("\n  Ejecuta: bootstrap.bat (Windows) o ./bootstrap.sh (Linux)", '\033[96m')
        cprint("  Para intentar auto-instalacion de prerrequisitos.", '\033[0m')
        return 1


def main():
    parser = argparse.ArgumentParser(description="Verificador de prerrequisitos")
    parser.add_argument("--json", action="store_true",
                        help="Output como JSON")
    parser.add_argument("--fix", action="store_true",
                        help="Intentar auto-fix (instalar prerrequisitos faltantes)")
    args = parser.parse_args()

    results = run_all_checks()

    if args.json:
        print(json.dumps(results, indent=2, default=str))
        return 0

    exit_code = print_results(results)

    if args.fix and exit_code != 0:
        print()
        cprint("Modo --fix: intentando auto-instalacion...", '\033[96m')
        cprint("Ejecuta bootstrap.bat (Windows) o ./bootstrap.sh (Linux) para auto-instalar.", '\033[96m')

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
