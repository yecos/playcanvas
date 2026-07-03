"""
bot_telegram.py - Bot de Telegram para control remoto del ComfyUI Social Suite

Comandos soportados:
  /start          - Bienvenida
  /status         - Estado de ComfyUI + cola
  /pending        - Lista posts pendientes
  /gen <workflow> <prompt> - Encolar generacion rapida
  /publish <post_id> - Forzar publicacion de un post
  /pause          - Pausar cola
  /resume         - Reanudar cola
  /retry          - Reintentar posts fallidos
  /cancel <post_id> - Cancelar post
  /help           - Mostrar ayuda

Seguridad:
  Solo usuarios cuyos IDs esten en TELEGRAM_ALLOWED_USER_IDS pueden usar el bot.

Uso:
    python bot_telegram.py

Requisitos:
    pip install python-telegram-bot
    Set TELEGRAM_BOT_TOKEN en .env (via @BotFather)
    Set TELEGRAM_ALLOWED_USER_IDS=123456789,987654321
"""
import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import cprint, info, ok, warn, error, banner, ROOT_DIR

try:
    from telegram import Update
    from telegram.ext import (
        Application, CommandHandler, MessageHandler,
        ContextTypes, filters
    )
    HAS_TG = True
except ImportError:
    HAS_TG = False


# ============================================================
# Auth
# ============================================================

def get_allowed_users() -> set:
    """Devuelve el set de user IDs permitidos."""
    raw = os.environ.get("TELEGRAM_ALLOWED_USER_IDS", "")
    if not raw:
        return set()
    return {int(uid.strip()) for uid in raw.split(",") if uid.strip().isdigit()}


def is_authorized(update: Update) -> bool:
    """Verifica si el usuario esta autorizado."""
    allowed = get_allowed_users()
    if not allowed:
        return False  # Si no hay allow-list, nadie pasa
    return update.effective_user.id in allowed


# ============================================================
# Commands
# ============================================================

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        await update.message.reply_text(
            "No estas autorizado para usar este bot.\n"
            f"Tu user ID es: {update.effective_user.id}\n"
            "Anadelo a TELEGRAM_ALLOWED_USER_IDS en .env"
        )
        return

    await update.message.reply_text(
        "ComfyUI Social Suite - Bot de Control\n\n"
        "Comandos disponibles:\n"
        "/status - Estado del sistema\n"
        "/pending - Posts pendientes\n"
        "/gen <workflow> <prompt> - Encolar generacion\n"
        "/publish <post_id> - Publicar un post\n"
        "/pause - Pausar cola\n"
        "/resume - Reanudar cola\n"
        "/retry - Reintentar fallidos\n"
        "/cancel <post_id> - Cancelar post\n"
        "/help - Mostrar esta ayuda"
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return

    try:
        from comfyui_api_client import ComfyUIClient
        client = ComfyUIClient()
        comfy_alive = client.is_alive(timeout=3)
    except Exception:
        comfy_alive = False

    # Estado de cola
    try:
        from queue_manager import get_status
        queue_status = get_status()
    except Exception:
        queue_status = {}

    msg = f"""Estado del Sistema
━━━━━━━━━━━━━━━━━━━━
ComfyUI: {'OK' if comfy_alive else 'NO RESPONDE'}
Cola: {queue_status or 'vacia'}
"""
    await update.message.reply_text(msg)


async def cmd_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return

    cal_file = ROOT_DIR / "config" / "calendar.json"
    if not cal_file.exists():
        await update.message.reply_text("calendar.json no existe")
        return

    with open(cal_file, "r", encoding="utf-8") as f:
        cal = json.load(f)

    pending = [p for p in cal.get("posts", []) if p.get("status") == "pending"]
    if not pending:
        await update.message.reply_text("No hay posts pendientes.")
        return

    msg = f"Posts pendientes: {len(pending)}\n\n"
    for p in pending[:10]:
        msg += f"• {p['id']}: {p.get('workflow')} - {p.get('prompt', '')[:40]}...\n"
    if len(pending) > 10:
        msg += f"\n...y {len(pending) - 10} mas"

    await update.message.reply_text(msg)


async def cmd_gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Encola una generacion rapida: /gen instagram_post mi prompt aqui"""
    if not is_authorized(update):
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "Uso: /gen <workflow> <prompt>\n"
            "Ej: /gen instagram_post sunset over Tokyo, 8k"
        )
        return

    workflow = context.args[0]
    prompt = " ".join(context.args[1:])

    # Crear post temporal en calendar
    cal_file = ROOT_DIR / "config" / "calendar.json"
    with open(cal_file, "r", encoding="utf-8") as f:
        cal = json.load(f)

    post_id = f"tg_{int(__import__('time').time())}"
    post = {
        "id": post_id,
        "status": "pending",
        "workflow": workflow,
        "prompt": prompt,
        "caption": prompt[:2200],
        "platforms": ["instagram"],
        "created_at": __import__("datetime").datetime.now().isoformat(),
        "created_via": "telegram",
    }
    cal.setdefault("posts", []).append(post)

    with open(cal_file, "w", encoding="utf-8") as f:
        json.dump(cal, f, indent=2, ensure_ascii=False)

    await update.message.reply_text(
        f"Post encolado: {post_id}\nWorkflow: {workflow}\nPrompt: {prompt[:80]}..."
    )


async def cmd_publish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fuerza la publicacion de un post: /publish post_001"""
    if not is_authorized(update):
        return

    if not context.args:
        await update.message.reply_text("Uso: /publish <post_id>")
        return

    post_id = context.args[0]
    await update.message.reply_text(f"Iniciando publicacion de {post_id}...")

    # Ejecutar en background
    try:
        from auto_publish import run
        run(post_id=post_id)
        await update.message.reply_text(f"Post {post_id} procesado.")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


async def cmd_pause(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return
    try:
        from queue_manager import pause_all
        pause_all()
        await update.message.reply_text("Cola pausada.")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


async def cmd_resume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return
    try:
        from queue_manager import resume_all
        resume_all()
        await update.message.reply_text("Cola reanudada.")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


async def cmd_retry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return
    try:
        from queue_manager import retry_failed
        retry_failed()
        await update.message.reply_text("Posts fallidos reencolados.")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancela un post: /cancel post_001"""
    if not is_authorized(update):
        return
    if not context.args:
        await update.message.reply_text("Uso: /cancel <post_id>")
        return

    post_id = context.args[0]
    cal_file = ROOT_DIR / "config" / "calendar.json"
    with open(cal_file, "r", encoding="utf-8") as f:
        cal = json.load(f)

    for p in cal.get("posts", []):
        if p["id"] == post_id:
            p["status"] = "cancelled"
            with open(cal_file, "w", encoding="utf-8") as f:
                json.dump(cal, f, indent=2, ensure_ascii=False)
            await update.message.reply_text(f"Post {post_id} cancelado.")
            return

    await update.message.reply_text(f"Post {post_id} no encontrado.")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await cmd_start(update, context)


# ============================================================
# Main
# ============================================================

def main():
    banner("TELEGRAM BOT - COMFYUI SOCIAL SUITE")

    if not HAS_TG:
        error("python-telegram-bot no instalado.")
        error("  pip install python-telegram-bot")
        sys.exit(1)

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        error("TELEGRAM_BOT_TOKEN no configurado en .env")
        error("  1. Crea un bot con @BotFather en Telegram")
        error("  2. Copia el token a .env: TELEGRAM_BOT_TOKEN=...")
        sys.exit(1)

    allowed = get_allowed_users()
    if not allowed:
        warn("TELEGRAM_ALLOWED_USER_IDS vacio. Nadie podra usar el bot.")
        warn("  Anade tu user ID a .env")
    else:
        ok(f"Usuarios autorizados: {allowed}")

    info("Iniciando bot...")

    # Configurar logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    # Silenciar httpx
    logging.getLogger("httpx").setLevel(logging.WARNING)

    app = Application.builder().token(token).build()

    # Handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("pending", cmd_pending))
    app.add_handler(CommandHandler("gen", cmd_gen))
    app.add_handler(CommandHandler("publish", cmd_publish))
    app.add_handler(CommandHandler("pause", cmd_pause))
    app.add_handler(CommandHandler("resume", cmd_resume))
    app.add_handler(CommandHandler("retry", cmd_retry))
    app.add_handler(CommandHandler("cancel", cmd_cancel))

    info("Bot listo. Ctrl+C para detener.")
    print()
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
