"""
brand_overlay.py - Aplica branding consistente a todas las imagenes generadas

Lee un brand_kit.yaml con:
  - Logo (path a PNG con transparencia)
  - Nombre de marca
  - Handle de redes sociales
  - Hashtags obligatorios
  - Colores primario/secundario
  - Fuente a usar

Y aplica overlay consistente:
  - Logo esquina inferior derecha (5% tamano, 70% opacity)
  - Handle de marca esquina inferior izquierda
  - Opcional: hashtags como texto en zona segura

Uso:
    from brand_overlay import apply_branding
    apply_branding("output.png", "output_branded.jpg")

    # Con config custom
    apply_branding("output.png", "output_branded.jpg",
                   brand_kit_path="config/my_brand_kit.yaml")

CLI:
    python brand_overlay.py --input output.png --output branded.jpg
    python brand_overlay.py --init  # crea brand_kit.yaml de ejemplo
"""
import os
import sys
import argparse
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import ROOT_DIR

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps
except ImportError:
    print("ERROR: Pillow no instalado. pip install Pillow")
    sys.exit(1)

try:
    import yaml
except ImportError:
    yaml = None  # Fallback a YAML manual parse

BRAND_KIT_PATH = ROOT_DIR / "config" / "brand_kit.yaml"

# ============================================================
# Brand kit loading
# ============================================================

DEFAULT_BRAND_KIT = {
    "brand_name": "Mi Marca",
    "handle": "@mimarca",
    "logo_path": None,  # path a PNG con transparencia
    "primary_color": "#FFFFFF",
    "secondary_color": "#000000",
    "font_family": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "font_size_handle": 24,
    "font_size_logo": 18,
    "hashtag_set": [],
    "watermark_opacity": 0.7,
    "watermark_position": "bottom-right",
    "margin": 30,
    "show_handle": True,
    "show_logo": True,
    "show_hashtags": False,
}


def load_brand_kit(path: Optional[str] = None) -> Dict:
    """Carga el brand_kit.yaml. Si no existe, devuelve defaults."""
    kit_path = Path(path) if path else BRAND_KIT_PATH

    if not kit_path.exists():
        return DEFAULT_BRAND_KIT.copy()

    try:
        if yaml:
            with open(kit_path, "r", encoding="utf-8") as f:
                user_kit = yaml.safe_load(f) or {}
        else:
            # Fallback: parse manual simple (lineas key: value)
            user_kit = {}
            with open(kit_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.split("#")[0].strip()
                    if ":" not in line:
                        continue
                    k, v = line.split(":", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if v.lower() in ("true", "false"):
                        v = v.lower() == "true"
                    elif v.isdigit():
                        v = int(v)
                    elif v.startswith("[") and v.endswith("]"):
                        v = [x.strip().strip('"').strip("'")
                             for x in v[1:-1].split(",") if x.strip()]
                    user_kit[k] = v
    except Exception as e:
        print(f"WARN: Error leyendo brand_kit: {e}. Usando defaults.")
        return DEFAULT_BRAND_KIT.copy()

    # Merge con defaults
    kit = DEFAULT_BRAND_KIT.copy()
    kit.update(user_kit)
    return kit


def save_default_brand_kit(path: Optional[str] = None):
    """Crea un brand_kit.yaml de ejemplo."""
    kit_path = Path(path) if path else BRAND_KIT_PATH

    content = """# Brand Kit - Configuracion de marca para ComfyUI Social Suite
# Edita estos valores con la identidad de tu marca

# Nombre de la marca (no se muestra por defecto)
brand_name: "Mi Marca"

# Handle de Instagram/TikTok/Twitter (se muestra esquina inf-izq)
handle: "@mimarca"

# Path al logo PNG con transparencia (recomendado 512x512)
# Si no tienes logo, dejalo como null y se usara solo el handle de texto
logo_path: null

# Colores de marca
primary_color: "#FFFFFF"   # texto principal
secondary_color: "#000000" # sombra/fondo

# Fuente TrueType (.ttf) - busca en /usr/share/fonts o C:\\Windows\\Fonts
# Recomendado: Montserrat-Bold, Poppins-Bold, o Inter-Bold
font_family: "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# Tamano de fuente
font_size_handle: 24
font_size_logo: 18

# Hashtags que se anaden automaticamente al final del caption
# (no se muestran en la imagen, solo en el caption)
hashtag_set:
  - "#aiart"
  - "#digitalart"

# Configuracion del watermark
watermark_opacity: 0.7       # 0.0 - 1.0
watermark_position: "bottom-right"  # bottom-right | bottom-left | top-right | top-left
margin: 30                    # pixels desde el borde

# Que elementos mostrar
show_handle: true
show_logo: true
show_hashtags: false          # mostrar hashtags como overlay en imagen
"""

    kit_path.parent.mkdir(parents=True, exist_ok=True)
    with open(kit_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Brand kit creado: {kit_path}")
    print("Edita este archivo con la identidad de tu marca.")


# ============================================================
# Color helpers
# ============================================================

def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convierte #RRGGBB a (r, g, b)."""
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def hex_to_rgba(hex_color: str, alpha: int = 255) -> Tuple[int, int, int, int]:
    """Convierte #RRGGBB a (r, g, b, a)."""
    r, g, b = hex_to_rgb(hex_color)
    return (r, g, b, alpha)


# ============================================================
# Overlay functions
# ============================================================

def add_logo_watermark(img: Image.Image, logo_path: str,
                       position: str = "bottom-right",
                       opacity: float = 0.7,
                       margin: int = 30,
                       size_percent: float = 0.05) -> Image.Image:
    """Anade logo como watermark."""
    if not Path(logo_path).exists():
        return img

    logo = Image.open(logo_path).convert("RGBA")
    # Tamano: 5% del ancho de la imagen
    logo_w = int(img.width * size_percent)
    logo_h = int(logo.height * (logo_w / logo.width))
    logo = logo.resize((logo_w, logo_h), Image.LANCZOS)

    # Aplicar opacity
    r, g, b, a = logo.split()
    a = a.point(lambda x: int(x * opacity))
    logo.putalpha(a)

    # Posicionar
    positions = {
        "top-left":     (margin, margin),
        "top-right":    (img.width - logo_w - margin, margin),
        "bottom-left":  (margin, img.height - logo_h - margin),
        "bottom-right": (img.width - logo_w - margin, img.height - logo_h - margin),
    }
    pos = positions.get(position, positions["bottom-right"])

    img.paste(logo, pos, logo)
    return img


def add_text_handle(img: Image.Image, handle: str,
                    font_path: str, font_size: int,
                    primary_color: str, secondary_color: str,
                    position: str = "bottom-left",
                    margin: int = 30) -> Image.Image:
    """Anade handle de marca como texto con sombra."""
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype(font_path, font_size)
    except Exception:
        font = ImageFont.load_default()
        # try Windows fallback
        win_path = "C:\\Windows\\Fonts\\arialbd.ttf"
        if Path(win_path).exists():
            try:
                font = ImageFont.truetype(win_path, font_size)
            except Exception:
                pass

    # Calcular tamano del texto
    bbox = draw.textbbox((0, 0), handle, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    positions = {
        "top-left":     (margin, margin),
        "top-right":    (img.width - text_w - margin, margin),
        "bottom-left":  (margin, img.height - text_h - margin),
        "bottom-right": (img.width - text_w - margin, img.height - text_h - margin),
    }
    pos = positions.get(position, positions["bottom-left"])

    # Sombra (offset 2px)
    shadow_color = hex_to_rgb(secondary_color)
    draw.text((pos[0] + 2, pos[1] + 2), handle, fill=shadow_color, font=font)

    # Texto principal
    text_color = hex_to_rgb(primary_color)
    draw.text(pos, handle, fill=text_color, font=font)

    return img


def add_hashtags_overlay(img: Image.Image, hashtags: list,
                         font_path: str, font_size: int = 18,
                         primary_color: str = "#FFFFFF",
                         margin: int = 30) -> Image.Image:
    """Anade hashtags como texto pequeno en zona segura inferior."""
    if not hashtags:
        return img

    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(font_path, font_size)
    except Exception:
        font = ImageFont.load_default()

    hashtags_text = " ".join(hashtags)
    bbox = draw.textbbox((0, 0), hashtags_text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    # Posicionar: parte inferior centrada
    x = (img.width - text_w) // 2
    y = img.height - text_h - margin - 40

    # Sombra
    draw.text((x + 1, y + 1), hashtags_text, fill=(0, 0, 0), font=font)
    # Texto
    draw.text((x, y), hashtags_text, fill=hex_to_rgb(primary_color), font=font)

    return img


# ============================================================
# Main function: apply_branding
# ============================================================

def apply_branding(input_path: str, output_path: Optional[str] = None,
                   brand_kit_path: Optional[str] = None,
                   format: str = "JPEG") -> str:
    """
    Aplica branding completo a una imagen.
    Devuelve la ruta del archivo de salida.
    """
    if output_path is None:
        p = Path(input_path)
        output_path = str(p.parent / f"{p.stem}_branded.jpg")

    kit = load_brand_kit(brand_kit_path)

    # Cargar imagen
    img = Image.open(input_path).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))

    # 1. Logo watermark
    if kit["show_logo"] and kit["logo_path"]:
        try:
            overlay = add_logo_watermark(
                overlay, kit["logo_path"],
                position=kit["watermark_position"],
                opacity=kit["watermark_opacity"],
                margin=kit["margin"]
            )
        except Exception as e:
            print(f"WARN: No se pudo aplicar logo: {e}")

    # Composite logo sobre imagen
    img = Image.alpha_composite(img, overlay).convert("RGB")

    # 2. Handle de marca
    if kit["show_handle"] and kit["handle"]:
        # Position opuesto al logo
        handle_pos = "bottom-left" if kit["watermark_position"] == "bottom-right" else "bottom-right"
        img = add_text_handle(
            img, kit["handle"],
            font_path=kit["font_family"],
            font_size=kit["font_size_handle"],
            primary_color=kit["primary_color"],
            secondary_color=kit["secondary_color"],
            position=handle_pos,
            margin=kit["margin"]
        )

    # 3. Hashtags (opcional, off por defecto)
    if kit["show_hashtags"] and kit["hashtag_set"]:
        img = add_hashtags_overlay(
            img, kit["hashtag_set"],
            font_path=kit["font_family"],
            font_size=kit["font_size_logo"],
            primary_color=kit["primary_color"],
            margin=kit["margin"]
        )

    # Guardar
    img.save(output_path, format=format, quality=92)
    return output_path


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Aplica branding a imagenes")
    parser.add_argument("--input", "-i", help="Imagen de entrada")
    parser.add_argument("--output", "-o", help="Imagen de salida")
    parser.add_argument("--brand-kit", "-b", help="Path a brand_kit.yaml custom")
    parser.add_argument("--init", action="store_true",
                        help="Crear brand_kit.yaml de ejemplo")
    args = parser.parse_args()

    if args.init:
        save_default_brand_kit()
        return

    if not args.input:
        parser.error("--input es requerido (o usa --init)")

    out = apply_branding(args.input, args.output, args.brand_kit)
    print(f"Branding aplicado: {out}")


if __name__ == "__main__":
    main()
