"""
calendar_generator.py - Genera calendar.json desde una estrategia mensual

Input: strategy.yaml con:
  - Pillar topics (temas principales)
  - Cadencia por plataforma (post por semana)
  - Fechas especiales (holidays, lanzamientos)
  - Plantillas de prompt por topico

Output: calendar.json con N posts balanceados

Uso:
    # Generar calendario del mes actual
    python calendar_generator.py --month current

    # Generar 30 dias desde hoy
    python calendar_generator.py --days 30

    # Inicializar strategy.yaml de ejemplo
    python calendar_generator.py --init
"""
import os
import sys
import json
import argparse
import random
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import cprint, info, ok, warn, error, banner, ROOT_DIR

try:
    import yaml
except ImportError:
    yaml = None


STRATEGY_PATH = ROOT_DIR / "config" / "strategy.yaml"
CALENDAR_PATH = ROOT_DIR / "config" / "calendar.json"


# ============================================================
# Default strategy template
# ============================================================

DEFAULT_STRATEGY = """# Strategy - Configuracion de estrategia de contenido
# Edita estos valores para tu marca/proyecto

# Nombre de la marca (se anade a captions)
brand_name: "Mi Marca"

# Pillar topics - los 3-5 temas principales que quieres cubrir
pillar_topics:
  - name: "Inspiracion"
    description: "Citas, motivacion, pensamientos"
    prompt_templates:
      - "inspirational quote on minimalist background, typography focused, professional, {topic_subtext}"
      - "abstract artistic interpretation of {topic_subtext}, vibrant colors, modern"
  - name: "Tutorial"
    description: "Tips y how-tos"
    prompt_templates:
      - "step-by-step visual tutorial illustration of {topic_subtext}, clean infographic style"
      - "professional diagram showing {topic_subtext}, modern flat design"
  - name: "Detras de camaras"
    description: "BTS del estudio"
    prompt_templates:
      - "behind the scenes of creative studio working on {topic_subtext}, candid photography"
      - "designer working on laptop, warm lighting, instagram story vertical, {topic_subtext}"

# Cadencia por plataforma (posts por semana)
cadence:
  instagram:
    posts_per_week: 5
    workflows: ["instagram_post", "instagram_story", "carousel_5"]
    default_platforms: ["instagram"]
  twitter:
    posts_per_week: 7
    workflows: ["twitter_post"]
    default_platforms: ["twitter"]
  youtube:
    posts_per_week: 2
    workflows: ["youtube_thumbnail"]
    default_platforms: ["youtube"]

# Caption templates (usan placeholders {brand}, {topic}, {subtext})
caption_templates:
  - "{brand} | {topic}: {subtext} ✨ #aiart #digitalart"
  - "Nuevo post sobre {topic}. {subtext} #creativity"
  - "{subtext} - {brand} #{topic_lower}"

# Hashtags por defecto
default_hashtags:
  - "#aiart"
  - "#digitalart"
  - "#creativity"

# Fuentes de subtext (se rellenan aleatoriamente)
subtext_pool:
  - "el futuro del trabajo creativo"
  - "inteligencia artificial como herramienta"
  - "diseno que inspira"
  - "innovacion en cada pixel"
  - "creatividad sin limites"
  - "comunidad que crea juntos"
  - "ideas que transforman"
  - "artista + maquina = magia"

# Fechas especiales (anadir posts extra esos dias)
special_dates:
  # - date: "2026-12-25"
  #   name: "Navidad"
  #   extra_posts: 2
  #   topic_override: "Inspiracion"
"""


def save_default_strategy():
    """Crea strategy.yaml de ejemplo."""
    with open(STRATEGY_PATH, "w", encoding="utf-8") as f:
        f.write(DEFAULT_STRATEGY)
    print(f"Strategy creada: {STRATEGY_PATH}")
    print("Edita este archivo con tu estrategia y luego ejecuta:")
    print("  python calendar_generator.py --days 30")


def load_strategy() -> Dict:
    """Carga strategy.yaml."""
    if not STRATEGY_PATH.exists():
        save_default_strategy()
        warn("Se creo strategy.yaml de ejemplo. Editalo y vuelve a ejecutar.")
        sys.exit(0)

    if yaml is None:
        error("PyYAML no instalado. pip install pyyaml")
        sys.exit(1)

    with open(STRATEGY_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ============================================================
# Generation
# ============================================================

def generate_calendar(strategy: Dict, days: int = 30) -> Dict:
    """Genera el calendario a partir de la estrategia."""
    brand = strategy.get("brand_name", "Mi Marca")
    topics = strategy.get("pillar_topics", [])
    cadence = strategy.get("cadence", {})
    caption_templates = strategy.get("caption_templates", ["{brand} | {topic}: {subtext}"])
    subtext_pool = strategy.get("subtext_pool", ["creatividad"])
    default_hashtags = strategy.get("default_hashtags", [])

    if not topics:
        error("strategy.yaml no tiene pillar_topics")
        return {"posts": []}

    posts = []
    post_counter = 1
    start_date = datetime.now()

    for day_offset in range(days):
        current_date = start_date + timedelta(days=day_offset)

        # Para cada plataforma con cadencia definida
        for platform, config in cadence.items():
            posts_per_week = config.get("posts_per_week", 0)
            workflows = config.get("workflows", [f"{platform}_post"])
            default_platforms = config.get("default_platforms", [platform])

            # Determinar si este dia toca post (distribucion uniforme)
            if posts_per_week == 0:
                continue
            posts_this_day = 1 if (day_offset * posts_per_week) % 7 < posts_per_week else 0
            # Simplificacion: post_per_week / 7 probabilidad
            if random.random() > (posts_per_week / 7.0):
                continue

            # Elegir topico aleatorio
            topic = random.choice(topics)
            topic_name = topic.get("name", "general")
            prompt_templates = topic.get("prompt_templates",
                                          ["professional photo of {topic_subtext}"])

            # Elegir prompt template y subtext
            prompt_template = random.choice(prompt_templates)
            subtext = random.choice(subtext_pool)

            # Rellenar placeholders
            prompt = prompt_template.format(
                topic_subtext=subtext,
                brand=brand
            )

            # Generar caption
            caption_template = random.choice(caption_templates)
            caption = caption_template.format(
                brand=brand,
                topic=topic_name,
                topic_lower=topic_name.lower(),
                subtext=subtext
            )
            if default_hashtags:
                caption += " " + " ".join(default_hashtags)

            # Elegir workflow
            workflow = random.choice(workflows)

            # Dimensiones por workflow
            dimensions = {
                "instagram_post": (1080, 1080),
                "instagram_story": (1080, 1920),
                "twitter_post": (1200, 675),
                "youtube_thumbnail": (1280, 720),
                "tiktok_video": (1080, 1920),
                "carousel_5": (1080, 1080),
            }
            w, h = dimensions.get(workflow, (1024, 1024))

            # Crear post
            post_id = f"auto_{post_counter:04d}"
            posts.append({
                "id": post_id,
                "status": "pending",
                "workflow": workflow,
                "title": f"{topic_name} - {subtext[:30]}",
                "prompt": prompt,
                "negative_prompt": "blurry, low quality, distorted, ugly, watermark, text, jpeg artifacts",
                "caption": caption[:2200],
                "platforms": default_platforms,
                "checkpoint": "juggernautXL_v9.safetensors",
                "seed": random.randint(1, 999999999),
                "width": w,
                "height": h,
                "batch_size": 1,
                "output_prefix": post_id,
                "scheduled_at": current_date.replace(
                    hour=10 + post_counter % 8,  # entre 10am y 6pm
                    minute=0, second=0, microsecond=0
                ).isoformat(),
                "created_at": datetime.now().isoformat(),
                "created_via": "calendar_generator",
            })
            post_counter += 1

    return {
        "last_updated": datetime.now().isoformat(),
        "strategy_version": "1.0",
        "posts": posts
    }


# ============================================================
# Main
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Generador de calendario")
    parser.add_argument("--days", type=int, default=30,
                        help="Numero de dias a generar (default 30)")
    parser.add_argument("--month", choices=["current", "next"],
                        help="Generar mes completo")
    parser.add_argument("--init", action="store_true",
                        help="Crear strategy.yaml de ejemplo")
    parser.add_argument("--merge", action="store_true",
                        help="Anadir a calendar.json existente en vez de sobreescribir")
    args = parser.parse_args()

    if args.init:
        save_default_strategy()
        return

    strategy = load_strategy()

    if args.month == "current":
        now = datetime.now()
        days_in_month = 31  # simplificacion
        args.days = days_in_month - now.day + 1
    elif args.month == "next":
        args.days = 31

    info(f"Generando calendario para {args.days} dias...")
    calendar = generate_calendar(strategy, args.days)

    if args.merge and CALENDAR_PATH.exists():
        with open(CALENDAR_PATH, "r", encoding="utf-8") as f:
            existing = json.load(f)
        existing.setdefault("posts", []).extend(calendar["posts"])
        calendar = existing

    with open(CALENDAR_PATH, "w", encoding="utf-8") as f:
        json.dump(calendar, f, indent=2, ensure_ascii=False)

    banner("CALENDARIO GENERADO")
    ok(f"Posts generados: {len(calendar['posts'])}")
    ok(f"Archivo: {CALENDAR_PATH}")

    # Distribucion por plataforma
    from collections import Counter
    platforms = Counter()
    for p in calendar["posts"]:
        for plat in p["platforms"]:
            platforms[plat] += 1

    cprint("\nDistribucion por plataforma:", '\033[96m')
    for plat, count in platforms.most_common():
        cprint(f"  {plat:15} {count} posts", '\033[0m')


if __name__ == "__main__":
    main()
