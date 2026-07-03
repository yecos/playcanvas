"""
postprocess.py - Post-procesamiento de imagenes antes de publicar

Funciones:
  - convert_to_jpeg(input, output, quality=92): PNG -> JPEG
  - strip_exif(path): elimina metadatos EXIF por privacidad
  - add_watermark(input, output, logo_path, position='bottom-right', opacity=0.7)
  - resize_for_platform(input, output, platform): dimensiones optimas por red
  - add_ai_label(input, output): anade etiqueta "Creado con IA" (Meta/TikTok compliance)

Uso:
    from postprocess import process_for_platform
    process_for_platform("output.png", "final.jpg", platform="instagram",
                         watermark="logo.png")
"""
import os
import sys
from pathlib import Path
from typing import Optional, Tuple

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps
except ImportError:
    print("ERROR: Pillow no instalado. pip install Pillow")
    sys.exit(1)


# Dimensiones optimas por plataforma (ancho, alto)
PLATFORM_SIZES = {
    "instagram_post":    (1080, 1080),  # 1:1
    "instagram_portrait":(1080, 1350),  # 4:5
    "instagram_story":   (1080, 1920),  # 9:16
    "tiktok":            (1080, 1920),  # 9:16
    "youtube_thumbnail": (1280, 720),   # 16:9
    "youtube_short":     (1080, 1920),  # 9:16
    "twitter":           (1200, 675),   # 16:9
    "facebook":          (1200, 630),   # 1.91:1
    "pinterest":         (1000, 1500),  # 2:3
    "linkedin":          (1200, 627),   # 1.91:1
}


def convert_to_jpeg(input_path: str, output_path: Optional[str] = None,
                    quality: int = 92, bg_color: Tuple[int, int, int] = (255, 255, 255)) -> str:
    """Convierte una imagen a JPEG (PNG con transparencia se rellena con bg_color)."""
    if output_path is None:
        p = Path(input_path)
        output_path = str(p.with_suffix(".jpg"))

    img = Image.open(input_path)
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        # Crear fondo blanco y pegar la imagen con transparencia
        bg = Image.new("RGB", img.size, bg_color)
        bg.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
        img = bg
    elif img.mode != "RGB":
        img = img.convert("RGB")

    img.save(output_path, "JPEG", quality=quality, optimize=True)
    return output_path


def strip_exif(path: str) -> None:
    """Elimina metadatos EXIF de una imagen (in-place)."""
    img = Image.open(path)
    data = list(img.getdata())
    img_no_exif = Image.new(img.mode, img.size)
    img_no_exif.putdata(data)
    img_no_exif.save(path, format=img.format or "JPEG", quality=92)


def add_watermark(input_path: str, output_path: str,
                  logo_path: Optional[str] = None,
                  text: Optional[str] = None,
                  position: str = "bottom-right",
                  opacity: float = 0.7,
                  margin: int = 20,
                  font_size: int = 32) -> str:
    """Anade watermark (logo o texto) a una imagen."""
    img = Image.open(input_path).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))

    if logo_path and Path(logo_path).exists():
        logo = Image.open(logo_path).convert("RGBA")
        # Calcular tamano del logo (5% del ancho de la imagen)
        logo_w = int(img.width * 0.05)
        logo_h = int(logo.height * (logo_w / logo.width))
        logo = logo.resize((logo_w, logo_h), Image.LANCZOS)
        # Aplicar opacity
        logo_with_alpha = Image.new("RGBA", logo.size, (0, 0, 0, 0))
        for x in range(logo.width):
            for y in range(logo.height):
                r, g, b, a = logo.getpixel((x, y))
                logo_with_alpha.putpixel((x, y), (r, g, b, int(a * opacity)))
        logo = logo_with_alpha

        # Posicionar
        positions = {
            "top-left":     (margin, margin),
            "top-right":    (img.width - logo_w - margin, margin),
            "bottom-left":  (margin, img.height - logo_h - margin),
            "bottom-right": (img.width - logo_w - margin, img.height - logo_h - margin),
            "center":       ((img.width - logo_w) // 2, (img.height - logo_h) // 2),
        }
        pos = positions.get(position, positions["bottom-right"])
        overlay.paste(logo, pos, logo)

    elif text:
        # Texto watermark
        draw = ImageDraw.Draw(overlay)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                                       font_size)
        except Exception:
            font = ImageFont.load_default()

        # Calcular tamano del texto
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        positions = {
            "top-left":     (margin, margin),
            "top-right":    (img.width - text_w - margin, margin),
            "bottom-left":  (margin, img.height - text_h - margin),
            "bottom-right": (img.width - text_w - margin, img.height - text_h - margin),
            "center":       ((img.width - text_w) // 2, (img.height - text_h) // 2),
        }
        pos = positions.get(position, positions["bottom-right"])
        # Semi-transparente
        alpha = int(255 * opacity)
        draw.text(pos, text, fill=(255, 255, 255, alpha), font=font)

    result = Image.alpha_composite(img, overlay).convert("RGB")
    result.save(output_path, "JPEG", quality=92)
    return output_path


def resize_for_platform(input_path: str, output_path: str,
                        platform: str = "instagram_post",
                        pad_mode: str = "cover") -> str:
    """
    Redimensiona la imagen al tamano optimo de la plataforma.
    pad_mode: 'cover' (recorta) o 'contain' (añade padding)
    """
    target_size = PLATFORM_SIZES.get(platform, PLATFORM_SIZES["instagram_post"])
    img = Image.open(input_path)

    if pad_mode == "cover":
        # Recortar al aspect ratio target
        img = ImageOps.fit(img, target_size, Image.LANCZOS)
    else:
        # Contain con padding
        img.thumbnail(target_size, Image.LANCZOS)
        new_img = Image.new("RGB", target_size, (255, 255, 255))
        x = (target_size[0] - img.width) // 2
        y = (target_size[1] - img.height) // 2
        new_img.paste(img, (x, y))
        img = new_img

    img.save(output_path, "JPEG", quality=92)
    return output_path


def add_ai_label(input_path: str, output_path: str,
                 label: str = "Creado con IA",
                 position: str = "bottom-left") -> str:
    """Anade etiqueta visible de contenido AI (cumplimiento Meta/TikTok)."""
    img = Image.open(input_path).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    try:
        font_size = max(16, img.width // 40)
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                                   font_size)
    except Exception:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), label, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    padding = 10

    positions = {
        "top-left":     (padding, padding),
        "top-right":    (img.width - text_w - padding * 3, padding),
        "bottom-left":  (padding, img.height - text_h - padding * 3),
        "bottom-right": (img.width - text_w - padding * 3, img.height - text_h - padding * 3),
    }
    pos = positions.get(position, positions["bottom-left"])

    # Fondo semi-negro
    draw.rectangle(
        [pos[0] - padding, pos[1] - padding,
         pos[0] + text_w + padding, pos[1] + text_h + padding],
        fill=(0, 0, 0, 180)
    )
    draw.text(pos, label, fill=(255, 255, 255, 255), font=font)

    result = Image.alpha_composite(img, overlay).convert("RGB")
    result.save(output_path, "JPEG", quality=92)
    return output_path


def process_for_platform(input_path: str, output_path: Optional[str] = None,
                         platform: str = "instagram_post",
                         watermark_logo: Optional[str] = None,
                         watermark_text: Optional[str] = None,
                         add_ai_tag: bool = False,
                         convert_jpeg: bool = True) -> str:
    """
    Pipeline completo de post-procesamiento para una plataforma.
    """
    if output_path is None:
        p = Path(input_path)
        output_path = str(p.parent / f"{p.stem}_{platform}.jpg")

    # 1. Redimensionar
    resize_for_platform(input_path, output_path, platform)

    # 2. Watermark
    if watermark_logo or watermark_text:
        wm_out = output_path.replace(".jpg", "_wm.jpg")
        add_watermark(output_path, wm_out,
                      logo_path=watermark_logo,
                      text=watermark_text)
        os.replace(wm_out, output_path)

    # 3. AI label
    if add_ai_tag:
        ai_out = output_path.replace(".jpg", "_ai.jpg")
        add_ai_label(output_path, ai_out)
        os.replace(ai_out, output_path)

    # 4. Strip EXIF
    strip_exif(output_path)

    return output_path


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Post-procesamiento de imagenes")
    parser.add_argument("input", help="Imagen de entrada")
    parser.add_argument("--platform", default="instagram_post",
                        choices=list(PLATFORM_SIZES.keys()))
    parser.add_argument("--watermark-logo", help="Logo para watermark")
    parser.add_argument("--watermark-text", help="Texto para watermark")
    parser.add_argument("--ai-label", action="store_true",
                        help="Anade etiqueta 'Creado con IA'")
    parser.add_argument("--output", "-o", help="Archivo de salida")
    args = parser.parse_args()

    out = process_for_platform(
        args.input, args.output, args.platform,
        watermark_logo=args.watermark_logo,
        watermark_text=args.watermark_text,
        add_ai_tag=args.ai_label
    )
    print(f"Procesado: {out}")
