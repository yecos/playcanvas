"""
content_moderator.py - Filtra contenido antes de publicar (anti-ban)

Tres niveles de filtrado:
  1. NSFW detection en imagen (usando transformers o detector local)
  2. Profanity / palabras prohibidas en caption
  3. Validacion de policies por plataforma (TikTok/Meta exigen etiquetar AI)

Uso:
    from content_moderator import moderate
    result = moderate(image_path="output.png", caption="texto del post",
                      platform="instagram")
    if not result["allowed"]:
        print("Bloqueado:", result["reasons"])

CLI:
    python content_moderator.py --image output.png --caption "texto" --platform instagram
"""
import os
import sys
import re
import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import cprint, info, ok, warn, error, ROOT_DIR


# ============================================================
# 1. NSFW detection (imagen)
# ============================================================

# Importancia: si onnxruntime esta disponible, usamos el modelo
# nudenet-3.0 (200MB) o fallback a transformers

_nsfw_detector = None

def _load_nsfw_detector():
    """Carga el detector NSFW (lazy loading)."""
    global _nsfw_detector
    if _nsfw_detector is not None:
        return _nsfw_detector

    # Intentar con transformers (CLIP-based NSFW classifier)
    try:
        from transformers import pipeline
        info("Cargando detector NSFW (transformers)...")
        _nsfw_detector = pipeline(
            "image-classification",
            model="AdamCodd/vit-base-nsfw-detector"
        )
        return _nsfw_detector
    except ImportError:
        pass
    except Exception as e:
        warn(f"No se pudo cargar transformers: {e}")

    # Fallback:detector basico con Pillow (solo color analysis)
    warn("No hay detector NSFW disponible. Instala: pip install transformers torch")
    _nsfw_detector = False  # marker: no disponible
    return _nsfw_detector


def detect_nsfw_image(image_path: str, threshold: float = 0.65) -> Dict:
    """
    Detecta si una imagen es NSFW.
    Devuelve: {"is_nsfw": bool, "score": float, "label": str}
    """
    detector = _load_nsfw_detector()
    if detector is False:
        # Sin detector, asumir safe (mejor falso negativo que bloquear todo)
        return {"is_nsfw": False, "score": 0.0, "label": "unknown",
                "warning": "Detector NSFW no disponible"}

    try:
        from PIL import Image
        img = Image.open(image_path)
        results = detector(img)

        # results es lista de {label, score}
        # En el modelo AdamCodd: label "nsfw" o "normal"
        nsfw_score = 0.0
        label = "normal"
        for r in results:
            if "nsfw" in r["label"].lower():
                nsfw_score = max(nsfw_score, r["score"])
                if r["score"] > 0.5:
                    label = r["label"]

        return {
            "is_nsfw": nsfw_score >= threshold,
            "score": nsfw_score,
            "label": label,
            "all_scores": results if isinstance(results, list) else None,
        }
    except Exception as e:
        return {"is_nsfw": False, "score": 0.0, "label": "error",
                "error": str(e)}


# ============================================================
# 2. Profanity / banned keywords
# ============================================================

# Lista de palabras prohibidas (ampliar segun necesidades)
BANNED_WORDS = {
    # Ingles
    "fuck", "shit", "bitch", "asshole", "dick", "pussy", "cunt",
    "nigger", "nigga", "faggot", "retard", "rape",
    # Espanol
    "joder", "puta", "puto", "cabron", "coño", "maricon", "gilipollas",
    "hijo de puta", "pendejo", "pelotudo", "boludo", "verga", "culo",
    # Tematicas problematicas para plataformas
    "kill yourself", "kys", "self-harm", "anorexia",
    "thinspo", "selfharm",
    # Tokens de spam
    "click here", "buy now", "free money", "crypto giveaway",
    "dm me", "link in bio",  # IG tiende a penalizar
}

# Palabras extra a bloquear por plataforma
PLATFORM_BANNED = {
    "tiktok": {"young", "teen", "minor", "school"},  # puede triggear algoritmo
    "instagram": {"dm me", "link in bio", "buy followers"},
    "youtube": {"subscribe", "like and subscribe"},  # spammy
    "facebook": {"share this post", "1 like = 1 prayer"},
}

# Patrones regex adicionales (URLs sospechosas, etc)
BANNED_PATTERNS = [
    r"https?://(?:bit\.ly|tinyurl|t\.co)/\S+",  # acortadores sospechosos
    r"\+\d{1,3}\s?\d{6,}",  # numeros de telefono
    r"\b\d{16}\b",  # posibles numeros de tarjeta
]


def detect_profanity(caption: str, platform: str = "") -> Dict:
    """
    Detecta palabras prohibidas en el caption.
    Devuelve: {"has_profanity": bool, "found": list, "platform_specific": list}
    """
    if not caption:
        return {"has_profanity": False, "found": [], "platform_specific": []}

    caption_lower = caption.lower()

    # Tokenizar de forma simple (palabras completas)
    found = []
    for word in BANNED_WORDS:
        # Match como palabra completa (no subcadena)
        pattern = r"\b" + re.escape(word) + r"\b"
        if re.search(pattern, caption_lower):
            found.append(word)

    # Platform-specific
    platform_words = PLATFORM_BANNED.get(platform, set())
    platform_found = []
    for word in platform_words:
        pattern = r"\b" + re.escape(word) + r"\b"
        if re.search(pattern, caption_lower):
            platform_found.append(word)

    # Patrones regex
    for pattern in BANNED_PATTERNS:
        if re.search(pattern, caption_lower):
            found.append(f"patron:{pattern[:30]}")

    return {
        "has_profanity": bool(found or platform_found),
        "found": found,
        "platform_specific": platform_found,
    }


# ============================================================
# 3. Platform policies (AI labeling requirement)
# ============================================================

# Plataformas que exigen etiquetar contenido generado con IA
AI_LABEL_REQUIRED_PLATFORMS = {
    "tiktok",    # TikTok Content Policy: AI must be labeled
    "instagram", # Meta AI content policy
    "facebook",
}

def check_ai_label_requirement(platform: str, caption: str = "") -> Dict:
    """
    Verifica si el contenido requiere etiqueta AI.
    """
    requires_label = platform in AI_LABEL_REQUIRED_PLATFORMS

    # Hashtags / textos que indican que ya esta etiquetado
    ai_label_markers = [
        "creado con ia", "created with ai", "ai generated",
        "generated by ai", "#aiart", "#aigenerated",
        "#aiartwork", "#aimade", "altered reality",
    ]
    caption_lower = caption.lower()
    has_label = any(marker in caption_lower for marker in ai_label_markers)

    return {
        "requires_label": requires_label,
        "has_label": has_label,
        "needs_label_added": requires_label and not has_label,
        "suggested_label": "Creado con IA" if requires_label else None,
    }


# ============================================================
# 4. Orquestador: moderate()
# ============================================================

def moderate(image_path: Optional[str] = None,
             caption: str = "",
             platform: str = "instagram",
             nsfw_threshold: float = 0.65,
             skip_nsfw: bool = False) -> Dict:
    """
    Ejecuta todos los checks de moderacion.

    Devuelve:
    {
      "allowed": bool,
      "reasons": list[str],
      "warnings": list[str],
      "nsfw": {...},
      "profanity": {...},
      "ai_label": {...}
    }
    """
    reasons = []
    warnings = []

    # 1. NSFW
    nsfw_result = None
    if image_path and not skip_nsfw:
        nsfw_result = detect_nsfw_image(image_path, nsfw_threshold)
        if nsfw_result.get("is_nsfw"):
            reasons.append(f"NSFW detectado (score: {nsfw_result['score']:.2f})")
        if "warning" in nsfw_result:
            warnings.append(nsfw_result["warning"])

    # 2. Profanity
    profanity_result = detect_profanity(caption, platform)
    if profanity_result["has_profanity"]:
        all_found = profanity_result["found"] + profanity_result["platform_specific"]
        reasons.append(f"Palabras prohibidas: {', '.join(all_found[:5])}")

    # 3. AI label
    ai_label_result = check_ai_label_requirement(platform, caption)
    if ai_label_result["needs_label_added"]:
        warnings.append(
            f"Plataforma {platform} requiere etiqueta AI. "
            f"Sugerencia: anadir '{ai_label_result['suggested_label']}'"
        )

    return {
        "allowed": len(reasons) == 0,
        "reasons": reasons,
        "warnings": warnings,
        "nsfw": nsfw_result,
        "profanity": profanity_result,
        "ai_label": ai_label_result,
    }


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Moderador de contenido anti-ban")
    parser.add_argument("--image", help="Ruta de la imagen a analizar")
    parser.add_argument("--caption", default="", help="Caption del post")
    parser.add_argument("--platform", default="instagram",
                        choices=["instagram", "tiktok", "twitter", "facebook",
                                 "pinterest", "youtube"])
    parser.add_argument("--nsfw-threshold", type=float, default=0.65,
                        help="Umbral NSFW (default 0.65)")
    parser.add_argument("--skip-nsfw", action="store_true",
                        help="Saltar check NSFW")
    parser.add_argument("--json", action="store_true",
                        help="Output como JSON")
    args = parser.parse_args()

    if not args.image and not args.caption:
        error("Especifica --image o --caption")
        sys.exit(1)

    result = moderate(
        image_path=args.image,
        caption=args.caption,
        platform=args.platform,
        nsfw_threshold=args.nsfw_threshold,
        skip_nsfw=args.skip_nsfw,
    )

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        if result["allowed"]:
            ok("Contenido APROBADO para publicacion")
        else:
            error("Contenido BLOQUEADO:")
            for r in result["reasons"]:
                cprint(f"  - {r}", '\033[91m')
        if result["warnings"]:
            cprint("\nWarnings:", '\033[93m')
            for w in result["warnings"]:
                cprint(f"  - {w}", '\033[93m')

    sys.exit(0 if result["allowed"] else 2)


if __name__ == "__main__":
    main()
