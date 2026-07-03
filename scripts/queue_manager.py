"""
queue_manager.py - Cola persistente SQLite con reintentos y prioridades

Reemplaza el procesamiento directo del calendar.json con una cola robusta:
  - Persistente ante crashes (estado en SQLite)
  - Reintentos con backoff exponencial
  - Prioridades (low=0, normal=1, high=2, urgent=3)
  - Pause/resume de la cola
  - Tracking de intentos, errores, tiempos

Schema:
  CREATE TABLE queue (
    id INTEGER PRIMARY KEY,
    post_id TEXT UNIQUE,
    payload TEXT,           -- JSON con todo el post
    status TEXT,            -- pending|processing|completed|failed|paused
    priority INTEGER,
    attempts INTEGER,
    max_attempts INTEGER,
    last_error TEXT,
    created_at TIMESTAMP,
    scheduled_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
  );

Uso:
    # Encolar todos los posts pendientes del calendar
    python queue_manager.py enqueue

    # Worker continuo
    python queue_manager.py worker

    # Ver estado
    python queue_manager.py status

    # Reintentar fallidos
    python queue_manager.py retry-failed
"""
import os
import sys
import json
import time
import sqlite3
import argparse
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import cprint, info, ok, warn, error, banner, ROOT_DIR

DB_PATH = ROOT_DIR / "queue.db"


# ============================================================
# Database initialization
# ============================================================

def init_db():
    """Crea la tabla queue si no existe."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id TEXT UNIQUE NOT NULL,
            payload TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            priority INTEGER DEFAULT 1,
            attempts INTEGER DEFAULT 0,
            max_attempts INTEGER DEFAULT 3,
            last_error TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            scheduled_at TIMESTAMP,
            started_at TIMESTAMP,
            completed_at TIMESTAMP
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON queue(status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_priority ON queue(priority DESC)")
    conn.commit()
    conn.close()


def get_conn():
    """Devuelve conexion con row_factory."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================
# Queue operations
# ============================================================

def enqueue_post(post: Dict, priority: int = 1,
                 scheduled_at: Optional[str] = None) -> bool:
    """Anade un post a la cola. Devuelve True si fue anadido nuevo."""
    post_id = post.get("id")
    if not post_id:
        error("Post sin 'id'")
        return False

    init_db()
    conn = get_conn()
    try:
        conn.execute(
            """INSERT OR IGNORE INTO queue
               (post_id, payload, status, priority, scheduled_at)
               VALUES (?, ?, 'pending', ?, ?)""",
            (post_id, json.dumps(post, ensure_ascii=False),
             priority, scheduled_at)
        )
        conn.commit()
        affected = conn.total_changes
        return affected > 0
    finally:
        conn.close()


def enqueue_from_calendar():
    """Encola todos los posts pendientes del calendar.json."""
    cal_file = ROOT_DIR / "config" / "calendar.json"
    if not cal_file.exists():
        error("calendar.json no existe")
        return 0

    with open(cal_file, "r", encoding="utf-8") as f:
        cal = json.load(f)

    enqueued = 0
    for post in cal.get("posts", []):
        if post.get("status") != "pending":
            continue
        # Prioridad basada en scheduled_at
        priority = 1  # normal
        sched = post.get("scheduled_at")
        if sched:
            try:
                sched_dt = datetime.fromisoformat(sched.replace("Z", ""))
                if sched_dt < datetime.now():
                    priority = 2  # high (atrasado)
            except Exception:
                pass
        if enqueue_post(post, priority=priority, scheduled_at=sched):
            enqueued += 1
            ok(f"Encolado: {post['id']} (priority={priority})")

    return enqueued


def claim_next() -> Optional[Dict]:
    """
    Marca como 'processing' el siguiente post pendiente y lo devuelve.
    Implementa atomic claim con UPDATE...WHERE status='pending' LIMIT 1.
    """
    init_db()
    conn = get_conn()
    try:
        # SQLite no soporta UPDATE...LIMIT sin compile option
        # Usamos transaction explicita
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            """SELECT * FROM queue
               WHERE status = 'pending'
                 AND (scheduled_at IS NULL OR scheduled_at <= CURRENT_TIMESTAMP)
               ORDER BY priority DESC, created_at ASC
               LIMIT 1"""
        ).fetchone()

        if not row:
            conn.rollback()
            return None

        conn.execute(
            """UPDATE queue
               SET status = 'processing',
                   started_at = CURRENT_TIMESTAMP,
                   attempts = attempts + 1
               WHERE id = ?""",
            (row["id"],)
        )
        conn.commit()

        return {
            "id": row["id"],
            "post_id": row["post_id"],
            "payload": json.loads(row["payload"]),
            "attempts": row["attempts"] + 1,
            "max_attempts": row["max_attempts"],
        }
    except Exception as e:
        conn.rollback()
        error(f"Error claiming next: {e}")
        return None
    finally:
        conn.close()


def mark_completed(post_id: str, result: Optional[Dict] = None):
    """Marca un post como completado."""
    init_db()
    conn = get_conn()
    try:
        conn.execute(
            """UPDATE queue
               SET status = 'completed',
                   completed_at = CURRENT_TIMESTAMP,
                   last_error = NULL
               WHERE post_id = ?""",
            (post_id,)
        )
        conn.commit()
    finally:
        conn.close()


def mark_failed(post_id: str, error_msg: str,
                max_attempts: int = 3):
    """
    Marca como fallido. Si aun quedan intentos, vuelve a pending.
    Si agoto intentos, marca como failed definitivo.
    """
    init_db()
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT attempts, max_attempts FROM queue WHERE post_id = ?",
            (post_id,)
        ).fetchone()

        if not row:
            return

        if row["attempts"] >= row["max_attempts"]:
            # Agotado
            conn.execute(
                """UPDATE queue
                   SET status = 'failed',
                       last_error = ?,
                       completed_at = CURRENT_TIMESTAMP
                   WHERE post_id = ?""",
                (error_msg[:500], post_id)
            )
            error(f"Post {post_id} FALLO definitivamente: {error_msg}")
        else:
            # Reintentar con backoff exponencial
            # 1er reintento: +60s, 2do: +300s, 3ro: +900s
            delays = [60, 300, 900, 1800]
            delay = delays[min(row["attempts"] - 1, len(delays) - 1)]
            next_run = (datetime.now() + timedelta(seconds=delay)).isoformat()
            conn.execute(
                """UPDATE queue
                   SET status = 'pending',
                       last_error = ?,
                       scheduled_at = ?
                   WHERE post_id = ?""",
                (error_msg[:500], next_run, post_id)
            )
            warn(f"Post {post_id} fallo (intento {row['attempts']}/{row['max_attempts']}). "
                 f"Reintento en {delay}s")
        conn.commit()
    finally:
        conn.close()


def retry_failed():
    """Resetea todos los posts failed a pending con attempts=0."""
    init_db()
    conn = get_conn()
    try:
        conn.execute(
            """UPDATE queue
               SET status = 'pending', attempts = 0, last_error = NULL
               WHERE status = 'failed'"""
        )
        n = conn.total_changes
        conn.commit()
        ok(f"{n} posts reencolados para reintento")
        return n
    finally:
        conn.close()


def pause_all():
    """Pausa toda la cola (pending -> paused)."""
    init_db()
    conn = get_conn()
    try:
        conn.execute(
            "UPDATE queue SET status = 'paused' WHERE status = 'pending'"
        )
        conn.commit()
        ok("Cola pausada")
    finally:
        conn.close()


def resume_all():
    """Reanuda la cola (paused -> pending)."""
    init_db()
    conn = get_conn()
    try:
        conn.execute(
            "UPDATE queue SET status = 'pending' WHERE status = 'paused'"
        )
        conn.commit()
        ok("Cola reanudada")
    finally:
        conn.close()


def get_status() -> Dict:
    """Devuelve estadisticas de la cola."""
    init_db()
    conn = get_conn()
    try:
        rows = conn.execute(
            """SELECT status, COUNT(*) as count
               FROM queue GROUP BY status"""
        ).fetchall()
        return {r["status"]: r["count"] for r in rows}
    finally:
        conn.close()


# ============================================================
# Worker
# ============================================================

def worker_loop(max_iterations: Optional[int] = None,
                poll_interval: int = 10):
    """
    Bucle del worker. Procesa jobs hasta que no haya mas o se alcance max_iterations.
    """
    banner("QUEUE WORKER INICIADO")
    info(f"Poll interval: {poll_interval}s")
    info(f"DB: {DB_PATH}")
    print()

    iteration = 0
    while True:
        if max_iterations is not None and iteration >= max_iterations:
            info(f"Alcanzado max_iterations={max_iterations}. Deteniendo.")
            break

        job = claim_next()
        if not job:
            # No hay jobs, esperar
            time.sleep(poll_interval)
            iteration += 1
            continue

        post_id = job["post_id"]
        post = job["payload"]
        attempts = job["attempts"]

        info(f"=== Procesando {post_id} (intento {attempts}) ===")
        info(f"  Workflow: {post.get('workflow')}")
        info(f"  Prompt: {post.get('prompt', '')[:80]}...")

        try:
            # Importar auto_publish y procesar
            from auto_publish import process_post, update_post_status
            from comfyui_api_client import ComfyUIClient

            client = ComfyUIClient()
            if not client.is_alive():
                raise RuntimeError("ComfyUI no responde")

            # Guardar prompt_id para matching con webhook
            result = process_post(post, client)

            if result.get("success"):
                mark_completed(post_id, result)
                ok(f"Post {post_id} completado")
            else:
                # Si fallo parcialmente, lo marcamos como completado igual
                # (las plataformas que funcionaron ya tienen el post)
                mark_completed(post_id, result)
                warn(f"Post {post_id} completado con warnings: {result.get('error', '')}")

        except Exception as e:
            error_msg = str(e)
            error(f"Post {post_id} fallo: {error_msg}")
            mark_failed(post_id, error_msg, max_attempts=3)

        iteration += 1
        print()


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Gestor de cola SQLite")
    subparsers = parser.add_subparsers(dest="command")

    p_enqueue = subparsers.add_parser("enqueue",
                                       help="Encolar posts pendientes del calendar")
    p_enqueue.add_argument("--priority", type=int, default=1,
                           choices=[0, 1, 2, 3])

    p_worker = subparsers.add_parser("worker", help="Iniciar worker continuo")
    p_worker.add_argument("--max-iterations", type=int,
                          help="Max iteraciones (None = infinito)")
    p_worker.add_argument("--poll-interval", type=int, default=10)

    subparsers.add_parser("status", help="Ver estado de la cola")
    subparsers.add_parser("retry-failed", help="Reintentar posts failed")
    subparsers.add_parser("pause", help="Pausar cola")
    subparsers.add_parser("resume", help="Reanudar cola")
    subparsers.add_parser("reset", help="Borrar cola (USAR CON CUIDADO)")

    args = parser.parse_args()

    if args.command == "enqueue":
        n = enqueue_from_calendar()
        ok(f"{n} posts encolados")

    elif args.command == "worker":
        worker_loop(max_iterations=args.max_iterations,
                    poll_interval=args.poll_interval)

    elif args.command == "status":
        status = get_status()
        banner("ESTADO DE LA COLA")
        if not status:
            info("Cola vacia")
        else:
            for state, count in status.items():
                cprint(f"  {state:15} : {count}", '\033[96m')

    elif args.command == "retry-failed":
        retry_failed()

    elif args.command == "pause":
        pause_all()

    elif args.command == "resume":
        resume_all()

    elif args.command == "reset":
        init_db()
        conn = get_conn()
        conn.execute("DELETE FROM queue")
        conn.commit()
        conn.close()
        warn("Cola borrada")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
