"""
download_models.py - Descarga todos los modelos necesarios
ComfyUI Social Media Suite (optimizado para RTX 3060 12GB)

Uso:
    python download_models.py             # Descarga todo
    python download_models.py --retry     # Reintenta los que fallaron
    python download_models.py --required  # Solo los marcados como required
    python download_models.py --list      # Solo lista, no descarga
    python download_models.py --category vae,checkpoints
"""
import os
import sys
import argparse
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import (
    cprint, info, ok, warn, error, banner,
    download_file, file_exists_with_size, load_json,
    MODELS_DIR, ROOT_DIR
)

MODELS_LIST = ROOT_DIR / "models_list.json"

# Mapa categoria -> subcarpeta de ComfyUI/models/
CATEGORY_PATHS = {
    "checkpoints":        MODELS_DIR / "checkpoints",
    "loras":              MODELS_DIR / "loras",
    "vae":                MODELS_DIR / "vae",
    "controlnet":         MODELS_DIR / "controlnet",
    "animatediff_models": MODELS_DIR / "animatediff_models",
    "upscale_models":     MODELS_DIR / "upscale_models",
    "embeddings":         MODELS_DIR / "embeddings",
    "clip_vision":        MODELS_DIR / "clip_vision",
    "text_encoders":      MODELS_DIR / "text_encoders",
    "diffusion_models":   MODELS_DIR / "diffusion_models",
}


def get_model_dest(category, filename):
    """Devuelve la ruta destino de un modelo."""
    base = CATEGORY_PATHS.get(category)
    if not base:
        warn(f"  Categoria desconocida: {category}")
        return None
    return base / filename


def download_model(model, category, retry=False, only_required=False):
    """Descarga un modelo si no existe."""
    name = model["name"]
    url = model["url"]
    size_gb = model.get("size_gb", 0)
    required = model.get("required", False)
    desc = model.get("description", "")
    headers = model.get("headers")

    if only_required and not required:
        return True  # Skip silenciosamente

    dest = get_model_dest(category, name)
    if not dest:
        return False

    info(f"[{category}] {name}")
    if desc:
        cprint(f"           {desc}", '\033[90m')
    cprint(f"           Tamano aprox: {size_gb} GB", '\033[90m')

    # Si ya existe con tamano minimo (al menos 1MB), skip
    if dest.exists() and dest.stat().st_size > 1024 * 1024:
        if retry:
            info(f"  Ya existe. Re-descargando (--retry)...")
        else:
            ok(f"  Ya existe. Saltando.")
            return True

    # Para CivitAI, el token de autorizacion se puede configurar via env var
    if headers and "Authorization" in headers:
        token = os.environ.get("CIVITAI_TOKEN", "")
        if token:
            headers = {"Authorization": f"Bearer {token}"}
        else:
            warn(f"  URL de CivitAI requiere token. Set CIVITAI_TOKEN env var.")
            warn(f"  Intentando sin token... (puede fallar)")

    success = download_file(url, dest, headers=headers, retries=3)
    if success:
        ok(f"  Descargado: {name}")
        return True
    else:
        if required:
            error(f"  FALLO (requerido): {name}")
        else:
            warn(f"  FALLO (opcional): {name}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Descargador de modelos")
    parser.add_argument("--retry", action="store_true",
                        help="Re-descargar incluso los existentes")
    parser.add_argument("--required", action="store_true",
                        help="Solo descargar modelos marcados como required")
    parser.add_argument("--list", action="store_true",
                        help="Solo listar modelos, no descargar")
    parser.add_argument("--category", type=str, default="",
                        help="Filtrar por categoria (comma-separated)")
    args = parser.parse_args()

    banner("DESCARGA DE MODELOS")

    if not MODELS_LIST.exists():
        error(f"No se encontro {MODELS_LIST}")
        return 1

    data = load_json(MODELS_LIST)

    # Filtrar categorias
    selected_categories = set()
    if args.category:
        selected_categories = set(args.category.split(","))
        info(f"Filtrando categorias: {selected_categories}")

    if not MODELS_DIR.exists():
        MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # Crear subcarpetas
    for cat, path in CATEGORY_PATHS.items():
        path.mkdir(parents=True, exist_ok=True)

    total = 0
    success = 0
    failed_required = 0
    failed_optional = 0
    total_size = 0

    print()
    for category, models in data.items():
        if category.startswith("_"):
            continue
        if selected_categories and category not in selected_categories:
            continue
        if not isinstance(models, list):
            continue

        for model in models:
            total += 1
            total_size += model.get("size_gb", 0)

            if args.list:
                name = model["name"]
                req = "[REQ]" if model.get("required") else "[opt]"
                size = model.get("size_gb", 0)
                cprint(f"  {req:5} {category:20} {name:45} {size:>5} GB",
                       '\033[96m')
                continue

            if download_model(model, category,
                              retry=args.retry,
                              only_required=args.required):
                success += 1
            else:
                if model.get("required"):
                    failed_required += 1
                else:
                    failed_optional += 1

    # ---- Resumen ----
    print()
    banner("RESUMEN DESCARGA MODELOS")
    cprint(f"  Total modelos procesados: {total}", '\033[96m')
    cprint(f"  Tamano total estimado:    {total_size:.1f} GB", '\033[96m')
    ok(f"  Descargas OK:             {success}")
    if failed_optional:
        warn(f"  Fallos opcionales:        {failed_optional}")
    if failed_required:
        error(f"  Fallos requeridos:        {failed_required}")
        error("  Reejecuta: python download_models.py --retry")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
