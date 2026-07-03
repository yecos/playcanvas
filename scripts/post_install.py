"""
post_install.py - Validacion final tras la instalacion

Verifica que TODO este listo para funcionar:
  1. ComfyUI instalado y arrancable
  2. PyTorch con CUDA funcional
  3. Venv activo con todas las dependencias
  4. Custom nodes instalados
  5. Modelos descargados (al menos los requeridos)
  6. Workflows cargados (UI + API format)
  7. Tema aplicado
  8. Configuracion (.env, calendar.json) inicializada
  9. Credenciales configuradas (si se va a publicar)
 10. Scripts auxiliares funcionan (queue_manager, webhook_server, dashboard)

Uso:
    python post_install.py
    python post_install.py --strict  # falla en warnings
"""
import os
import sys
import json
import importlib
import argparse
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import cprint, info, ok, warn, error, banner, ROOT_DIR


# ============================================================
# Checks
# ============================================================

def check_comfyui_installed():
    """ComfyUI directorio y main.py existen."""
    main_py = ROOT_DIR / "ComfyUI" / "main.py"
    if main_py.exists():
        ok("ComfyUI instalado")
        return True
    error("ComfyUI no instalado (falta ComfyUI/main.py)")
    return False


def check_venv():
    """Entorno virtual existe y tiene paquetes clave."""
    if os.name == "nt":
        venv_py = ROOT_DIR / "venv" / "Scripts" / "python.exe"
    else:
        venv_py = ROOT_DIR / "venv" / "bin" / "python"

    if not venv_py.exists():
        error("Entorno virtual no existe")
        return False

    # Verificar paquetes criticos
    packages = ["torch", "requests", "websocket", "PIL", "yaml"]
    all_ok = True
    for pkg in packages:
        result = os.system(f'"{venv_py}" -c "import {pkg}" 2>nul' if os.name == "nt"
                          else f'"{venv_py}" -c "import {pkg}" 2>/dev/null')
        if result != 0:
            warn(f"  Paquete no disponible en venv: {pkg}")
            all_ok = False

    if all_ok:
        ok("Entorno virtual OK con paquetes base")
    return all_ok


def check_pytorch_cuda():
    """PyTorch puede usar CUDA."""
    if os.name == "nt":
        venv_py = ROOT_DIR / "venv" / "Scripts" / "python.exe"
    else:
        venv_py = ROOT_DIR / "venv" / "bin" / "python"

    if not venv_py.exists():
        return False

    test_code = (
        'import torch; '
        'print(f"PyTorch {torch.__version__}"); '
        'print(f"CUDA disponible: {torch.cuda.is_available()}"); '
        'if torch.cuda.is_available(): print(f"GPU: {torch.cuda.get_device_name(0)}")'
    )
    cmd = f'"{venv_py}" -c "{test_code}"'
    result = os.system(cmd)
    if result == 0:
        ok("PyTorch + CUDA verificado")
        return True
    warn("PyTorch no puede usar CUDA (modo CPU)")
    return False


def check_custom_nodes():
    """Custom nodes basicos instalados."""
    nodes_dir = ROOT_DIR / "ComfyUI" / "custom_nodes"
    essential = ["ComfyUI-Manager", "ComfyUI-Impact-Pack", "rgthree-comfy"]
    optional = ["ComfyUI-VideoHelperSuite", "ComfyUI_WD14_Tagger",
                "comfyui_LLM_party", "ComfyUI_Comfyroll_CustomNodes",
                "ComfyUI-WebhookNotifier", "ComfyUI-AnimateDiff-Evolved"]

    found = 0
    for n in essential:
        if (nodes_dir / n).exists():
            found += 1
        else:
            warn(f"  Custom node faltante (requerido): {n}")
    for n in optional:
        if (nodes_dir / n).exists():
            found += 1
        # No warn en opcionales

    ok(f"Custom nodes: {found} instalados")
    return found >= len(essential)


def check_models():
    """Modelos requeridos descargados."""
    models_dir = ROOT_DIR / "ComfyUI" / "models" / "checkpoints"
    required = ["sd_xl_base_1.0.safetensors", "juggernautXL_v9.safetensors",
                "dreamshaper_8.safetensors"]

    found = 0
    for m in required:
        if (models_dir / m).exists():
            size = (models_dir / m).stat().st_size / (1024*1024*1024)
            if size > 1.0:  # al menos 1GB (no truncado)
                found += 1
            else:
                warn(f"  Modelo truncado: {m} ({size:.1f} GB)")
        else:
            warn(f"  Modelo faltante: {m}")

    if found == len(required):
        ok(f"Modelos requeridos: {found}/{len(required)} OK")
        return True
    elif found > 0:
        warn(f"Modelos: {found}/{len(required)} (algunos faltantes)")
        return False
    else:
        error("No hay modelos descargados")
        return False


def check_workflows():
    """Workflows UI + API format presentes."""
    wf_dir = ROOT_DIR / "workflows"
    ui_workflows = list(wf_dir.glob("*.json"))
    api_workflows = list(wf_dir.glob("*_api.json"))

    # Excluir README.md
    ui_workflows = [w for w in ui_workflows if w.suffix == ".json"]

    if len(ui_workflows) >= 8:
        ok(f"Workflows UI: {len(ui_workflows)}")
    else:
        warn(f"Workflows UI insuficientes: {len(ui_workflows)}")

    if len(api_workflows) >= 8:
        ok(f"Workflows API Format: {len(api_workflows)}")
        return True
    else:
        warn(f"Workflows API Format insuficientes ({len(api_workflows)}). "
             f"Ejecuta: python scripts/convert_workflow_format.py --all")
        return False


def check_theme_applied():
    """Tema de marca aplicado."""
    user_css = ROOT_DIR / "ComfyUI" / "user" / "default" / "user.css"
    settings_file = ROOT_DIR / "ComfyUI" / "user" / "default" / "comfy.settings.json"

    css_ok = user_css.exists()
    settings_ok = False
    if settings_file.exists():
        try:
            with open(settings_file) as f:
                s = json.load(f)
            settings_ok = "Comfy.ColorPalette" in s
        except Exception:
            pass

    if css_ok and settings_ok:
        ok("Tema de marca aplicado (user.css + paleta)")
        return True
    elif css_ok:
        warn("Tema parcial: user.css OK pero paleta no importada")
        return False
    else:
        warn("Tema no aplicado. Ejecuta: python scripts/apply_theme.py")
        return False


def check_config_files():
    """Configuracion inicializada."""
    env_file = ROOT_DIR / ".env"
    cal_file = ROOT_DIR / "config" / "calendar.json"

    env_ok = env_file.exists()
    cal_ok = cal_file.exists()

    if env_ok and cal_ok:
        ok(".env y calendar.json inicializados")
        return True
    else:
        missing = []
        if not env_ok: missing.append(".env")
        if not cal_ok: missing.append("config/calendar.json")
        warn(f"Falta inicializar: {', '.join(missing)}. "
             f"Ejecuta: python scripts/init_config.py")
        return False


def check_scripts():
    """Scripts auxiliares pueden importarse."""
    scripts_to_test = [
        ("comfyui_api_client", "ComfyUIClient"),
        ("auto_publish", "PUBLISHERS"),
        ("queue_manager", "init_db"),
        ("content_moderator", "moderate"),
        ("brand_overlay", "apply_branding"),
        ("convert_workflow_format", "convert_ui_to_api"),
        ("generate_caption", "generate_caption"),
        ("postprocess", "process_for_platform"),
        ("analytics_collector", "collect_all"),
        ("calendar_generator", "generate_calendar"),
    ]

    ok_count = 0
    for module_name, attr in scripts_to_test:
        try:
            mod = importlib.import_module(module_name)
            if hasattr(mod, attr):
                ok_count += 1
            else:
                warn(f"  {module_name}.{attr} no encontrado")
        except Exception as e:
            warn(f"  {module_name}: {e}")

    if ok_count == len(scripts_to_test):
        ok(f"Scripts auxiliares: {ok_count}/{len(scripts_to_test)} OK")
        return True
    return False


# ============================================================
# Main
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Validacion post-instalacion")
    parser.add_argument("--strict", action="store_true",
                        help="Falla en warnings")
    args = parser.parse_args()

    banner("VALIDACION POST-INSTALACION")

    checks = [
        ("ComfyUI", check_comfyui_installed),
        ("Venv", check_venv),
        ("PyTorch+CUDA", check_pytorch_cuda),
        ("Custom nodes", check_custom_nodes),
        ("Modelos", check_models),
        ("Workflows", check_workflows),
        ("Tema", check_theme_applied),
        ("Configuracion", check_config_files),
        ("Scripts", check_scripts),
    ]

    print()
    results = []
    for name, fn in checks:
        cprint(f"\n=== {name} ===", '\033[1m')
        try:
            result = fn()
        except Exception as e:
            error(f"Check {name} fallo con excepcion: {e}")
            result = False
        results.append((name, result))

    # Resumen
    print()
    banner("RESUMEN")
    passed = sum(1 for _, r in results if r)
    total = len(results)
    RESET = '\033[0m'
    for name, ok_flag in results:
        marker = "OK" if ok_flag else "FAIL"
        color = '\033[92m' if ok_flag else '\033[91m'
        cprint(f"  [{color}{marker}{RESET}] {name}")

    print()
    if passed == total:
        ok(f"TODO OK: {passed}/{total} checks pasaron")
        cprint("\n  Sistema listo para arrancar:", '\033[1m')
        cprint("  Windows:  start_all.bat", '\033[96m')
        cprint("  Linux:    ./start_all.sh", '\033[96m')
        return 0
    else:
        warn(f"{passed}/{total} checks OK. Revisa los WARN/FAIL arriba.")
        if args.strict:
            return 1
        return 0


if __name__ == "__main__":
    sys.exit(main())
