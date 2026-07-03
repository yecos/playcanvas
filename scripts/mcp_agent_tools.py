"""
mcp_agent_tools.py - Expone el ComfyUI Social Suite como servidor MCP (Model Context Protocol)

Permite que agentes AI como Claude Desktop, Hermes, Cursor, etc. controlen el suite
via tools estandarizadas MCP:

Tools disponibles:
  - list_workflows: lista workflows disponibles
  - enqueue_job: encola un post en la cola SQLite
  - get_job_status: consulta estado de un job
  - list_pending: lista posts pendientes
  - publish_now: fuerza publicacion inmediata
  - pause_queue / resume_queue: controla la cola
  - get_analytics: obtiene metricas agregadas
  - generate_caption: genera caption con LLM

Uso:
    python mcp_agent_tools.py

Configurar en Claude Desktop / Hermes:
    {
      "mcpServers": {
        "comfyui-social": {
          "command": "python",
          "args": ["/ruta/a/scripts/mcp_agent_tools.py"],
          "env": {"PYTHONPATH": "/ruta/a/scripts"}
        }
      }
    }
"""
import os
import sys
import json
import asyncio
import argparse
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import cprint, info, ok, warn, error, banner, ROOT_DIR

try:
    from mcp.server import Server
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    HAS_MCP = True
except ImportError:
    HAS_MCP = False


# ============================================================
# Tool definitions
# ============================================================

def get_tool_definitions() -> List[Tool]:
    """Define todas las tools MCP disponibles."""
    return [
        Tool(
            name="list_workflows",
            description="Lista todos los workflows disponibles en el suite",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="enqueue_job",
            description="""Encola un nuevo post para generacion y publicacion automatica.

Argumentos:
  - workflow: nombre del workflow (ej: instagram_post, tiktok_video)
  - prompt: prompt de generacion de imagen
  - platforms: lista de plataformas (instagram, twitter, facebook, etc.)
  - caption: caption del post (opcional, se genera con LLM si no se especifica)
  - scheduled_at: fecha ISO para publicacion programada (opcional)
""",
            inputSchema={
                "type": "object",
                "properties": {
                    "workflow": {"type": "string",
                                 "description": "Nombre del workflow"},
                    "prompt": {"type": "string",
                              "description": "Prompt de generacion"},
                    "platforms": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Plataformas objetivo",
                        "default": ["instagram"]
                    },
                    "caption": {"type": "string",
                               "description": "Caption del post"},
                    "scheduled_at": {"type": "string",
                                    "description": "ISO datetime"}
                },
                "required": ["workflow", "prompt"]
            }
        ),
        Tool(
            name="get_job_status",
            description="Obtiene el estado de un job por post_id",
            inputSchema={
                "type": "object",
                "properties": {
                    "post_id": {"type": "string"}
                },
                "required": ["post_id"]
            }
        ),
        Tool(
            name="list_pending",
            description="Lista los posts pendientes en la cola",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="publish_now",
            description="Fuerza la publicacion inmediata de un post",
            inputSchema={
                "type": "object",
                "properties": {
                    "post_id": {"type": "string"}
                },
                "required": ["post_id"]
            }
        ),
        Tool(
            name="pause_queue",
            description="Pausa la cola de publicacion",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="resume_queue",
            description="Reanuda la cola de publicacion",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="get_analytics",
            description="Obtiene metricas agregadas de engagement",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="generate_caption",
            description="Genera un caption usando LLM",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string",
                              "description": "Prompt de la imagen"},
                    "platform": {"type": "string",
                                "default": "instagram"}
                },
                "required": ["prompt"]
            }
        ),
    ]


# ============================================================
# Tool handlers
# ============================================================

async def handle_tool_call(name: str, arguments: Dict) -> str:
    """Ejecuta una tool y devuelve el resultado como string."""

    if name == "list_workflows":
        workflows_dir = ROOT_DIR / "workflows"
        workflows = []
        for f in sorted(workflows_dir.glob("*.json")):
            if f.name == "README.md":
                continue
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                meta = data.get("_meta", {})
                workflows.append({
                    "name": f.stem,
                    "title": meta.get("title", f.stem),
                    "platform": meta.get("platform", "unknown"),
                    "format": meta.get("format", ""),
                    "description": meta.get("description", "")[:200]
                })
            except Exception:
                workflows.append({"name": f.stem, "error": "invalid JSON"})
        return json.dumps(workflows, indent=2, ensure_ascii=False)

    elif name == "enqueue_job":
        # Crear post en calendar
        cal_file = ROOT_DIR / "config" / "calendar.json"
        with open(cal_file, "r", encoding="utf-8") as f:
            cal = json.load(f)

        post_id = f"mcp_{int(asyncio.get_event_loop().time() * 1000)}"
        post = {
            "id": post_id,
            "status": "pending",
            "workflow": arguments["workflow"],
            "prompt": arguments["prompt"],
            "caption": arguments.get("caption", arguments["prompt"][:2200]),
            "platforms": arguments.get("platforms", ["instagram"]),
            "scheduled_at": arguments.get("scheduled_at"),
            "created_at": __import__("datetime").datetime.now().isoformat(),
            "created_via": "mcp_agent",
        }
        cal.setdefault("posts", []).append(post)
        with open(cal_file, "w", encoding="utf-8") as f:
            json.dump(cal, f, indent=2, ensure_ascii=False)

        # Encolar en queue_manager si esta disponible
        try:
            from queue_manager import enqueue_post
            enqueue_post(post)
        except Exception:
            pass

        return json.dumps({"success": True, "post_id": post_id})

    elif name == "get_job_status":
        post_id = arguments["post_id"]
        cal_file = ROOT_DIR / "config" / "calendar.json"
        with open(cal_file, "r", encoding="utf-8") as f:
            cal = json.load(f)

        for p in cal.get("posts", []):
            if p["id"] == post_id:
                return json.dumps(p, indent=2, ensure_ascii=False,
                                  default=str)

        return json.dumps({"error": "Post no encontrado"})

    elif name == "list_pending":
        cal_file = ROOT_DIR / "config" / "calendar.json"
        with open(cal_file, "r", encoding="utf-8") as f:
            cal = json.load(f)

        pending = [p for p in cal.get("posts", []) if p.get("status") == "pending"]
        return json.dumps({
            "count": len(pending),
            "posts": [{"id": p["id"], "workflow": p.get("workflow"),
                       "prompt": p.get("prompt", "")[:80]}
                      for p in pending]
        }, indent=2, ensure_ascii=False)

    elif name == "publish_now":
        post_id = arguments["post_id"]
        try:
            from auto_publish import run
            run(post_id=post_id)
            return json.dumps({"success": True, "message": f"Post {post_id} publicado"})
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    elif name == "pause_queue":
        try:
            from queue_manager import pause_all
            pause_all()
            return json.dumps({"success": True})
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    elif name == "resume_queue":
        try:
            from queue_manager import resume_all
            resume_all()
            return json.dumps({"success": True})
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    elif name == "get_analytics":
        try:
            from analytics_collector import print_summary
            import io
            import contextlib
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                print_summary()
            return buf.getvalue()
        except Exception as e:
            return json.dumps({"error": str(e)})

    elif name == "generate_caption":
        try:
            from generate_caption import generate_caption
            caption = generate_caption(
                arguments["prompt"],
                arguments.get("platform", "instagram")
            )
            return caption
        except Exception as e:
            return json.dumps({"error": str(e)})

    return json.dumps({"error": f"Tool desconocida: {name}"})


# ============================================================
# MCP Server
# ============================================================

async def run_mcp_server():
    """Inicia el servidor MCP via stdio."""
    if not HAS_MCP:
        error("mcp no instalado. pip install mcp")
        sys.exit(1)

    server = Server("comfyui-social")

    @server.list_tools()
    async def list_tools() -> List[Tool]:
        return get_tool_definitions()

    @server.call_tool()
    async def call_tool(name: str, arguments: Dict) -> List[TextContent]:
        result = await handle_tool_call(name, arguments)
        return [TextContent(type="text", text=result)]

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="comfyui-social",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None
                )
            )
        )


def main():
    parser = argparse.ArgumentParser(description="MCP Server para ComfyUI Social Suite")
    parser.add_argument("--list-tools", action="store_true",
                        help="Lista las tools disponibles y sale")
    args = parser.parse_args()

    if args.list_tools:
        banner("MCP TOOLS DISPONIBLES")
        for tool in get_tool_definitions():
            cprint(f"\n  {tool.name}", '\033[1m')
            cprint(f"    {tool.description}", '\033[96m')
        return

    banner("MCP SERVER - COMFYUI SOCIAL SUITE")
    info("Las siguientes tools estan expuestas:")
    for tool in get_tool_definitions():
        cprint(f"  - {tool.name}", '\033[96m')
    info("\nEsperando conexiones via stdio...")
    info("Configura tu cliente MCP (Claude/Hermes/Cursor) con este comando.")
    print()

    asyncio.run(run_mcp_server())


if __name__ == "__main__":
    main()
