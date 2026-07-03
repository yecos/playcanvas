"""
init_config.py - Inicializa configuracion del usuario desde plantillas

Crea:
  - .env desde config/.env.example
  - config/calendar.json desde config/calendar_template.json
  - ComfyUI/extra_model_paths.yaml (si ComfyUI existe)

Uso:
    python init_config.py
"""
import os
import sys
import shutil
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import cprint, info, ok, warn, error, banner, ROOT_DIR


def copy_if_missing(src: Path, dst: Path, label: str) -> bool:
    """Copia src a dst si dst no existe. Devuelve True si hizo algo."""
    if not src.exists():
        error(f"Plantilla no encontrada: {src}")
        return False
    if dst.exists():
        info(f"{label} ya existe: {dst}")
        return False
    shutil.copy2(src, dst)
    ok(f"Creado: {dst}")
    return True


def main():
    banner("INICIALIZACION DE CONFIGURACION")

    created = []

    # 1. .env
    env_template = ROOT_DIR / "config" / ".env.example"
    env_target = ROOT_DIR / ".env"
    if copy_if_missing(env_template, env_target, ".env"):
        created.append(env_target)

    # 2. calendar.json
    cal_template = ROOT_DIR / "config" / "calendar_template.json"
    cal_target = ROOT_DIR / "config" / "calendar.json"
    if copy_if_missing(cal_template, cal_target, "calendar.json"):
        created.append(cal_target)

    # 3. extra_model_paths.yaml (si ComfyUI existe)
    comfyui_dir = ROOT_DIR / "ComfyUI"
    if comfyui_dir.exists():
        emp_template = ROOT_DIR / "config" / "extra_model_paths.yaml"
        emp_target = comfyui_dir / "extra_model_paths.yaml"
        if copy_if_missing(emp_template, emp_target, "extra_model_paths.yaml"):
            created.append(emp_target)

    # Resumen
    print()
    if created:
        banner("CONFIGURACION INICIALIZADA")
        for p in created:
            cprint(f"  ✓ {p}", '\033[92m')
        print()
        cprint("Proximos pasos:", '\033[1m')
        cprint(f"  1. Edita {ROOT_DIR / '.env'} con tus credenciales", '\033[0m')
        cprint(f"  2. Edita {ROOT_DIR / 'config' / 'calendar.json'} con tus posts", '\033[0m')
        cprint(f"  3. Valida con: python scripts/validate_config.py", '\033[0m')
        cprint(f"  4. Test ComfyUI: python scripts/test_comfyui.py", '\033[0m')
        cprint(f"  5. Ejecuta: python scripts/auto_publish.py --dry-run", '\033[0m')
        return 0
    else:
        info("Todo ya estaba inicializado. Edita los archivos existentes.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
