"""
validate_config.py - Valida que la configuracion este completa antes de ejecutar

Comprueba:
  - .env existe y no tiene placeholders
  - Variables requeridas por las plataformas que se van a usar
  - calendar.json existe y tiene estructura valida
  - Cada workflow referenciado existe
  - Cada plataforma referenciada esta soportada

Uso:
    python validate_config.py
    python validate_config.py --strict   # falla en cualquier warning
"""
import os
import sys
import argparse
from pathlib import Path
from typing import List, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import cprint, info, ok, warn, error, banner, ROOT_DIR

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Variables requeridas por plataforma
REQUIRED_ENV_BY_PLATFORM = {
    "instagram": ["IG_USERNAME", "IG_PASSWORD"],
    "twitter":   ["TWITTER_CONSUMER_KEY", "TWITTER_CONSUMER_SECRET",
                  "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_TOKEN_SECRET"],
    "facebook":  ["FB_PAGE_TOKEN", "FB_PAGE_ID"],
    "pinterest": ["PINTEREST_EMAIL", "PINTEREST_PASSWORD",
                  "PINTEREST_USERNAME", "PINTEREST_BOARD_ID"],
    "youtube":   ["YOUTUBE_CLIENT_SECRETS_FILE"],
    "tiktok":    ["TIKTOK_USERNAME", "TIKTOK_PASSWORD"],
}

# Placeholders del .env.example que NO deben quedar en .env
PLACEHOLDERS = {
    "tu_usuario_instagram", "tu_password_instagram",
    "cambia_esto_por_un_secreto_aleatorio",
    "", "1234567890", "123456789,987654321",
}


def check_env() -> Tuple[List[str], List[str]]:
    """Devuelve (errors, warnings)."""
    errors = []
    warnings = []

    env_file = ROOT_DIR / ".env"
    if not env_file.exists():
        errors.append(f".env no existe. Ejecuta: python scripts/init_config.py")
        return errors, warnings

    # Variables criticas (siempre)
    comfy_host = os.environ.get("COMFYUI_HOST", "127.0.0.1")
    comfy_port = os.environ.get("COMFYUI_PORT", "8188")
    if not comfy_host or not comfy_port:
        warnings.append("COMFYUI_HOST/PORT no definidos (usando defaults)")

    return errors, warnings


def check_calendar() -> Tuple[List[str], List[str]]:
    """Valida calendar.json."""
    errors = []
    warnings = []

    cal_file = ROOT_DIR / "config" / "calendar.json"
    if not cal_file.exists():
        errors.append(f"calendar.json no existe. Ejecuta: python scripts/init_config.py")
        return errors, warnings

    try:
        import json
        with open(cal_file, "r", encoding="utf-8") as f:
            cal = json.load(f)
    except Exception as e:
        errors.append(f"calendar.json invalido: {e}")
        return errors, warnings

    posts = cal.get("posts", [])
    if not posts:
        warnings.append("calendar.json no tiene posts")
        return errors, warnings

    # Validar cada post
    seen_ids = set()
    supported_platforms = set(REQUIRED_ENV_BY_PLATFORM.keys())

    for i, post in enumerate(posts):
        post_id = post.get("id", f"<sin id #{i}>")

        # Campos requeridos
        for field in ["id", "workflow", "prompt", "platforms"]:
            if field not in post:
                errors.append(f"Post {post_id}: falta campo '{field}'")

        if post_id in seen_ids:
            errors.append(f"Post ID duplicado: {post_id}")
        seen_ids.add(post_id)

        # Workflow existe?
        wf_name = post.get("workflow")
        if wf_name:
            wf_api = ROOT_DIR / "workflows" / f"{wf_name}_api.json"
            wf_ui = ROOT_DIR / "workflows" / f"{wf_name}.json"
            if not wf_api.exists() and not wf_ui.exists():
                errors.append(f"Post {post_id}: workflow '{wf_name}' no existe")

        # Plataformas soportadas?
        platforms = post.get("platforms", [])
        if not isinstance(platforms, list):
            errors.append(f"Post {post_id}: 'platforms' debe ser una lista")
        else:
            for p in platforms:
                if p not in supported_platforms:
                    errors.append(
                        f"Post {post_id}: plataforma '{p}' no soportada. "
                        f"Soportadas: {sorted(supported_platforms)}"
                    )

    return errors, warnings


def check_platform_credentials(platforms_used: set) -> Tuple[List[str], List[str]]:
    """Verifica que las credenciales para cada plataforma esten presentes."""
    errors = []
    warnings = []

    for platform in platforms_used:
        required = REQUIRED_ENV_BY_PLATFORM.get(platform, [])
        for var in required:
            value = os.environ.get(var, "")
            if not value or value in PLACEHOLDERS:
                errors.append(f"Plataforma {platform}: variable {var} no configurada en .env")

        # Casos especiales
        if platform == "youtube":
            secrets_file = Path(os.environ.get("YOUTUBE_CLIENT_SECRETS_FILE",
                                                "client_secret.json"))
            if not secrets_file.exists():
                errors.append(f"YouTube: falta archivo {secrets_file} (descarga OAuth credentials)")

    return errors, warnings


def main():
    parser = argparse.ArgumentParser(description="Valida configuracion")
    parser.add_argument("--strict", action="store_true",
                        help="Falla en warnings tambien")
    args = parser.parse_args()

    banner("VALIDACION DE CONFIGURACION")

    all_errors = []
    all_warnings = []

    # 1. .env
    e, w = check_env()
    all_errors.extend(e)
    all_warnings.extend(w)

    # 2. calendar.json
    e, w = check_calendar()
    all_errors.extend(e)
    all_warnings.extend(w)

    # 3. Credenciales por plataforma
    # Determinar plataformas usadas en el calendario
    try:
        import json
        cal_file = ROOT_DIR / "config" / "calendar.json"
        if cal_file.exists():
            with open(cal_file, "r", encoding="utf-8") as f:
                cal = json.load(f)
            platforms_used = set()
            for post in cal.get("posts", []):
                for p in post.get("platforms", []):
                    platforms_used.add(p)
            if platforms_used:
                e, w = check_platform_credentials(platforms_used)
                all_errors.extend(e)
                all_warnings.extend(w)
    except Exception as ex:
        all_errors.append(f"Error leyendo plataformas: {ex}")

    # Reporte
    print()
    if all_errors:
        cprint("ERRORES:", '\033[91m')
        for err in all_errors:
            cprint(f"  ✗ {err}", '\033[91m')
    if all_warnings:
        cprint("\nWARNINGS:", '\033[93m')
        for w in all_warnings:
            cprint(f"  ⚠ {w}", '\033[93m')

    print()
    if not all_errors and not all_warnings:
        ok("Configuracion valida. Listo para ejecutar auto_publish.py")
        return 0
    elif not all_errors:
        ok("Configuracion valida (con warnings)")
        return 0 if not args.strict else 1
    else:
        error(f"{len(all_errors)} errores encontrados. Corrigelos antes de continuar.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
