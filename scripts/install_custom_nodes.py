"""
install_custom_nodes.py - Instala los custom nodes esenciales
ComfyUI Social Media Suite

Uso:
    python install_custom_nodes.py           # Instala los que faltan
    python install_custom_nodes.py --update  # Actualiza todos
    python install_custom_nodes.py --force   # Reinstala todo
"""
import os
import sys
import shutil
import argparse
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import (
    cprint, info, ok, warn, error, banner,
    git_clone, git_pull, run, load_json,
    CUSTOM_NODES_DIR, ROOT_DIR, pip_executable
)

NODES_LIST = ROOT_DIR / "custom_nodes_list.json"


def install_node(node, force=False, update=False):
    """Instala o actualiza un custom node."""
    name = node["name"]
    url = node["url"]
    required = node.get("required", False)
    desc = node.get("description", "")
    dest = CUSTOM_NODES_DIR / name

    info(f"Procesando: {name}")
    if desc:
        cprint(f"           {desc}", '\033[90m')

    if dest.exists():
        if force:
            shutil.rmtree(dest)
        elif update:
            ok(f"  Actualizando {name}...")
            git_pull(dest)
            # Instalar requirements si existen
            req = dest / "requirements.txt"
            if req.exists():
                run([pip_executable(), "install", "-r", str(req)], check=False)
            return True
        else:
            ok(f"  Ya instalado: {name}")
            return True

    # Clonar
    info(f"  Clonando desde {url}...")
    git_clone(url, dest, depth=1)

    if not dest.exists():
        if required:
            error(f"  FALLO al instalar (requerido): {name}")
            return False
        else:
            warn(f"  FALLO al instalar (opcional): {name}")
            return False

    # Instalar requirements si existen
    req = dest / "requirements.txt"
    if req.exists():
        info(f"  Instalando dependencias de {name}...")
        run([pip_executable(), "install", "-r", str(req)], check=False)

    ok(f"  Instalado: {name}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Instalador de custom nodes")
    parser.add_argument("--update", action="store_true",
                        help="Actualizar custom nodes existentes")
    parser.add_argument("--force", action="store_true",
                        help="Forzar reinstalacion completa")
    args = parser.parse_args()

    banner("INSTALACION DE CUSTOM NODES")

    if not NODES_LIST.exists():
        error(f"No se encontro {NODES_LIST}")
        return 1

    if not CUSTOM_NODES_DIR.exists():
        CUSTOM_NODES_DIR.mkdir(parents=True, exist_ok=True)

    data = load_json(NODES_LIST)
    nodes = data.get("nodes", [])

    cprint(f"\n  Total de custom nodes a procesar: {len(nodes)}\n",
           '\033[96m')

    success = 0
    failed = 0
    failed_required = 0

    for node in nodes:
        if install_node(node, force=args.force, update=args.update):
            success += 1
        else:
            failed += 1
            if node.get("required", False):
                failed_required += 1

    # ---- Resumen ----
    print()
    banner("RESUMEN CUSTOM NODES")
    ok(f"Instalados/OK:   {success}")
    if failed:
        warn(f"Fallos:          {failed}")
    if failed_required:
        error(f"Fallos criticos: {failed_required}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
