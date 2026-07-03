"""
cleanup_outputs.py - Limpia outputs antiguos de ComfyUI/output/

Elimina imagenes/videos generados hace mas de N dias.
OPCIONALMENTE preserva los que estan referenciados en calendar.json.

Uso:
    python cleanup_outputs.py                    # dry-run, muestra que eliminaria
    python cleanup_outputs.py --delete           # ejecuta la limpieza
    python cleanup_outputs.py --days 7 --delete  # elimina mayores a 7 dias
"""
import os
import sys
import json
import argparse
import time
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import cprint, info, ok, warn, error, banner, ROOT_DIR


OUTPUT_DIR = ROOT_DIR / "ComfyUI" / "output"
CALENDAR_FILE = ROOT_DIR / "config" / "calendar.json"


def get_referenced_files() -> set:
    """Devuelve el conjunto de nombres de archivo referenciados en calendar.json."""
    if not CALENDAR_FILE.exists():
        return set()

    try:
        with open(CALENDAR_FILE, "r", encoding="utf-8") as f:
            cal = json.load(f)
    except Exception:
        return set()

    referenced = set()
    for post in cal.get("posts", []):
        for path_str in post.get("image_paths", []):
            referenced.add(Path(path_str).name)
    return referenced


def main():
    parser = argparse.ArgumentParser(description="Limpieza de outputs antiguos")
    parser.add_argument("--days", type=int, default=30,
                        help="Eliminar archivos modificados hace mas de N dias (default 30)")
    parser.add_argument("--delete", action="store_true",
                        help="Ejecutar eliminacion (sin esto es dry-run)")
    parser.add_argument("--keep-referenced", action="store_true", default=True,
                        help="Preservar archivos referenciados en calendar.json (default True)")
    args = parser.parse_args()

    banner("LIMPIEZA DE OUTPUTS")

    if not OUTPUT_DIR.exists():
        info("Directorio output no existe. Nada que limpiar.")
        return 0

    referenced = get_referenced_files() if args.keep_referenced else set()
    if referenced:
        info(f"Preservando {len(referenced)} archivos referenciados en calendar.json")

    cutoff_time = time.time() - (args.days * 86400)
    files_to_delete = []
    total_size = 0

    for f in OUTPUT_DIR.iterdir():
        if not f.is_file():
            continue
        if f.name in referenced:
            continue
        mtime = f.stat().st_mtime
        if mtime < cutoff_time:
            files_to_delete.append(f)
            total_size += f.stat().st_size

    if not files_to_delete:
        ok("No hay archivos antiguos para limpiar.")
        return 0

    size_mb = total_size / (1024 * 1024)
    info(f"Archivos a eliminar: {len(files_to_delete)} ({size_mb:.1f} MB)")
    info(f"Anteriores a: {datetime.fromtimestamp(cutoff_time).isoformat()}")

    if not args.delete:
        cprint("\n  [DRY RUN] No se elimino nada. Usa --delete para ejecutar.",
               '\033[93m')
        # Mostrar primeros 10
        for f in files_to_delete[:10]:
            cprint(f"    {f.name}", '\033[90m')
        if len(files_to_delete) > 10:
            cprint(f"    ... y {len(files_to_delete) - 10} mas", '\033[90m')
        return 0

    # Ejecutar eliminacion
    deleted = 0
    for f in files_to_delete:
        try:
            f.unlink()
            deleted += 1
        except Exception as e:
            warn(f"No se pudo eliminar {f.name}: {e}")

    ok(f"Eliminados: {deleted}/{len(files_to_delete)} archivos")
    ok(f"Espacio liberado: {size_mb:.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
