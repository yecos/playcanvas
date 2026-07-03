"""
webhook_server.py - Servidor HTTP para recibir webhooks de ComfyUI-WebhookNotifier

Permite ejecucion event-driven: ComfyUI termina un job -> notifica a este servidor
-> el servidor dispara la publicacion del post correspondiente.

Flujo:
  1. auto_publish.py encola un workflow en ComfyUI
  2. ComfyUI-WebhookNotifier (custom node) esta configurado para POST a
     http://localhost:8189/comfyui-webhook cuando termina
  3. Este servidor recibe el webhook, busca el post por prompt_id
  4. Descarga la imagen y publica en redes sociales

Uso:
    python webhook_server.py
    python webhook_server.py --port 8189 --host 0.0.0.0

Configurar ComfyUI-WebhookNotifier:
  - URL: http://localhost:8189/comfyui-webhook
  - Method: POST
  - Header: X-Webhook-Secret: <tu secreto de .env WEBHOOK_SECRET>
"""
import os
import sys
import json
import argparse
import threading
import time
from pathlib import Path
from typing import Dict, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import cprint, info, ok, warn, error, banner, ROOT_DIR

# Flask o http.server (fallback stdlib)
try:
    from flask import Flask, request, jsonify
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False
    from http.server import HTTPServer, BaseHTTPRequestHandler


# ============================================================
# Webhook handler
# ============================================================

def process_webhook_payload(payload: Dict, expected_secret: str) -> Dict:
    """
    Procesa el payload del webhook de ComfyUI-WebhookNotifier.
    Devuelve: {"success": bool, "message": str, "post_id": str}
    """
    # Validar secreto
    received_secret = payload.get("secret") or payload.get("webhook_secret", "")
    if expected_secret and received_secret != expected_secret:
        return {"success": False, "message": "Secret invalido"}

    # Extraer prompt_id y estado
    prompt_id = payload.get("prompt_id") or payload.get("promptId")
    status = payload.get("status", "unknown")
    node_id = payload.get("node_id") or payload.get("node")

    if not prompt_id:
        return {"success": False, "message": "Falta prompt_id"}

    info(f"Webhook recibido: prompt_id={prompt_id}, status={status}, node={node_id}")

    if status not in ("success", "executed", "completed", None):
        warn(f"Workflow con estado no exitoso: {status}")
        return {"success": False, "message": f"Workflow fallo: {status}"}

    # Buscar el post correspondiente en calendar.json
    calendar_file = ROOT_DIR / "config" / "calendar.json"
    if not calendar_file.exists():
        return {"success": False, "message": "calendar.json no existe"}

    with open(calendar_file, "r", encoding="utf-8") as f:
        calendar = json.load(f)

    # Buscar post con prompt_id coincidente
    post = None
    for p in calendar.get("posts", []):
        if p.get("last_prompt_id") == prompt_id:
            post = p
            break

    if not post:
        warn(f"No se encontro post para prompt_id {prompt_id}")
        return {"success": False, "message": "Post no encontrado en calendar"}

    # Ejecutar publicacion en background
    post_id = post["id"]
    info(f"Disparando publicacion para post {post_id}")

    # Importar aqui para evitar import circular
    try:
        from auto_publish import process_post, update_post_status
        from comfyui_api_client import ComfyUIClient

        # El workflow ya termino, solo necesitamos descargar + publicar
        client = ComfyUIClient()
        history = client.get_history(prompt_id)

        if not history:
            return {"success": False, "message": "Historial vacio para prompt_id"}

        # Descargar imagenes
        image_paths = []
        try:
            from auto_publish import OUTPUT_DIR, execute_workflow
            images = client.get_output_images(history)
            for fname, data in images:
                out_path = OUTPUT_DIR / f"{post_id}_{fname}"
                with open(out_path, "wb") as f:
                    f.write(data)
                image_paths.append(out_path)
                info(f"Imagen descargada: {out_path}")
        except Exception as e:
            error(f"Error descargando imagenes: {e}")
            return {"success": False, "message": str(e)}

        if not image_paths:
            return {"success": False, "message": "No se generaron imagenes"}

        # Publicar
        platforms = post.get("platforms", ["instagram"])
        caption = post.get("caption", post.get("prompt", "")[:2200])

        # Aplicar moderacion antes de publicar
        try:
            from content_moderator import moderate
            moderation = moderate(
                image_path=str(image_paths[0]),
                caption=caption,
                platform=platforms[0] if platforms else "instagram"
            )
            if not moderation["allowed"]:
                error(f"Post {post_id} bloqueado por moderacion: {moderation['reasons']}")
                update_post_status(post_id, "blocked",
                                   {"moderation": moderation})
                return {"success": False,
                        "message": f"Bloqueado: {moderation['reasons']}"}
        except ImportError:
            warn("content_moderator no disponible, saltando moderacion")

        # Publicar via el dict PUBLISHERS
        from auto_publish import PUBLISHERS
        results = {}
        for platform in platforms:
            if platform not in PUBLISHERS:
                continue
            try:
                if platform == "pinterest":
                    result = PUBLISHERS[platform](image_paths[0], caption,
                                                  title=post.get("title", ""))
                elif platform == "youtube":
                    result = PUBLISHERS[platform](image_paths[0],
                                                  title=post.get("title", caption[:100]),
                                                  description=caption,
                                                  tags=post.get("tags", []))
                else:
                    result = PUBLISHERS[platform](image_paths[0], caption)
                results[platform] = result
            except Exception as e:
                results[platform] = {"success": False, "error": str(e)}

        # Actualizar calendario
        all_success = all(r.get("success") for r in results.values()) if results else False
        status_final = "published" if all_success else "partial"
        update_post_status(post_id, status_final, {
            "image_paths": [str(p) for p in image_paths],
            "publish_results": results,
            "webhook_processed_at": time.strftime("%Y-%m-%dT%H:%M:%S")
        })

        ok(f"Post {post_id} procesado via webhook: {status_final}")
        return {"success": True, "post_id": post_id, "status": status_final,
                "results": results}

    except Exception as e:
        error(f"Error procesando webhook: {e}")
        return {"success": False, "message": str(e)}


# ============================================================
# Flask server
# ============================================================

if HAS_FLASK:
    app = Flask(__name__)

    @app.route("/comfyui-webhook", methods=["POST"])
    def comfyui_webhook():
        payload = request.get_json(silent=True) or {}
        secret = os.environ.get("WEBHOOK_SECRET", "")
        result = process_webhook_payload(payload, secret)
        return jsonify(result), 200 if result.get("success") else 400

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "service": "comfyui-webhook-server"})

    @app.route("/", methods=["GET"])
    def index():
        return jsonify({
            "service": "ComfyUI Social Media Suite - Webhook Server",
            "endpoints": {
                "/comfyui-webhook": "POST - recibe webhooks de ComfyUI",
                "/health": "GET - health check"
            }
        })


# ============================================================
# HTTP server fallback (stdlib)
# ============================================================

class WebhookHandler(BaseHTTPRequestHandler):
    def _send_json(self, code, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/comfyui-webhook":
            self._send_json(404, {"error": "Not found"})
            return
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            payload = json.loads(body) if body else {}
        except Exception as e:
            self._send_json(400, {"error": f"JSON invalido: {e}"})
            return

        secret = os.environ.get("WEBHOOK_SECRET", "")
        result = process_webhook_payload(payload, secret)
        self._send_json(200 if result.get("success") else 400, result)

    def do_GET(self):
        if self.path == "/health":
            self._send_json(200, {"status": "ok"})
        elif self.path == "/":
            self._send_json(200, {"service": "ComfyUI Webhook Server",
                                   "endpoints": ["/comfyui-webhook", "/health"]})
        else:
            self._send_json(404, {"error": "Not found"})

    def log_message(self, format, *args):
        # Suprimir logs de HTTP stdlib (usamos nuestros propios)
        pass


# ============================================================
# Main
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Webhook server para ComfyUI")
    parser.add_argument("--host", default="127.0.0.1",
                        help="Host (default 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8189,
                        help="Puerto (default 8189)")
    args = parser.parse_args()

    banner("WEBHOOK SERVER - COMFYUI SOCIAL SUITE")
    info(f"Backend: {'Flask' if HAS_FLASK else 'http.server (stdlib)'}")
    info(f"Escuchando en: http://{args.host}:{args.port}")
    info(f"Endpoint webhook: POST http://{args.host}:{args.port}/comfyui-webhook")
    info(f"Health check:    GET  http://{args.host}:{args.port}/health")

    if not os.environ.get("WEBHOOK_SECRET"):
        warn("WEBHOOK_SECRET no configurado. Endpoints sin autenticacion.")
    else:
        ok("WEBHOOK_SECRET configurado. Endpoints protegidos.")

    print()
    info("Configura ComfyUI-WebhookNotifier con:")
    cprint(f"  URL: http://{args.host}:{args.port}/comfyui-webhook", '\033[96m')
    cprint(f"  Method: POST", '\033[96m')
    cprint(f"  Header: X-Webhook-Secret: <tu WEBHOOK_SECRET>", '\033[96m')
    cprint(f"  Body: {{\"prompt_id\": \"<prompt_id>\", \"status\": \"success\"}}", '\033[96m')
    print()
    info("Ctrl+C para detener.")
    print()

    if HAS_FLASK:
        app.run(host=args.host, port=args.port, debug=False, threaded=True)
    else:
        server = HTTPServer((args.host, args.port), WebhookHandler)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            info("\nDeteniendo servidor...")
            server.shutdown()


if __name__ == "__main__":
    main()
