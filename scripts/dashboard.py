"""
dashboard.py - Web dashboard simple para monitorizar el ComfyUI Social Suite

Muestra en tiempo real:
  - Estado de ComfyUI (alive, GPU, VRAM)
  - Estado de la cola (pending, processing, completed, failed)
  - Ultimos posts publicados
  - Logs recientes
  - Botones para: pausar/reanudar cola, reintentar fallidos

Corre en http://127.0.0.1:8080

Uso:
    python dashboard.py
    python dashboard.py --port 8080 --host 0.0.0.0
"""
import os
import sys
import json
import time
import subprocess
import argparse
import sqlite3
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import ROOT_DIR

try:
    from flask import Flask, jsonify, render_template_string, request
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False
    print("ERROR: Flask no instalado. pip install flask")
    sys.exit(1)


app = Flask(__name__)


# ============================================================
# Helpers
# ============================================================

def check_port(port):
    """Verifica si un puerto esta escuchando."""
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        result = s.connect_ex(("127.0.0.1", port))
        s.close()
        return result == 0
    except Exception:
        return False


def get_comfyui_status():
    """Obtiene estado de ComfyUI via API."""
    try:
        from comfyui_api_client import ComfyUIClient
        client = ComfyUIClient()
        if not client.is_alive(timeout=2):
            return {"alive": False}
        stats = client.get_system_stats()
        # Extraer info util
        sys_stats = stats.get("system", {})
        devices = stats.get("devices", [])
        gpu_info = {}
        if devices:
            d = devices[0]
            gpu_info = {
                "name": d.get("name", ""),
                "type": d.get("type", ""),
                "vram_total": d.get("vram_total", 0) // (1024*1024),
                "vram_free": d.get("vram_free", 0) // (1024*1024),
            }
        return {
            "alive": True,
            "ram_total": sys_stats.get("ram_total", 0) // (1024*1024),
            "ram_free": sys_stats.get("ram_free", 0) // (1024*1024),
            "gpu": gpu_info,
        }
    except Exception as e:
        return {"alive": False, "error": str(e)}


def get_queue_status():
    """Obtiene estado de la cola SQLite."""
    try:
        from queue_manager import get_status
        return get_status()
    except Exception:
        return {}


def get_recent_posts(limit=10):
    """Obtiene ultimos posts del calendar."""
    cal_file = ROOT_DIR / "config" / "calendar.json"
    if not cal_file.exists():
        return []
    try:
        with open(cal_file, "r", encoding="utf-8") as f:
            cal = json.load(f)
        posts = cal.get("posts", [])
        # Ordenar por updated_at descendente
        posts.sort(key=lambda p: p.get("updated_at", ""), reverse=True)
        return posts[:limit]
    except Exception:
        return []


def get_recent_logs(log_name="comfyui", lines=20):
    """Lee las ultimas N lineas de un log."""
    log_file = ROOT_DIR / "logs" / f"{log_name}.log"
    if not log_file.exists():
        return []
    try:
        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            all_lines = f.readlines()
        return all_lines[-lines:]
    except Exception:
        return []


def get_analytics_summary():
    """Resumen de analytics si existe."""
    db_path = ROOT_DIR / "analytics.db"
    if not db_path.exists():
        return None
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT platform, COUNT(*) as n, SUM(likes) as likes,
                   AVG(engagement_rate) as er
            FROM analytics GROUP BY platform
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return None


# ============================================================
# Routes
# ============================================================

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route("/api/status")
def api_status():
    """Devuelve JSON con estado completo."""
    return jsonify({
        "comfyui": get_comfyui_status(),
        "queue": get_queue_status(),
        "services": {
            "comfyui": check_port(8188),
            "webhook_server": check_port(8189),
            "dashboard": check_port(8080),
            "telegram_bot": _check_telegram_running(),
        },
        "posts": get_recent_posts(5),
        "analytics": get_analytics_summary(),
        "timestamp": datetime.now().isoformat(),
    })


def _check_telegram_running():
    """Verifica si el bot telegram esta corriendo."""
    pid_file = ROOT_DIR / "run" / "telegram_bot.pid"
    if not pid_file.exists():
        return False
    try:
        pid = int(pid_file.read_text().strip())
        os.kill(pid, 0)
        return True
    except Exception:
        return False


@app.route("/api/logs/<log_name>")
def api_logs(log_name):
    """Devuelve las ultimas lineas de un log."""
    if log_name not in ("comfyui", "queue_worker", "webhook_server",
                        "telegram_bot", "dashboard", "auto_publish"):
        return jsonify({"error": "Log no permitido"}), 400
    lines = request.args.get("lines", 50, type=int)
    return jsonify({"lines": get_recent_logs(log_name, lines)})


@app.route("/api/queue/<action>", methods=["POST"])
def api_queue_action(action):
    """Control de cola: pause, resume, retry-failed."""
    try:
        from queue_manager import pause_all, resume_all, retry_failed
        if action == "pause":
            pause_all()
            return jsonify({"success": True, "message": "Cola pausada"})
        elif action == "resume":
            resume_all()
            return jsonify({"success": True, "message": "Cola reanudada"})
        elif action == "retry-failed":
            retry_failed()
            return jsonify({"success": True, "message": "Fallidos reencolados"})
        else:
            return jsonify({"error": "Accion no valida"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/posts")
def api_posts():
    """Lista todos los posts."""
    return jsonify({"posts": get_recent_posts(50)})


# ============================================================
# HTML Template
# ============================================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ComfyUI Social Suite - Dashboard</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      background: #1A1A2E;
      color: #F0E6D2;
      padding: 20px;
    }
    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 30px;
      padding-bottom: 15px;
      border-bottom: 1px solid #3C3C5C;
    }
    .header h1 {
      color: #FFB266;
      font-size: 24px;
    }
    .header .timestamp {
      color: #B5A642;
      font-size: 13px;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 20px;
      margin-bottom: 30px;
    }
    .card {
      background: #16213E;
      border: 1px solid #3C3C5C;
      border-radius: 8px;
      padding: 20px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    .card h2 {
      color: #FFB266;
      font-size: 16px;
      margin-bottom: 15px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .status-row {
      display: flex;
      justify-content: space-between;
      padding: 8px 0;
      border-bottom: 1px solid #2D2D44;
    }
    .status-row:last-child { border-bottom: none; }
    .status-label { color: #B5A642; }
    .status-value { font-weight: 500; }
    .badge {
      display: inline-block;
      padding: 4px 10px;
      border-radius: 4px;
      font-size: 12px;
      font-weight: 600;
    }
    .badge-online { background: #3a784e; color: #fff; }
    .badge-offline { background: #aa534b; color: #fff; }
    .badge-pending { background: #b38f46; color: #fff; }
    .badge-success { background: #3a784e; color: #fff; }
    .badge-failed { background: #aa534b; color: #fff; }
    .badge-published { background: #4a749e; color: #fff; }
    .actions {
      display: flex;
      gap: 10px;
      margin-top: 15px;
    }
    .btn {
      background: #2D2D44;
      color: #F0E6D2;
      border: 1px solid #3C3C5C;
      padding: 8px 14px;
      border-radius: 6px;
      cursor: pointer;
      font-size: 13px;
      transition: all 0.15s;
    }
    .btn:hover { background: #3C3C5C; }
    .btn-primary { background: #FFB266; color: #1A1A2E; border: none; font-weight: 600; }
    .btn-primary:hover { background: #FFA931; }
    .posts-list { max-height: 300px; overflow-y: auto; }
    .post-item {
      padding: 10px 0;
      border-bottom: 1px solid #2D2D44;
      font-size: 13px;
    }
    .post-id { color: #FFB266; font-weight: 600; }
    .post-prompt { color: #F0E6D2; margin-top: 4px; }
    .progress-bar {
      background: #2D2D44;
      border-radius: 4px;
      height: 8px;
      margin-top: 8px;
      overflow: hidden;
    }
    .progress-fill {
      background: #FFB266;
      height: 100%;
      transition: width 0.3s;
    }
    .footer {
      text-align: center;
      color: #B5A642;
      font-size: 12px;
      margin-top: 30px;
      padding-top: 15px;
      border-top: 1px solid #3C3C5C;
    }
    a { color: #FFB266; text-decoration: none; }
    a:hover { text-decoration: underline; }
  </style>
</head>
<body>
  <div class="header">
    <h1>ComfyUI Social Suite - Dashboard</h1>
    <div class="timestamp" id="timestamp">Cargando...</div>
  </div>

  <div class="grid">
    <!-- ComfyUI Status -->
    <div class="card">
      <h2>ComfyUI</h2>
      <div id="comfyui-status">Cargando...</div>
      <div class="actions">
        <a href="http://127.0.0.1:8188" target="_blank" class="btn">Abrir ComfyUI</a>
      </div>
    </div>

    <!-- Queue Status -->
    <div class="card">
      <h2>Cola de Publicacion</h2>
      <div id="queue-status">Cargando...</div>
      <div class="actions">
        <button class="btn" onclick="queueAction('pause')">Pausar</button>
        <button class="btn" onclick="queueAction('resume')">Reanudar</button>
        <button class="btn btn-primary" onclick="queueAction('retry-failed')">Reintentar fallidos</button>
      </div>
    </div>

    <!-- Services -->
    <div class="card">
      <h2>Servicios</h2>
      <div id="services-status">Cargando...</div>
    </div>

    <!-- Analytics -->
    <div class="card" id="analytics-card" style="display:none;">
      <h2>Analytics</h2>
      <div id="analytics-content"></div>
    </div>
  </div>

  <!-- Posts recientes -->
  <div class="card" style="margin-bottom: 30px;">
    <h2>Posts Recientes</h2>
    <div class="posts-list" id="posts-list">Cargando...</div>
  </div>

  <div class="footer">
    ComfyUI Social Suite &middot; <a href="https://github.com/yecos/playcanvas" target="_blank">github.com/yecos/playcanvas</a>
    &middot; Auto-refresh cada 5s
  </div>

  <script>
    async function fetchStatus() {
      try {
        const r = await fetch('/api/status');
        const data = await r.json();
        renderStatus(data);
      } catch (e) {
        document.getElementById('timestamp').textContent = 'Error: ' + e.message;
      }
    }

    function renderStatus(data) {
      // Timestamp
      document.getElementById('timestamp').textContent =
        'Actualizado: ' + new Date(data.timestamp).toLocaleTimeString();

      // ComfyUI
      const cu = data.comfyui;
      let cuHtml = '';
      if (cu.alive) {
        cuHtml += '<div class="status-row"><span class="status-label">Estado</span><span class="badge badge-online">ONLINE</span></div>';
        if (cu.gpu && cu.gpu.name) {
          cuHtml += '<div class="status-row"><span class="status-label">GPU</span><span class="status-value">' + cu.gpu.name + '</span></div>';
          const vramTotal = (cu.gpu.vram_total / 1024).toFixed(1);
          const vramFree = (cu.gpu.vram_free / 1024).toFixed(1);
          const used = (vramTotal - vramFree).toFixed(1);
          const usedPct = (used / vramTotal * 100).toFixed(0);
          cuHtml += '<div class="status-row"><span class="status-label">VRAM</span><span class="status-value">' + used + ' / ' + vramTotal + ' GB</span></div>';
          cuHtml += '<div class="progress-bar"><div class="progress-fill" style="width:' + usedPct + '%"></div></div>';
        }
      } else {
        cuHtml = '<div class="status-row"><span class="status-label">Estado</span><span class="badge badge-offline">OFFLINE</span></div>';
        if (cu.error) cuHtml += '<div class="status-row"><span class="status-label">Error</span><span class="status-value">' + cu.error + '</span></div>';
      }
      document.getElementById('comfyui-status').innerHTML = cuHtml;

      // Queue
      const q = data.queue;
      let qHtml = '';
      const states = ['pending', 'processing', 'completed', 'failed', 'paused'];
      states.forEach(s => {
        if (q[s]) {
          const cls = s === 'failed' ? 'badge-failed' : (s === 'completed' ? 'badge-success' : 'badge-pending');
          qHtml += '<div class="status-row"><span class="status-label">' + s + '</span><span class="badge ' + cls + '">' + q[s] + '</span></div>';
        }
      });
      if (!qHtml) qHtml = '<div class="status-row"><span class="status-label">Cola vacia</span><span class="badge badge-success">OK</span></div>';
      document.getElementById('queue-status').innerHTML = qHtml;

      // Services
      const sv = data.services;
      let svHtml = '';
      const services = [
        ['ComfyUI (8188)', sv.comfyui],
        ['Webhook Server (8189)', sv.webhook_server],
        ['Dashboard (8080)', sv.dashboard],
        ['Telegram Bot', sv.telegram_bot],
      ];
      services.forEach(([name, alive]) => {
        svHtml += '<div class="status-row"><span class="status-label">' + name + '</span><span class="badge ' + (alive ? 'badge-online' : 'badge-offline') + '">' + (alive ? 'ONLINE' : 'OFFLINE') + '</span></div>';
      });
      document.getElementById('services-status').innerHTML = svHtml;

      // Analytics
      if (data.analytics && data.analytics.length > 0) {
        document.getElementById('analytics-card').style.display = 'block';
        let aHtml = '';
        data.analytics.forEach(a => {
          aHtml += '<div class="status-row"><span class="status-label">' + a.platform + '</span><span class="status-value">' + a.n + ' posts, ' + (a.likes||0) + ' likes, ER ' + (a.er||0).toFixed(2) + '%</span></div>';
        });
        document.getElementById('analytics-content').innerHTML = aHtml;
      }

      // Posts
      const posts = data.posts || [];
      let pHtml = '';
      if (posts.length === 0) {
        pHtml = '<div class="post-item">No hay posts aun. Crea calendar.json con python scripts/calendar_generator.py --days 30</div>';
      } else {
        posts.forEach(p => {
          const cls = p.status === 'published' ? 'badge-published' :
                      (p.status === 'failed' ? 'badge-failed' :
                      (p.status === 'completed' ? 'badge-success' : 'badge-pending'));
          pHtml += '<div class="post-item"><span class="post-id">' + p.id + '</span> <span class="badge ' + cls + '">' + p.status + '</span><div class="post-prompt">' + (p.prompt || '').substring(0, 80) + '...</div></div>';
        });
      }
      document.getElementById('posts-list').innerHTML = pHtml;
    }

    async function queueAction(action) {
      try {
        const r = await fetch('/api/queue/' + action, { method: 'POST' });
        const data = await r.json();
        alert(data.message || data.error);
        fetchStatus();
      } catch (e) {
        alert('Error: ' + e.message);
      }
    }

    // Auto-refresh cada 5 segundos
    fetchStatus();
    setInterval(fetchStatus, 5000);
  </script>
</body>
</html>
"""


# ============================================================
# Main
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Dashboard del ComfyUI Social Suite")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()

    print(f"\n  Dashboard disponible en: http://{args.host}:{args.port}\n")
    print("  Ctrl+C para detener.\n")

    app.run(host=args.host, port=args.port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
