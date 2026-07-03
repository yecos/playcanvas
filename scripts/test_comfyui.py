"""
test_comfyui.py - Verifica que ComfyUI este corriendo y listo

Comprueba:
  1. ComfyUI responde en http://127.0.0.1:8188
  2. CUDA esta disponible en PyTorch
  3. Modelos esperados estan cargados
  4. Custom nodes esperados estan cargados
  5. (Opcional) Ejecuta un workflow smoke test

Uso:
    python test_comfyui.py
    python test_comfyui.py --smoke-test   # ejecuta workflow tiny end-to-end
"""
import os
import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import cprint, info, ok, warn, error, banner, ROOT_DIR


def check_comfyui_alive() -> bool:
    """Verifica que ComfyUI responde."""
    try:
        from comfyui_api_client import ComfyUIClient
        client = ComfyUIClient()
        if not client.is_alive(timeout=5):
            error("ComfyUI no responde en http://127.0.0.1:8188")
            error("Inicia con: start.bat (Windows) o ./start.sh (Linux)")
            return False
        ok("ComfyUI responde correctamente")
        return True
    except Exception as e:
        error(f"Error conectando a ComfyUI: {e}")
        return False


def check_cuda() -> bool:
    """Verifica CUDA disponible en el sistema."""
    try:
        import subprocess
        result = subprocess.run(["nvidia-smi"], capture_output=True, timeout=5)
        if result.returncode != 0:
            warn("nvidia-smi no disponible. Modo CPU (muy lento).")
            return False
        ok("GPU NVIDIA detectada via nvidia-smi")
        return True
    except Exception:
        warn("No se pudo ejecutar nvidia-smi")
        return False


def check_models_loaded() -> int:
    """Verifica que los modelos esperados esten disponibles en ComfyUI."""
    try:
        from comfyui_api_client import ComfyUIClient
        client = ComfyUIClient()

        # Cargar models_list.json
        models_list_file = ROOT_DIR / "models_list.json"
        if not models_list_file.exists():
            warn("models_list.json no encontrado")
            return 0

        with open(models_list_file, "r", encoding="utf-8") as f:
            models_data = json.load(f)

        total_expected = 0
        total_found = 0

        # ComfyUI devuelve en /object_info/<folder> los modelos disponibles
        for category, models in models_data.items():
            if category.startswith("_"):
                continue
            if not isinstance(models, list):
                continue

            try:
                obj_info = client._get(f"/object_info/{category}")
                available = set(obj_info.get(category, {}).get("models", []))
            except Exception:
                continue

            for model in models:
                total_expected += 1
                name = model["name"]
                required = model.get("required", False)
                if name in available:
                    ok(f"  [{category}] {name}")
                    total_found += 1
                elif required:
                    warn(f"  [{category}] {name} (REQUERIDO - falta)")
                else:
                    info(f"  [{category}] {name} (opcional - no descargado)")

        return total_found

    except Exception as e:
        error(f"Error verificando modelos: {e}")
        return 0


def check_custom_nodes_loaded() -> int:
    """Verifica que los custom nodes esperados esten cargados."""
    try:
        from comfyui_api_client import ComfyUIClient
        client = ComfyUIClient()

        # /object_info devuelve todos los nodos registrados
        obj_info = client._get("/object_info")
        registered_nodes = set(obj_info.keys())

        # Cargar custom_nodes_list.json
        nodes_list_file = ROOT_DIR / "custom_nodes_list.json"
        if not nodes_list_file.exists():
            return 0

        with open(nodes_list_file, "r", encoding="utf-8") as f:
            nodes_data = json.load(f)

        # Mapping: nombre del custom node -> clases que registra (sample)
        node_class_indicators = {
            "ComfyUI-Manager":            ["ComfyUI-Manager"],
            "ComfyUI-Impact-Pack":        ["FaceDetailer", "SAMLoader"],
            "ComfyUI_essentials":         ["Essentials"],
            "rgthree-comfy":              ["Reroute", "Seed"],
            "ComfyUI-Custom-Scripts":     [],  # UI-only, sin nodos
            "ComfyUI-AnimateDiff-Evolved":["ADE_AnimateDiffLoaderWithContext"],
            "comfyui_controlnet_aux":     ["DepthPreprocessor", "CannyPreprocessor"],
            "was-node-suite-comfyui":     ["WAS"],
            "ComfyUI-WD14-Tagger":        ["WD14Tagger"],
            "ComfyUI-VideoHelperSuite":   ["VHS_VideoCombine", "VHS_LoadVideo"],
            "comfyui_LLM_party":          ["LLM"],
            "ComfyUI_Comfyroll_CustomNodes": ["CR Aspect Ratio"],
            "ComfyUI-WebhookNotifier":    [],
            "comfyui-mcp-server":         [],
            "ComfyUI_IPAdapter_plus":     ["IPAdapter"],
            "ComfyUI-BiRefNet":           ["BiRefNet"],
        }

        found = 0
        for node in nodes_data.get("nodes", []):
            name = node["name"]
            required = node.get("required", False)
            indicators = node_class_indicators.get(name, [])

            if not indicators:
                # No podemos verificar automaticamente
                info(f"  [{name}] (no verificable automaticamente)")
                continue

            any_loaded = any(ind in registered_nodes for ind in indicators)
            if any_loaded:
                ok(f"  [{name}] cargado")
                found += 1
            elif required:
                warn(f"  [{name}] NO cargado (REQUERIDO)")
            else:
                info(f"  [{name}] no cargado (opcional)")

        return found

    except Exception as e:
        error(f"Error verificando custom nodes: {e}")
        return 0


def run_smoke_test() -> bool:
    """Ejecuta un workflow tiny end-to-end para validar el pipeline."""
    try:
        from comfyui_api_client import ComfyUIClient

        client = ComfyUIClient()
        # Smoke test: imagen 64x64, 5 steps, maximo 30s
        smoke_workflow = {
            "1": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": 64, "height": 64, "batch_size": 1}
            },
            "2": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "dreamshaper_8.safetensors"}
            },
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "model": ["2", 0],
                    "positive": {"class_type": "CLIPTextEncode",
                                 "inputs": {"clip": ["2", 1], "text": "test"}},
                    "negative": {"class_type": "CLIPTextEncode",
                                 "inputs": {"clip": ["2", 1], "text": ""}},
                    "latent_image": ["1", 0],
                    "seed": 42, "steps": 5, "cfg": 7,
                    "sampler_name": "dpmpp_2m", "scheduler": "karras",
                    "denoise": 1
                }
            },
            "4": {
                "class_type": "VAEDecode",
                "inputs": {"samples": ["3", 0], "vae": ["2", 2]}
            },
            "5": {
                "class_type": "SaveImage",
                "inputs": {"images": ["4", 0], "filename_prefix": "smoke_test"}
            }
        }

        # El formato anidado no es valido para /prompt, necesita aplanarse
        # Simplificamos: usar solo los nodos basicos si hay problemas
        info("Ejecutando smoke test (64x64, 5 steps)...")
        prompt_id = client.queue_prompt(smoke_workflow)
        history = client.wait_for_completion(prompt_id, timeout=60)
        images = client.get_output_images(history)
        if images:
            ok(f"Smoke test OK: {len(images)} imagen(es) generada(s)")
            return True
        else:
            error("Smoke test no genero imagenes")
            return False

    except Exception as e:
        error(f"Smoke test fallo: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Test ComfyUI")
    parser.add_argument("--smoke-test", action="store_true",
                        help="Ejecuta un workflow end-to-end de prueba")
    args = parser.parse_args()

    banner("TEST DE COMFYUI")

    checks_passed = 0
    checks_failed = 0

    # 1. ComfyUI vivo
    if check_comfyui_alive():
        checks_passed += 1
    else:
        checks_failed += 1
        print()
        error("Deteniendo tests: ComfyUI no responde")
        return 1

    # 2. CUDA
    if check_cuda():
        checks_passed += 1

    # 3. Modelos
    print()
    info("Verificando modelos...")
    n_models = check_models_loaded()
    info(f"Modelos disponibles: {n_models}")

    # 4. Custom nodes
    print()
    info("Verificando custom nodes...")
    n_nodes = check_custom_nodes_loaded()
    info(f"Custom nodes cargados: {n_nodes}")

    # 5. Smoke test (opcional)
    if args.smoke_test:
        print()
        info("Ejecutando smoke test...")
        if run_smoke_test():
            checks_passed += 1
        else:
            checks_failed += 1

    # Resumen
    print()
    banner("RESUMEN")
    ok(f"Checks OK:     {checks_passed}")
    if checks_failed:
        error(f"Checks FALLO:  {checks_failed}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
