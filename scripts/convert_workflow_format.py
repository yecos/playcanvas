"""
convert_workflow_format.py - Convierte workflows de ComfyUI UI Format a API Format

ComfyUI guarda workflows en dos formatos:
  - UI Format: { "nodes": [...], "links": [...], "last_node_id": N, ... }
  - API Format: { "1": {"class_type": "...", "inputs": {...}}, "2": {...}, ... }

La API /prompt de ComfyUI SOLO acepta API Format. Este script convierte automaticamente.

Uso:
    python convert_workflow_format.py workflows/instagram_post.json
    python convert_workflow_format.py workflows/instagram_post.json --output workflows/instagram_post_api.json
    python convert_workflow_format.py --all           # convertir todos
    python convert_workflow_format.py --all --check    # solo verificar, no escribir
"""
import json
import os
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def is_ui_format(data: Dict) -> bool:
    """Detecta si un workflow esta en formato UI."""
    return isinstance(data.get("nodes"), list)


def is_api_format(data: Dict) -> bool:
    """Detecta si un workflow esta en formato API."""
    if not data:
        return False
    for k, v in data.items():
        if k.startswith("_") or k in ("last_node_id", "last_link_id", "version"):
            continue
        if not isinstance(v, dict):
            return False
        if "class_type" not in v:
            return False
    return True


def convert_ui_to_api(ui: Dict) -> Dict:
    """
    Convierte un workflow de UI Format a API Format.

    UI Format:
      { "nodes": [{"id":1,"type":"X","widgets_values":[...],"inputs":[...],"outputs":[...]}],
        "links": [[link_id, src_node, src_slot, dst_node, dst_slot, type], ...] }

    API Format:
      { "1": {"class_type": "X", "inputs": {"widget_name": value, "input_name": [src_node, src_slot]}} }
    """
    if not is_ui_format(ui):
        if is_api_format(ui):
            return ui  # ya esta en API format
        raise ValueError("Workflow no reconocido como UI ni API format")

    nodes = ui.get("nodes", [])
    links = ui.get("links", [])

    # Indexar links por (dst_node, dst_slot) -> (src_node, src_slot)
    # Cada link: [link_id, src_node_id, src_slot, dst_node_id, dst_slot, type]
    link_map = {}
    for link in links:
        if len(link) < 6:
            continue
        link_id, src_node, src_slot, dst_node, dst_slot, link_type = link[:6]
        link_map[(dst_node, dst_slot)] = (src_node, src_slot)

    api = {}
    for node in nodes:
        node_id = str(node["id"])
        class_type = node["type"]
        api[node_id] = {
            "class_type": class_type,
            "inputs": {},
            "_meta": {
                "title": node.get("title", class_type),
            }
        }

        # Inputs con conexiones (edges)
        # En UI format, "inputs" del nodo tiene: [{"name": "model", "link": link_id, "type": "MODEL"}, ...]
        node_inputs = node.get("inputs", []) or []
        for inp in node_inputs:
            inp_name = inp.get("name")
            inp_link = inp.get("link")
            if inp_link is None:
                continue
            # Buscar el link correspondiente
            for link in links:
                if len(link) < 6:
                    continue
                if link[0] == inp_link:
                    src_node, src_slot = link[1], link[2]
                    api[node_id]["inputs"][inp_name] = [str(src_node), src_slot]
                    break

        # Widgets values (valores literales de los widgets del nodo)
        # En UI format: node["widgets_values"] es una lista en el orden del widget
        # En API format: deben mapearse a los nombres de inputs del class_type
        widgets_values = node.get("widgets_values", []) or []
        if widgets_values:
            widget_inputs = map_widgets_to_inputs(class_type, widgets_values)
            for name, value in widget_inputs.items():
                if name not in api[node_id]["inputs"]:  # no sobrescribir conexiones
                    api[node_id]["inputs"][name] = value

    return api


# Mapeo de class_type -> lista ordenada de nombres de widgets
# Esto normalmente se obtiene de /object_info, pero aqui hardcodeamos los comunes
WIDGET_NAMES_BY_CLASS = {
    "CheckpointLoaderSimple": ["ckpt_name"],
    "CLIPTextEncode": ["text"],
    "EmptyLatentImage": ["width", "height", "batch_size"],
    "KSampler": ["seed", "control_after_generate", "steps", "cfg", "sampler_name", "scheduler", "denoise"],
    "VAEDecode": [],
    "VAEEncode": [],
    "SaveImage": ["filename_prefix"],
    "LoadImage": ["image"],
    "LoraLoader": ["lora_name", "strength_model", "strength_clip"],
    "UpscaleModelLoader": ["model_name"],
    "ImageUpscaleWithModel": [],
    "Note": ["text"],
    "PreviewImage": [],
    "ControlNetLoader": ["control_net_name"],
    "ControlNetApply": ["strength", "start_percent", "end_percent"],
    "ControlNetApplyAdvanced": ["strength", "start_percent", "end_percent"],
    "CR Aspect Ratio Social Media": ["width_height", "swap_axis", "batch_size"],
    "CR Overlay Text": ["text", "text_color", "font_name", "font_size", "align"],
    "AnimateDiffLoader": ["model_name", "beta_schedule", "motion_model_settings"],
    "VHS_VideoCombine": ["frame_rate", "loop_count", "filename_prefix", "format", "pix_fmt", "save_metadata"],
}


def map_widgets_to_inputs(class_type: str, widgets_values: List) -> Dict[str, Any]:
    """
    Mapea la lista widgets_values a un dict {input_name: value}
    usando el orden definido en WIDGET_NAMES_BY_CLASS.

    Si la clase no esta mapeada, usamos indices numericos como fallback.
    """
    widget_names = WIDGET_NAMES_BY_CLASS.get(class_type)
    if not widget_names:
        # Fallback: indexar numericamente
        return {f"widget_{i}": v for i, v in enumerate(widgets_values)}

    result = {}
    for i, name in enumerate(widget_names):
        if i < len(widgets_values):
            value = widgets_values[i]
            # Saltar valores None (widgets no presentes)
            if value is not None:
                result[name] = value
    return result


def convert_file(input_path: str, output_path: Optional[str] = None,
                 check_only: bool = False) -> Tuple[bool, str]:
    """
    Convierte un archivo workflow.
    Devuelve (success, message).
    """
    p = Path(input_path)
    if not p.exists():
        return False, f"No encontrado: {input_path}"

    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return False, f"JSON invalido: {e}"

    if is_api_format(data):
        return True, f"Ya en API format: {p.name}"

    if not is_ui_format(data):
        return False, f"Formato no reconocido: {p.name}"

    try:
        api = convert_ui_to_api(data)
    except Exception as e:
        return False, f"Error convirtiendo {p.name}: {e}"

    if check_only:
        return True, f"OK (check-only): {p.name} -> {len(api)} nodos"

    # Determinar ruta de salida
    if output_path is None:
        # Por defecto: <name>_api.json en el mismo dir
        out = p.parent / f"{p.stem}_api.json"
    else:
        out = Path(output_path)

    with open(out, "w", encoding="utf-8") as f:
        json.dump(api, f, indent=2, ensure_ascii=False)

    return True, f"Convertido: {p.name} -> {out.name} ({len(api)} nodos)"


def main():
    parser = argparse.ArgumentParser(
        description="Convierte workflows ComfyUI de UI Format a API Format"
    )
    parser.add_argument("input", nargs="?", help="Archivo workflow JSON")
    parser.add_argument("--output", "-o", help="Archivo de salida")
    parser.add_argument("--all", action="store_true",
                        help="Convertir todos los workflows en workflows/")
    parser.add_argument("--check", action="store_true",
                        help="Solo verificar, no escribir archivos")
    args = parser.parse_args()

    if args.all:
        workflows_dir = Path(__file__).resolve().parent.parent / "workflows"
        if not workflows_dir.exists():
            print(f"Directorio no encontrado: {workflows_dir}")
            sys.exit(1)

        results = []
        for wf in sorted(workflows_dir.glob("*.json")):
            if wf.name == "README.md" or wf.stem.endswith("_api"):
                continue
            ok, msg = convert_file(str(wf), check_only=args.check)
            results.append((ok, msg))
            status = "OK" if ok else "FAIL"
            print(f"  [{status}] {msg}")

        n_ok = sum(1 for ok, _ in results if ok)
        n_fail = sum(1 for ok, _ in results if not ok)
        print(f"\nTotal: {n_ok} OK, {n_fail} FAIL")
        sys.exit(0 if n_fail == 0 else 1)

    if not args.input:
        parser.print_help()
        sys.exit(1)

    ok, msg = convert_file(args.input, args.output, check_only=args.check)
    status = "OK" if ok else "FAIL"
    print(f"[{status}] {msg}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
