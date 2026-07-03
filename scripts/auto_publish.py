"""
auto_publish.py - Orquestador de contenido social con ComfyUI + APIs
ComfyUI Social Media Suite

Pipeline:
  1. Lee calendario de contenido (JSON)
  2. Para cada post pendiente:
     a. Carga workflow API Format
     b. Sustituye prompt/seed/parametros
     c. Ejecuta via ComfyUI API (WebSocket)
     d. Descarga imagenes/videos generados
     e. (Opcional) Auto-genera caption con WD14 Tagger o LLM
     f. Publica a redes sociales (Instagram, Twitter/X, Facebook, Pinterest)
     g. Marca el post como publicado en el calendario

Uso:
    python auto_publish.py                           # Procesa posts pendientes
    python auto_publish.py --dry-run                 # Solo simula, no publica
    python auto_publish.py --once POST_ID            # Procesa solo un post
    python auto_publish.py --platforms instagram     # Solo publica en IG
    python auto_publish.py --schedule                # Modo daemon, cron-style

Variables de entorno requeridas (ver .env.example):
    COMFYUI_HOST=127.0.0.1
    COMFYUI_PORT=8188
    IG_USERNAME=tu_usuario
    IG_PASSWORD=tu_password
    TWITTER_CONSUMER_KEY=...
    TWITTER_CONSUMER_SECRET=...
    TWITTER_ACCESS_TOKEN=...
    TWITTER_ACCESS_TOKEN_SECRET=...
    FB_PAGE_TOKEN=...
    FB_PAGE_ID=...
    PINTEREST_EMAIL=...
    PINTEREST_PASSWORD=...
    PINTEREST_USERNAME=...
    PINTEREST_BOARD_ID=...
"""
import argparse
import json
import os
import sys
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Cargar .env si existe
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Path setup
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from comfyui_api_client import (
    ComfyUIClient, load_workflow_api_json, set_workflow_input,
    find_node_by_class, find_nodes_by_class
)

# ============================================================
# Configuracion
# ============================================================

ROOT_DIR = Path(__file__).resolve().parent.parent
CALENDAR_FILE = ROOT_DIR / "config" / "calendar.json"
OUTPUT_DIR = ROOT_DIR / "ComfyUI" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(ROOT_DIR / "auto_publish.log",
                            encoding="utf-8"),
    ]
)
log = logging.getLogger("auto_publish")


# ============================================================
# Calendar management
# ============================================================

def load_calendar() -> Dict:
    """Carga el calendario de contenido."""
    if not CALENDAR_FILE.exists():
        log.error(f"Calendario no encontrado: {CALENDAR_FILE}")
        log.info("Copia config/calendar_template.json a config/calendar.json")
        sys.exit(1)
    with open(CALENDAR_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_calendar(data: Dict):
    """Guarda el calendario."""
    with open(CALENDAR_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_pending_posts(calendar: Dict,
                      scheduled_only: bool = False) -> List[Dict]:
    """Devuelve posts pendientes de publicar."""
    now = datetime.now().isoformat()
    pending = []
    for post in calendar.get("posts", []):
        if post.get("status") != "pending":
            continue
        if scheduled_only and post.get("scheduled_at", now) > now:
            continue
        pending.append(post)
    return pending


def update_post_status(post_id: str, status: str,
                       extra: Optional[Dict] = None):
    """Actualiza el estado de un post en el calendario."""
    calendar = load_calendar()
    for post in calendar["posts"]:
        if post["id"] == post_id:
            post["status"] = status
            post["updated_at"] = datetime.now().isoformat()
            if extra:
                post.update(extra)
            break
    save_calendar(calendar)


# ============================================================
# Workflow execution
# ============================================================

def prepare_workflow(post: Dict) -> Dict:
    """Carga el workflow (API Format) y sustituye variables dinamicas."""
    # Buscar primero la version API Format (la que necesita el endpoint /prompt)
    workflow_path = ROOT_DIR / "workflows" / f"{post['workflow']}_api.json"

    if not workflow_path.exists():
        # Fallback: si existe UI format, intentar convertirlo on-the-fly
        ui_path = ROOT_DIR / "workflows" / f"{post['workflow']}.json"
        if ui_path.exists():
            log.info(f"Convirtiendo {ui_path.name} a API format on-the-fly...")
            try:
                from convert_workflow_format import convert_ui_to_api, is_api_format
                with open(ui_path, "r", encoding="utf-8") as f:
                    ui_data = json.load(f)
                if is_api_format(ui_data):
                    workflow = ui_data
                else:
                    workflow = convert_ui_to_api(ui_data)
                # Guardar para futuras ejecuciones
                with open(workflow_path, "w", encoding="utf-8") as f:
                    json.dump(workflow, f, indent=2, ensure_ascii=False)
                log.info(f"Workflow API guardado: {workflow_path.name}")
            except Exception as e:
                raise FileNotFoundError(
                    f"No se pudo convertir workflow {post['workflow']}: {e}. "
                    f"Ejecuta: python scripts/convert_workflow_format.py --all"
                )
        else:
            raise FileNotFoundError(
                f"Workflow no encontrado: {post['workflow']} "
                f"(buscado en {workflow_path} y {ui_path})"
            )
    else:
        workflow = load_workflow_api_json(str(workflow_path))

    # Validar que el workflow este en API format
    if "class_type" not in next(iter(workflow.values()), {}):
        raise ValueError(
            f"Workflow {post['workflow']} no esta en API Format. "
            f"Ejecuta: python scripts/convert_workflow_format.py --all"
        )

    # Buscar nodos CLIPTextEncode (siempre inicializar para evitar NameError)
    clip_nodes = find_nodes_by_class(workflow, "CLIPTextEncode")

    # Sustituir prompt positivo (primer CLIPTextEncode)
    if "prompt" in post and clip_nodes:
        set_workflow_input(workflow, clip_nodes[0], "text",
                           post["prompt"])

    # Sustituir prompt negativo (segundo CLIPTextEncode)
    if "negative_prompt" in post and len(clip_nodes) > 1:
        set_workflow_input(workflow, clip_nodes[1], "text",
                           post["negative_prompt"])

    # Sustituir seed
    if "seed" in post:
        ksampler_nodes = find_nodes_by_class(workflow, "KSampler")
        for nid in ksampler_nodes:
            set_workflow_input(workflow, nid, "seed", post["seed"])

    # Sustituir dimensiones
    if "width" in post and "height" in post:
        empty_nodes = find_nodes_by_class(workflow, "EmptyLatentImage")
        for nid in empty_nodes:
            set_workflow_input(workflow, nid, "width", post["width"])
            set_workflow_input(workflow, nid, "height", post["height"])

    # Sustituir batch_size (para videos/carruseles)
    if "batch_size" in post:
        empty_nodes = find_nodes_by_class(workflow, "EmptyLatentImage")
        for nid in empty_nodes:
            set_workflow_input(workflow, nid, "batch_size",
                               post["batch_size"])

    # Sustituir checkpoint
    if "checkpoint" in post:
        cp_nodes = find_nodes_by_class(workflow, "CheckpointLoaderSimple")
        for nid in cp_nodes:
            set_workflow_input(workflow, nid, "ckpt_name",
                               post["checkpoint"])

    # Sustituir SaveImage prefix
    if "output_prefix" in post:
        save_nodes = find_nodes_by_class(workflow, "SaveImage")
        for nid in save_nodes:
            set_workflow_input(workflow, nid, "filename_prefix",
                               post["output_prefix"])

    return workflow


def execute_workflow(client: ComfyUIClient, workflow: Dict,
                     post_id: str) -> List[Path]:
    """Ejecuta el workflow y devuelve las rutas de los outputs."""
    log.info(f"Encolando workflow para post {post_id}...")
    prompt_id = client.queue_prompt(workflow)
    log.info(f"Prompt ID: {prompt_id}")

    log.info("Esperando finalizacion (WebSocket)...")
    history = client.wait_for_completion(prompt_id, timeout=1800)
    log.info("Workflow completado.")

    images = client.get_output_images(history)
    if not images:
        raise RuntimeError(f"No se generaron outputs para post {post_id}")

    saved_paths = []
    for fname, data in images:
        out_path = OUTPUT_DIR / f"{post_id}_{fname}"
        with open(out_path, "wb") as f:
            f.write(data)
        saved_paths.append(out_path)
        log.info(f"Output guardado: {out_path}")

    return saved_paths


# ============================================================
# Publishing - Instagram
# ============================================================

def publish_instagram(image_path: Path, caption: str) -> Dict:
    """Publica en Instagram usando instagrapi con session caching."""
    try:
        from instagrapi import Client
    except ImportError:
        log.error("instagrapi no instalado. Ejecuta: pip install instagrapi")
        return {"success": False, "error": "instagrapi not installed"}

    session_file = ROOT_DIR / "ig_session.json"
    cl = Client()

    # Reusar sesion si existe para evitar multiples logins (ban risk)
    if session_file.exists():
        try:
            cl.load_settings(str(session_file))
            cl.get_timeline_feed()  # valida sesion
            log.info("  Sesion IG reusada.")
        except Exception:
            cl = Client()  # sesion invalida, recrear

    try:
        if not cl.user_id:
            cl.login(os.environ["IG_USERNAME"], os.environ["IG_PASSWORD"])
            cl.dump_settings(str(session_file))
            log.info("  Login IG OK, sesion guardada.")
        media = cl.photo_upload(str(image_path), caption=caption)
        return {"success": True, "media_id": media.id,
                "url": f"https://instagram.com/p/{media.code}/"}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        # NO cerrar sesion para poder reusarla
        pass


# ============================================================
# Publishing - Twitter/X
# ============================================================

def publish_twitter(image_path: Path, caption: str) -> Dict:
    """Publica en Twitter/X usando tweepy."""
    try:
        import tweepy
    except ImportError:
        log.error("tweepy no instalado. Ejecuta: pip install tweepy")
        return {"success": False, "error": "tweepy not installed"}

    try:
        client = tweepy.Client(
            bearer_token=os.environ.get("TWITTER_BEARER_TOKEN"),
            consumer_key=os.environ["TWITTER_CONSUMER_KEY"],
            consumer_secret=os.environ["TWITTER_CONSUMER_SECRET"],
            access_token=os.environ["TWITTER_ACCESS_TOKEN"],
            access_token_secret=os.environ["TWITTER_ACCESS_TOKEN_SECRET"],
        )
        auth = tweepy.OAuth1UserHandler(
            os.environ["TWITTER_CONSUMER_KEY"],
            os.environ["TWITTER_CONSUMER_SECRET"],
            os.environ["TWITTER_ACCESS_TOKEN"],
            os.environ["TWITTER_ACCESS_TOKEN_SECRET"],
        )
        api_v1 = tweepy.API(auth)
        media = api_v1.media_upload(str(image_path))
        response = client.create_tweet(text=caption,
                                       media_ids=[media.media_id])
        tweet_id = response.data["id"]
        return {"success": True, "tweet_id": tweet_id,
                "url": f"https://twitter.com/i/web/status/{tweet_id}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================
# Publishing - Facebook
# ============================================================

def publish_facebook(image_path: Path, caption: str) -> Dict:
    """Publica en una pagina de Facebook usando facebook-sdk."""
    try:
        import facebook
    except ImportError:
        log.error("facebook-sdk no instalado. pip install facebook-sdk")
        return {"success": False, "error": "facebook-sdk not installed"}

    try:
        graph = facebook.GraphAPI(access_token=os.environ["FB_PAGE_TOKEN"])
        with open(image_path, "rb") as img:
            response = graph.put_photo(image=img, message=caption)
        post_id = response["id"]
        page_id = os.environ["FB_PAGE_ID"]
        return {"success": True, "post_id": post_id,
                "url": f"https://facebook.com/{page_id}/posts/{post_id}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================
# Publishing - Pinterest
# ============================================================

def publish_pinterest(image_path: Path, caption: str,
                      title: str = "") -> Dict:
    """Publica en Pinterest usando py3-pinterest."""
    try:
        from py3pin.Pinterest import Pinterest
    except ImportError:
        log.error("py3-pinterest no instalado. pip install py3-pinterest")
        return {"success": False, "error": "py3-pinterest not installed"}

    try:
        p = Pinterest(
            email=os.environ["PINTEREST_EMAIL"],
            password=os.environ["PINTEREST_PASSWORD"],
            username=os.environ["PINTEREST_USERNAME"],
            cred_root=str(ROOT_DIR / "pinterest_creds")
        )
        p.login()
        response = p.upload_pin(
            board_id=os.environ["PINTEREST_BOARD_ID"],
            image_file=str(image_path),
            description=caption,
            title=title or caption[:100]
        )
        return {"success": True, "response": response}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================
# Publishing - YouTube (Shorts)
# ============================================================

def publish_youtube(video_path: Path, title: str = "",
                    description: str = "", tags: list = None) -> Dict:
    """Sube un video a YouTube usando la Data API v3 (OAuth flow)."""
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except ImportError:
        log.error("google-api-python-client no instalado. pip install google-api-python-client google-auth-oauthlib")
        return {"success": False, "error": "google-api deps not installed"}

    tags = tags or []
    client_secrets = os.environ.get("YOUTUBE_CLIENT_SECRETS_FILE", "client_secret.json")
    token_file = ROOT_DIR / "youtube_token.json"
    scopes = ["https://www.googleapis.com/auth/youtube.upload"]

    creds = None
    if token_file.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_file), scopes)
        except Exception:
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not Path(client_secrets).exists():
                return {"success": False,
                        "error": f"Falta {client_secrets}. Descarga OAuth credentials desde https://console.cloud.google.com/"}
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets, scopes)
            creds = flow.run_local_server(port=0)
        with open(token_file, "w") as f:
            f.write(creds.to_json())

    try:
        yt = build("youtube", "v3", credentials=creds)
        body = {
            "snippet": {
                "title": title[:100],
                "description": description,
                "tags": tags,
                "categoryId": "24",  # Entertainment
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False,
            }
        }
        media = MediaFileUpload(str(video_path), chunksize=-1,
                                resumable=True, mimetype="video/*")
        request = yt.videos().insert(part="snippet,status",
                                     body=body, media_body=media)
        response = None
        while response is None:
            status, response = request.next_chunk()
        video_id = response["id"]
        return {"success": True, "video_id": video_id,
                "url": f"https://youtube.com/watch?v={video_id}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================
# Publishing - TikTok
# ============================================================

def publish_tiktok(video_path: Path, caption: str = "",
                   hashtags: list = None) -> Dict:
    """Sube un video a TikTok usando tiktok-uploader (no oficial)."""
    try:
        from tiktok_uploader.upload import upload_video
    except ImportError:
        log.error("tiktok-uploader no instalado. pip install tiktok-uploader")
        return {"success": False, "error": "tiktok-uploader not installed"}

    hashtags = hashtags or []
    # Anadir hashtags al caption si no estan
    caption_with_tags = caption
    for tag in hashtags:
        if f"#{tag}" not in caption:
            caption_with_tags += f" #{tag}"

    username = os.environ.get("TIKTOK_USERNAME")
    password = os.environ.get("TIKTOK_PASSWORD")
    if not username or not password:
        return {"success": False,
                "error": "TIKTOK_USERNAME y TIKTOK_PASSWORD requeridos en .env"}

    try:
        # tiktok-uploader requiere cookies selenium en algunos casos
        # Forma simple: usar credenciales
        result = upload_video(
            str(video_path),
            description=caption_with_tags,
            credentials={"username": username, "password": password},
        )
        return {"success": True, "response": str(result)}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================
# Orquestador principal
# ============================================================

PUBLISHERS = {
    "instagram": publish_instagram,
    "twitter": publish_twitter,
    "facebook": publish_facebook,
    "pinterest": publish_pinterest,
    "youtube": publish_youtube,
    "tiktok": publish_tiktok,
}


def process_post(post: Dict, client: ComfyUIClient,
                 platforms_filter: Optional[List[str]] = None,
                 dry_run: bool = False) -> Dict:
    """Procesa un post: genera imagen y publica."""
    post_id = post["id"]
    log.info(f"=== Procesando post {post_id} ===")
    log.info(f"  Workflow: {post.get('workflow', 'instagram_post')}")
    log.info(f"  Prompt: {post.get('prompt', '')[:100]}...")

    # 1. Preparar workflow
    try:
        workflow = prepare_workflow(post)
    except Exception as e:
        log.error(f"Error preparando workflow: {e}")
        update_post_status(post_id, "failed", {"error": str(e)})
        return {"success": False, "error": str(e)}

    if dry_run:
        log.info("  [DRY RUN] No se ejecuta el workflow ni se publica.")
        return {"success": True, "dry_run": True}

    # 2. Ejecutar workflow
    try:
        image_paths = execute_workflow(client, workflow, post_id)
    except Exception as e:
        log.error(f"Error ejecutando workflow: {e}")
        update_post_status(post_id, "failed", {"error": str(e)})
        return {"success": False, "error": str(e)}

    # 3. Publicar en cada plataforma
    platforms = platforms_filter or post.get("platforms",
                                             ["instagram", "twitter"])
    caption = post.get("caption", post.get("prompt", "")[:2200])
    results = {}

    for platform in platforms:
        if platform not in PUBLISHERS:
            log.warning(f"  Plataforma no soportada: {platform}")
            continue
        log.info(f"  Publicando en {platform}...")
        try:
            # Cada publicador tiene su propia firma (algunos requieren title)
            if platform == "pinterest":
                result = PUBLISHERS[platform](
                    image_paths[0], caption,
                    title=post.get("title", "")
                )
            elif platform == "youtube":
                result = PUBLISHERS[platform](
                    image_paths[0],
                    title=post.get("title", caption[:100]),
                    description=caption,
                    tags=post.get("tags", [])
                )
            else:
                # instagram, twitter, facebook, tiktok - solo image + caption
                result = PUBLISHERS[platform](image_paths[0], caption)
            results[platform] = result
            if result.get("success"):
                log.info(f"    OK: {result.get('url', '')}")
            else:
                log.error(f"    FALLO: {result.get('error', '')}")
        except Exception as e:
            results[platform] = {"success": False, "error": str(e)}
            log.error(f"    FALLO: {e}")

    # 4. Actualizar calendario
    all_success = all(r.get("success") for r in results.values()) if results else False
    status = "published" if all_success else "partial"
    update_post_status(post_id, status, {
        "image_paths": [str(p) for p in image_paths],
        "publish_results": results,
        "published_at": datetime.now().isoformat()
    })

    return {"success": all_success, "results": results,
            "image_paths": [str(p) for p in image_paths]}


def run(dry_run: bool = False, post_id: Optional[str] = None,
        platforms: Optional[List[str]] = None,
        scheduled: bool = False):
    """Funcion principal."""
    calendar = load_calendar()
    pending = get_pending_posts(calendar, scheduled_only=scheduled)

    if post_id:
        pending = [p for p in pending if p["id"] == post_id]

    if not pending:
        log.info("No hay posts pendientes.")
        return

    log.info(f"Posts pendientes: {len(pending)}")

    # Verificar ComfyUI
    client = ComfyUIClient(
        host=os.environ.get("COMFYUI_HOST", "127.0.0.1"),
        port=int(os.environ.get("COMFYUI_PORT", "8188"))
    )

    if not dry_run and not client.is_alive():
        log.error("ComfyUI no esta corriendo. Inicia con start.bat/start.sh")
        sys.exit(1)

    for post in pending:
        try:
            process_post(post, client, platforms, dry_run)
        except Exception as e:
            log.exception(f"Error procesando post {post['id']}: {e}")
            update_post_status(post["id"], "failed", {"error": str(e)})


def run_daemon(interval: int = 60):
    """Modo daemon: revisa calendario cada N segundos."""
    log.info(f"Iniciando daemon (interval={interval}s). Ctrl+C para parar.")
    while True:
        try:
            run(scheduled=True)
        except KeyboardInterrupt:
            log.info("Deteniendo daemon...")
            break
        except Exception as e:
            log.exception(f"Error en daemon: {e}")
        time.sleep(interval)


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Orquestador de contenido social con ComfyUI"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Solo simula, no publica ni ejecuta workflow")
    parser.add_argument("--once", type=str,
                        help="Procesa solo un post por ID")
    parser.add_argument("--platforms", type=str,
                        help="Filtrar plataformas (comma-separated)")
    parser.add_argument("--schedule", action="store_true",
                        help="Solo procesa posts programados cuya fecha ya paso")
    parser.add_argument("--daemon", action="store_true",
                        help="Modo daemon continuo")
    parser.add_argument("--interval", type=int, default=60,
                        help="Intervalo del daemon en segundos (default 60)")
    args = parser.parse_args()

    if args.daemon:
        run_daemon(args.interval)
    else:
        platforms = args.platforms.split(",") if args.platforms else None
        run(
            dry_run=args.dry_run,
            post_id=args.once,
            platforms=platforms,
            scheduled=args.schedule
        )


if __name__ == "__main__":
    main()
