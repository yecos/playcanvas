# ComfyUI Social Media Suite 🎨🎬

> Instalador todo-en-uno de **ComfyUI** optimizado para **RTX 3060 12GB** y orientado a la **creación de imágenes y videos para redes sociales** (Instagram, TikTok, YouTube, X/Twitter, Facebook, Pinterest). Incluye **orquestador Python** para automatizar publicación multi-plataforma y **integración con agentes AI** (Hermes, etc.) vía MCP.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform: Windows + Linux](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-blue)]()
[![GPU: RTX 3060 12GB](https://img.shields.io/badge/GPU-RTX%203060%2012GB-green)]()
[![Language: Español](https://img.shields.io/badge/Idioma-Espa%C3%B1ol-red)]()
[![ComfyUI](https://img.shields.io/badge/ComfyUI-Latest-orange)]()

---

## 📋 Tabla de Contenidos

- [¿Qué es esto?](#-qué-es-esto)
- [Requisitos del sistema](#-requisitos-del-sistema)
- [Instalación rápida](#-instalación-rápida)
- [Uso](#-uso)
- [Workflows incluidos](#-workflows-incluidos)
- [Modelos incluidos](#-modelos-incluidos)
- [Personalización](#-personalización)
- [Solución de problemas](#-solución-de-problemas)
- [Estructura del proyecto](#-estructura-del-proyecto)
- [Créditos](#-créditos)

---

## 🎯 ¿Qué es esto?

Este repositorio contiene un **instalador automático** que configura en tu PC todo lo necesario para usar ComfyUI como herramienta profesional de creación de contenido para redes sociales, **más un orquestador Python** que automatiza la generación y publicación multi-plataforma.

**El instalador hace todo por ti:**
1. ✅ Verifica que tu PC cumple los requisitos (GPU, Python, Git, CUDA)
2. ✅ Clona ComfyUI oficial
3. ✅ Crea un entorno virtual Python aislado
4. ✅ Instala PyTorch con soporte CUDA 12.1
5. ✅ Instala ComfyUI-Manager (gestor visual de extensiones)
6. ✅ Instala **17 custom nodes esenciales** (incluye WD14 Tagger, VideoHelperSuite, LLM party, Comfyroll, WebhookNotifier, MCP server)
7. ✅ Descarga modelos optimizados para 12GB VRAM (SDXL, Juggernaut, DreamShaper, Flux opcional, VAEs, ControlNets, AnimateDiff, Wan 2.1 opcional)
8. ✅ Copia **9 workflows preconfigurados** (Instagram, TikTok, YouTube, X, Pinterest, Carrusel, Video, Logo, Multi-Aspect-Ratio)
9. ✅ Crea accesos directos `start.bat` / `start.sh`

**Además, el orquestador `scripts/auto_publish.py`:**
- 🤖 Lee un calendario JSON con los posts pendientes
- 🎨 Ejecuta workflows vía ComfyUI API (REST + WebSocket)
- 📤 Publica automáticamente a Instagram, Twitter/X, Facebook, Pinterest
- ⏰ Soporta modo daemon (cron-style) para programación
- 🔌 Preparado para integración con Hermes Agent vía MCP

Cuando termine, tendrás un sistema **end-to-end** listo para producir y publicar contenido sin tocar nada más.

---

## 💻 Requisitos del sistema

### Mínimo (recomendado para RTX 3060 12GB)

| Componente | Requerido | Recomendado |
|------------|-----------|-------------|
| **GPU** | NVIDIA RTX 3060 12GB | RTX 4070 / 4080 / 4090 |
| **VRAM** | 12GB | 16GB+ |
| **RAM** | 16GB | 32GB |
| **Disco** | 100GB SSD libre | 500GB NVMe |
| **SO** | Windows 10/11, Ubuntu 22.04+ | Windows 11 |
| **Python** | 3.10 o 3.11 | 3.11 |
| **Git** | Cualquier versión reciente | Última |
| **CUDA** | Driver 525+ (CUDA 12.1) | Driver 550+ |

### Verificación rápida

Antes de instalar, asegúrate de que tienes:
- **Python 3.10 o 3.11** instalado: https://www.python.org/downloads/
- **Git** instalado: https://git-scm.com/downloads
- **Driver NVIDIA actualizado**: https://www.nvidia.com/Download/index.aspx

> ⚠️ **Nota sobre VRAM**: Si tienes 8GB o menos, edita `config/launch_args.txt` y añade `--lowvram`. El sistema funcionará pero más lento.

---

## 🚀 Instalación rápida

### Windows

```bat
1. Descarga o clona este repositorio
2. Haz doble clic en install.bat
3. Sigue las instrucciones en pantalla
4. Al finalizar, haz doble clic en start.bat
```

### Linux / macOS

```bash
git clone https://github.com/yecos/playcanvas.git comfyui-social
cd comfyui-social
chmod +x install.sh
./install.sh
```

La instalación tarda entre **30 y 90 minutos** dependiendo de tu conexión (descarga ~30GB de modelos).

---

## 🎬 Uso

### Iniciar ComfyUI

**Windows**: doble clic en `start.bat`
**Linux/macOS**: `./start.sh`

Se abrirá automáticamente tu navegador en `http://127.0.0.1:8188`.

### Cargar un workflow

1. Abre ComfyUI en el navegador
2. Arrastra el archivo JSON desde la carpeta `workflows/` a la ventana
3. Ajusta el prompt y dimensiones según tu red social
4. Pulsa **Queue Prompt** (o Ctrl+Enter)

### Formatos preconfigurados

| Red Social | Resolución | Workflow |
|------------|------------|----------|
| Instagram post | 1080×1080 | `instagram_post.json` |
| Instagram story/reel | 1080×1920 | `instagram_story.json` |
| TikTok | 1080×1920 | `tiktok_video.json` |
| YouTube thumbnail | 1280×720 | `youtube_thumbnail.json` |
| X/Twitter | 1200×675 | `twitter_post.json` |
| Carrusel (5 imgs) | 1080×1080 | `carousel_5.json` |
| Video corto animado | 1024×576 | `animatediff_video.json` |

---

## 🎨 Workflows incluidos

Todos están en la carpeta `workflows/`:

- **instagram_post.json** — Post cuadrado con SDXL + upscaler
- **instagram_story.json** — Story vertical con SDXL
- **tiktok_video.json** — Video vertical con AnimateDiff
- **youtube_thumbnail.json** — Miniatura 16:9 con SDXL
- **twitter_post.json** — Imagen 16:9 optimizada para X
- **carousel_5.json** — Genera 5 imágenes con estilo coherente
- **animatediff_video.json** — Video animado de 2 segundos en loop
- **logo_brand.json** — Generación de logos con LoRA de marca

---

## 📦 Modelos incluidos

Optimizados para **12GB VRAM** (RTX 3060):

### Checkpoints (~13GB)
- `sd_xl_base_1.0.safetensors` — SDXL base (6.5GB)
- `juggernautXL_v9.safetensors` — Realismo fotográfico (6.5GB)
- `dreamshaper_8.safetensors` — SD 1.5 rápido (2GB)

### VAE (~335MB)
- `sdxl_vae.safetensors` — VAE para SDXL
- `vae-ft-mse-840000-ema-pruned.safetensors` — VAE para SD 1.5

### LoRAs (~500MB)
- `detail_tweaker_xl.safetensors` — Mejora detalles
- `add_detail_xl.safetensors` — Aumenta detalle

### ControlNet (~5GB)
- `control_v11f1p_sd15_depth.pth`
- `control_v11p_sd15_canny.pth`
- `control_v11f1p_sd15_openpose.pth`

### AnimateDiff (~1.6GB)
- `mm_sd_v15_v2.ckpt` — Motion module para SD 1.5

### Upscalers (~200MB)
- `4x-UltraSharp.pth` — Upscaler general
- `RealESRGAN_x4plus.pth` — Upscaler alternativo

### Embeddings (~50MB)
- `bad_prompt_version2.pt` — Negative prompt
- `EasyNegative.safetensors` — Negative prompt

**Total descarga**: ~20-25GB

> 💡 Puedes editar `models_list.json` para añadir/quitar modelos antes de instalar.

---

## ⚙️ Personalización

### Cambiar argumentos de lanzamiento

Edita `config/launch_args.txt`. Opciones útiles para 12GB VRAM:

```
--preview-method auto
--front-end-handler Comfy.WebSocketHandler
--xformers
--fp16-vae
--use-pytorch-cross-attention
```

### Añadir tus propios modelos

Coloca archivos `.safetensors` en:
- `ComfyUI/models/checkpoints/` — checkpoints
- `ComfyUI/models/loras/` — LoRAs
- `ComfyUI/models/vae/` — VAEs
- `ComfyUI/models/controlnet/` — ControlNets

### Añadir custom nodes

1. Abre ComfyUI
2. Click en **Manager** (botón del ComfyUI-Manager)
3. **Install Custom Nodes**
4. Busca e instala lo que necesites
5. **Restart** para aplicar

---

## 🛠 Solución de problemas

### "CUDA out of memory"
- Edita `config/launch_args.txt` y añade `--lowvram`
- Usa modelos SD 1.5 en vez de SDXL
- Reduce las dimensiones a 768×768

### "ModuleNotFoundError: torch"
- Borra la carpeta `venv/` y vuelve a ejecutar `install.bat`

### ComfyUI-Manager no aparece
- Verifica que `ComfyUI/custom_nodes/ComfyUI-Manager/` existe
- Ejecuta `update.bat`

### Lento al generar
- Activa `--xformers` en launch_args
- Cierra Chrome/Discord mientras generas
- Baja la resolución y haz upscale después

### Descarga de modelos fallida
- Ejecuta `python scripts/download_models.py --retry`
- Revisa tu conexión (los modelos pesan GBs)
- Descarga manualmente desde los links en `docs/MODELS.md`

Más soluciones en **docs/TROUBLESHOOTING.md**.

---

## 📁 Estructura del proyecto

```
playcanvas/
├── install.bat / install.sh          # Instalador principal
├── start.bat / start.sh              # Lanzador de ComfyUI
├── update.bat / update.sh            # Actualizar todo
├── uninstall.bat / uninstall.sh      # Desinstalar
├── requirements.txt                  # Dependencias Python base
├── requirements_extended.txt         # Dependencias del orquestador
├── README.md                         # Este archivo
├── LICENSE                           # Licencia MIT
│
├── config/                           # Configuración
│   ├── launch_args.txt               # Argumentos de ComfyUI
│   ├── extra_model_paths.yaml        # Rutas de modelos externas
│   ├── calendar_template.json        # Plantilla de calendario
│   ├── calendar.json                 # Calendario activo (crear de template)
│   └── .env.example                  # Plantilla de credenciales
│
├── scripts/                          # Scripts Python
│   ├── check_system.py               # Verificación de requisitos
│   ├── download_models.py            # Descargador de modelos
│   ├── install_custom_nodes.py       # Instalador de custom nodes
│   ├── comfyui_api_client.py         # Wrapper API REST/WS de ComfyUI
│   ├── auto_publish.py               # Orquestador de publicación
│   └── utils.py                      # Utilidades compartidas
│
├── workflows/                        # Workflows JSON preconfigurados
│   ├── instagram_post.json
│   ├── instagram_story.json
│   ├── tiktok_video.json
│   ├── youtube_thumbnail.json
│   ├── twitter_post.json
│   ├── carousel_5.json
│   ├── animatediff_video.json
│   ├── logo_brand.json
│   └── cr_aspect_ratio_social.json   # 1 render → 4 crops multi-plataforma
│
├── docs/                             # Documentación
│   ├── INSTALL.md
│   ├── USAGE.md
│   ├── MODELS.md
│   ├── WORKFLOWS.md
│   ├── ARCHITECTURE.md               # Arquitectura del sistema
│   └── TROUBLESHOOTING.md
│
├── models_list.json                  # Catálogo de modelos
└── custom_nodes_list.json            # Catálogo de custom nodes
```

> **Nota**: La carpeta `ComfyUI/` se crea durante la instalación y **no se sube al repo** (está en `.gitignore`).

---

## 🤖 Orquestador de Publicación Automática

El sistema incluye `scripts/auto_publish.py` que automatiza todo el pipeline:

### Configuración rápida

1. **Copia credenciales**:
   ```bash
   cp config/.env.example .env
   # Edita .env con tus credenciales de IG, Twitter, FB, Pinterest
   ```

2. **Crea tu calendario**:
   ```bash
   cp config/calendar_template.json config/calendar.json
   # Edita calendar.json con tus posts
   ```

3. **Inicia ComfyUI**:
   ```bash
   start.bat  # o ./start.sh
   ```

4. **Ejecuta el orquestador** (en otra terminal):
   ```bash
   # Procesar todos los pendientes
   python scripts/auto_publish.py

   # Simular sin publicar
   python scripts/auto_publish.py --dry-run

   # Solo un post específico
   python scripts/auto_publish.py --once post_001

   # Solo Instagram
   python scripts/auto_publish.py --platforms instagram

   # Modo daemon continuo (cron)
   python scripts/auto_publish.py --daemon --interval 300
   ```

### Flujo del orquestador

```
calendar.json → carga posts pendientes
        ↓
para cada post:
    ↓
    carga workflow JSON
        ↓
    sustituye prompt/seed/dimensiones
        ↓
    POST /prompt a ComfyUI API
        ↓
    espera vía WebSocket
        ↓
    descarga imágenes generadas
        ↓
    publica a IG / X / FB / Pinterest
        ↓
    actualiza calendar.json (status=published)
```

Más detalles en **docs/ARCHITECTURE.md**.

---

## 🔌 Integración con Agentes AI (Hermes, etc.)

El sistema está preparado para integrarse con agentes AI autónomos:

### Vía MCP Server (recomendado)
El script `scripts/mcp_agent_tools.py` expone el suite como servidor MCP (Model Context Protocol). Cualquier agente compatible con MCP (Hermes Agent, Claude Desktop, Cursor, Continue.dev) puede:

- Listar workflows disponibles
- Encolar jobs con parámetros arbitrarios
- Consultar estado de jobs
- Pausar/reanudar cola
- Generar captions con LLM
- Obtener analytics

**Configurar en Claude Desktop** (ejemplo `claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "comfyui-social": {
      "command": "python",
      "args": ["/ruta/al/scripts/mcp_agent_tools.py"]
    }
  }
}
```

🔗 Doc oficial Hermes + ComfyUI: https://hermes-agent.nousresearch.com/docs/user-guide/skills/bundled/creative/creative-comfyui

### Vía API REST directa
El wrapper `scripts/comfyui_api_client.py` puede ser usado como tool por cualquier LLM con function calling.

### Vía n8n / Make.com (no-code)
Para integración visual sin código, usar n8n con el nodo `n8n-nodes-comfyui`.

Más detalles en **docs/ARCHITECTURE.md**.

---

## 🛡️ Seguridad y Moderación Anti-Ban

El sistema incluye `scripts/content_moderator.py` que se ejecuta automáticamente antes de publicar:

- **Detección NSFW en imagen** (vía transformers / CLIP-based classifier)
- **Filtro de profanidad** en captions (palabras banneas por plataforma)
- **Validación de policies** (TikTok/Meta exigen etiquetar contenido AI)
- **Bloqueo automático** si el contenido no pasa los checks

Personaliza palabras prohibidas en `scripts/content_moderator.py` (`BANNED_WORDS` y `PLATFORM_BANNED`).

---

## 🎨 Branding Automático

El script `scripts/brand_overlay.py` aplica tu branding consistente a todas las imágenes generadas:

1. Crea tu brand kit:
   ```bash
   python scripts/brand_overlay.py --init
   ```
2. Edita `config/brand_kit.yaml` con:
   - Logo PNG con transparencia
   - Handle de redes sociales (@tumarca)
   - Colores de marca
   - Fuente tipográfica
3. Cada post publicado llevará automáticamente tu logo + handle

---

## 🤖 Control Remoto vía Telegram

El script `scripts/bot_telegram.py` te permite controlar el sistema desde tu móvil:

```bash
python scripts/bot_telegram.py
```

**Comandos disponibles:**
- `/status` - Estado del sistema
- `/pending` - Posts pendientes
- `/gen <workflow> <prompt>` - Encolar generación
- `/publish <post_id>` - Publicar post
- `/pause` / `/resume` - Controlar cola
- `/retry` - Reintentar fallidos

Configura con `TELEGRAM_BOT_TOKEN` (vía @BotFather) y `TELEGRAM_ALLOWED_USER_IDS` en `.env`.

---

## 📊 Analytics de Engagement

El script `scripts/analytics_collector.py` recolecta métricas de cada post publicado:

```bash
python analytics_collector.py collect    # recolectar
python analytics_collector.py summary    # resumen por plataforma
python analytics_collector.py top        # top 10 por engagement
```

Métricas soportadas: likes, comments, shares, saves, impressions, reach, views, engagement_rate. Se guardan en `analytics.db` (SQLite).

---

## 🙏 Créditos

Este proyecto es un wrapper de instalación. Todo el mérito es de:

- **ComfyUI** por comfyanonymous: https://github.com/comfyanonymous/ComfyUI
- **ComfyUI-Manager** por comfy-org: https://github.com/comfy-org/ComfyUI-Manager
- **Stability AI** por Stable Diffusion XL
- **CivitAI** y la comunidad por LoRAs y modelos
- **AnimateDiff** por Yuwei Guo
- **ControlNet** por lllyasviel

Licencia: **MIT** — libre uso, modificación y distribución.

---

## 📞 Soporte

- 🐛 **Issues**: https://github.com/yecos/playcanvas/issues
- 📖 **Docs ComfyUI oficial**: https://docs.comfy.org/
- 💬 **Discord ComfyUI**: https://discord.gg/comfyorg

---

⭐ Si te resulta útil, deja una estrella en el repo.
