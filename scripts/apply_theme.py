"""
apply_theme.py - Aplica el tema de marca a ComfyUI automaticamente

Hace 4 cosas:
  1. Copia config/user.css a ComfyUI/user/default/user.css
  2. Copia config/brand_palette.json a ComfyUI/user/default/brand_palette.json
     y la importa automaticamente en las settings de ComfyUI
  3. Verifica que el nuevo frontend este activo (recomendado)
  4. (Opcional) Instala Niutonian Themes via Manager

Uso:
    python apply_theme.py                # aplica tema
    python apply_theme.py --revert       # quita el tema (vuelve a default)
    python apply_theme.py --status       # muestra estado actual
"""
import os
import sys
import json
import shutil
import argparse
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import cprint, info, ok, warn, error, banner, ROOT_DIR


# ============================================================
# Paths
# ============================================================

COMFYUI_DIR = ROOT_DIR / "ComfyUI"
USER_DIR = COMFYUI_DIR / "user" / "default"
COMFYUI_SETTINGS = USER_DIR / "comfy.settings.json"

SRC_USER_CSS = ROOT_DIR / "config" / "user.css"
SRC_PALETTE = ROOT_DIR / "config" / "brand_palette.json"

DST_USER_CSS = USER_DIR / "user.css"
DST_PALETTE = USER_DIR / "brand_palette.json"


# ============================================================
# Helpers
# ============================================================

def comfyui_exists() -> bool:
    """Verifica que ComfyUI este instalado."""
    return COMFYUI_DIR.exists() and (COMFYUI_DIR / "main.py").exists()


def ensure_user_dir():
    """Crea ComfyUI/user/default/ si no existe."""
    USER_DIR.mkdir(parents=True, exist_ok=True)


def read_settings() -> dict:
    """Lee comfy.settings.json."""
    if not COMFYUI_SETTINGS.exists():
        return {}
    try:
        with open(COMFYUI_SETTINGS, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def write_settings(data: dict):
    """Escribe comfy.settings.json."""
    ensure_user_dir()
    with open(COMFYUI_SETTINGS, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ============================================================
# Apply theme
# ============================================================

def apply_user_css():
    """Copia user.css a ComfyUI/user/default/."""
    if not SRC_USER_CSS.exists():
        error(f"No existe: {SRC_USER_CSS}")
        return False

    ensure_user_dir()
    shutil.copy2(SRC_USER_CSS, DST_USER_CSS)
    ok(f"user.css copiado a {DST_USER_CSS}")
    return True


def apply_color_palette():
    """Importa brand_palette.json en las settings de ComfyUI."""
    if not SRC_PALETTE.exists():
        error(f"No existe: {SRC_PALETTE}")
        return False

    # Leer paleta
    with open(SRC_PALETTE, "r", encoding="utf-8") as f:
        palette_data = json.load(f)

    # Leer settings actuales
    settings = read_settings()

    # ComfyUI guarda la paleta en "Comfy.ColorPalette"
    settings["Comfy.ColorPalette"] = palette_data.get("colors", {})

    # Activar nuevos features del frontend (si disponibles)
    settings["Comfy.NodeColors.Default"] = True
    settings["Comfy.LinkRenderMode"] = 2  # splines suaves
    settings["Comfy.Graph.CanvasInfo"] = False  # ocultar info debug
    settings["Comfy.Graph.ZoomSpeed"] = 1.2

    write_settings(settings)
    ok(f"Paleta de marca aplicada a {COMFYUI_SETTINGS}")
    return True


def revert_theme():
    """Quita el tema y vuelve al default."""
    if DST_USER_CSS.exists():
        DST_USER_CSS.unlink()
        ok("user.css eliminado")
    else:
        info("user.css no existe (nada que revertir)")

    # Resetear paleta a default
    settings = read_settings()
    if "Comfy.ColorPalette" in settings:
        del settings["Comfy.ColorPalette"]
        write_settings(settings)
        ok("Paleta reseteada a default")
    else:
        info("Paleta ya era default")


def show_status():
    """Muestra estado actual del tema."""
    banner("ESTADO DEL TEMA")

    if not comfyui_exists():
        error("ComfyUI no instalado. Ejecuta install.bat primero.")
        return

    cprint(f"\nComfyUI: {COMFYUI_DIR}", '\033[96m')

    # user.css
    if DST_USER_CSS.exists():
        ok(f"user.css: INSTALADO ({DST_USER_CSS.stat().st_size} bytes)")
    else:
        warn("user.css: NO instalado")

    # Paleta
    settings = read_settings()
    if "Comfy.ColorPalette" in settings:
        ok("Color palette: de marca aplicada")
    else:
        info("Color palette: default")

    # Frontend
    frontend_version = settings.get("Comfy.Ui.Comfy-frontend-version", "default")
    info(f"Frontend version: {frontend_version}")

    # Custom nodes con temas
    themes_node = COMFYUI_DIR / "custom_nodes" / "ComfyUI-Niutonian-Themes"
    if themes_node.exists():
        ok("Niutonian Themes: INSTALADO")
    else:
        info("Niutonian Themes: no instalado (opcional)")


def recommend_niutonian():
    """Imprime instrucciones para instalar Niutonian Themes."""
    info("\nPara instalar temas adicionales (Niutonian):")
    cprint("  1. Abre ComfyUI en el navegador", '\033[96m')
    cprint("  2. Click en 'Manager'", '\033[96m')
    cprint("  3. 'Install Custom Nodes'", '\033[96m')
    cprint("  4. Busca 'Niutonian Themes'", '\033[96m')
    cprint("  5. Click 'Install' y restart", '\033[96m')
    cprint("  6. Settings -> Niutonian Themes -> 'Modern Dark'", '\033[96m')
    cprint("\n  O via CLI:", '\033[0m')
    cprint(f"  cd {COMFYUI_DIR}/custom_nodes && git clone https://github.com/Niutonian/ComfyUI-Niutonian-Themes.git", '\033[96m')


def verify_new_frontend():
    """Verifica/recomienda el nuevo frontend."""
    settings = read_settings()
    # ComfyUI nuevo frontend se activa con --front-end-version
    # Si no esta configurado, ComfyUI usa el nuevo por defecto desde nov 2024

    launch_args = ROOT_DIR / "config" / "launch_args.txt"
    if launch_args.exists():
        with open(launch_args, "r", encoding="utf-8") as f:
            content = f.read()
        if "--front-end-version" in content:
            ok("Nuevo frontend configurado en launch_args.txt")
        else:
            info("Frontend: usando default (nuevo por defecto desde nov 2024)")


# ============================================================
# Main
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Aplica tema de marca a ComfyUI")
    parser.add_argument("--revert", action="store_true",
                        help="Quitar tema (vuelve a default)")
    parser.add_argument("--status", action="store_true",
                        help="Mostrar estado actual del tema")
    parser.add_argument("--niutonian", action="store_true",
                        help="Mostrar instrucciones para instalar Niutonian Themes")
    args = parser.parse_args()

    if args.status:
        show_status()
        return

    if args.revert:
        banner("REVERTIR TEMA")
        revert_theme()
        return

    if args.niutonian:
        recommend_niutonian()
        return

    # Default: aplicar tema
    banner("APLICAR TEMA DE MARCA A COMFYUI")

    if not comfyui_exists():
        error("ComfyUI no instalado. Ejecuta install.bat / install.sh primero.")
        sys.exit(1)

    info("Aplicando tema de marca...")
    print()

    success = True
    success &= apply_user_css()
    success &= apply_color_palette()
    verify_new_frontend()

    print()
    if success:
        banner("TEMA APLICADO CORRECTAMENTE")
        cprint("  Reinicia ComfyUI para ver los cambios.", '\033[93m')
        cprint("  Si no se ve bien, fuerza refresh: Ctrl+Shift+R", '\033[0m')
        print()
        info("Para temas adicionales (Niutonian, Dracula, etc.):")
        cprint("  python apply_theme.py --niutonian", '\033[96m')
        print()
        info("Para revertir:")
        cprint("  python apply_theme.py --revert", '\033[96m')
    else:
        error("Algunos pasos fallaron. Revisa los errores arriba.")


if __name__ == "__main__":
    main()
