# Arquitectura del Sistema — ComfyUI Social Media Suite

## Visión General

ComfyUI Social Media Suite es un **pipeline automatizado de creación y publicación de contenido para redes sociales** que combina generación de imágenes/videos con IA, orquestación programática y publicación multi-plataforma.

El sistema está optimizado para **NVIDIA RTX 3060 12GB** y diseñado para operar localmente en un PC de escritorio, sin depender de servicios cloud (salvo las APIs oficiales de cada red social).

---

## Diagrama de Arquitectura

```
┌────────────────────────────────────────────────────────────────────┐
│                     CAPA DE ENTRADA / CALENDARIO                    │
│                                                                     │
│   config/calendar.json          Airtable / Notion (opcional)        │
│   ├─ post_001 (IG + X + FB)     └─ trigger por fecha/hora           │
│   ├─ post_002 (IG story)                                            │
│   └─ post_003 (YT thumbnail)                                        │
└──────────────────────────────┬─────────────────────────────────────┘
                               │
                               │ trigger
                               ▼
┌────────────────────────────────────────────────────────────────────┐
│                  CAPA DE ORQUESTACIÓN                               │
│                                                                     │
│   scripts/auto_publish.py                                           │
│   ├─ Lee posts pendientes del calendario                            │
│   ├─ Para cada post:                                                │
│   │   ├─ Carga workflow API Format JSON                            │
│   │   ├─ Sustituye prompt/seed/wh/dimensions                        │
│   │   ├─ Llama a ComfyUI API (/prompt + WebSocket /ws)              │
│   │   ├─ Espera finalizacion (WebSocket event)                      │
│   │   ├─ Descarga imagenes/videos generados (/view)                 │
│   │   ├─ (Opcional) Auto-genera caption con LLM                     │
│   │   └─ Publica a cada red social                                  │
│   └─ Marca post como published/partial/failed                       │
│                                                                     │
│   scripts/comfyui_api_client.py  ← Wrapper HTTP/WS de ComfyUI       │
└──────────────────────────────┬─────────────────────────────────────┘
                               │
                               │ HTTP + WebSocket
                               ▼
┌────────────────────────────────────────────────────────────────────┐
│                  CAPA DE GENERACIÓN (ComfyUI Local)                 │
│                                                                     │
│   ComfyUI  (http://127.0.0.1:8188)                                  │
│   ├─ Models: SDXL + Juggernaut XL + DreamShaper + Flux (opcional)   │
│   ├─ Custom Nodes:                                                  │
│   │   ├─ ComfyUI-Manager (gestor visual)                            │
│   │   ├─ ComfyUI-Impact-Pack (FaceDetailer, upscalers)              │
│   │   ├─ ComfyUI-VideoHelperSuite (load/save video)                 │
│   │   ├─ ComfyUI_WD14_Tagger (auto-captioning)                      │
│   │   ├─ comfyui_LLM_party (LLM para captions)                      │
│   │   ├─ ComfyUI_Comfyroll_CustomNodes (CR Aspect Ratio Social)     │
│   │   ├─ ComfyUI-WebhookNotifier (señal "terminé")                  │
│   │   ├─ ComfyUI-AnimateDiff-Evolved (videos animados)              │
│   │   ├─ comfyui_controlnet_aux (preprocessores)                    │
│   │   ├─ ComfyUI_IPAdapter_plus (consistencia de personaje)         │
│   │   └─ comfyui-mcp-server (puente MCP para agentes AI)            │
│   └─ Workflows preconfigurados (8):                                 │
│       instagram_post, instagram_story, tiktok_video,                │
│       youtube_thumbnail, twitter_post, carousel_5,                  │
│       animatediff_video, logo_brand, cr_aspect_ratio_social         │
└──────────────────────────────┬─────────────────────────────────────┘
                               │
                               │ imagen/video generados
                               ▼
┌────────────────────────────────────────────────────────────────────┐
│              CAPA DE PUBLICACIÓN (Multi-Plataforma)                 │
│                                                                     │
│   scripts/auto_publish.py → PUBLISHERS dict                         │
│   ├─ Instagram  → instagrapi (Python)                               │
│   ├─ Twitter/X  → tweepy (API v2 + v1.1 media)                      │
│   ├─ Facebook   → facebook-sdk (Graph API, page token)              │
│   ├─ Pinterest  → py3-pinterest                                     │
│   ├─ YouTube    → google-api-python-client (Data API v3)            │
│   ├─ TikTok     → tiktok-uploader (no oficial)                      │
│   └─ (Opcional) Ayrshare / Blotato → API unificada 13+ redes        │
└────────────────────────────────────────────────────────────────────┘
```

---

## Componentes Clave

### 1. Calendario de Contenido (`config/calendar.json`)

Archivo JSON que define cada post a generar y publicar. Estructura:

```json
{
  "posts": [
    {
      "id": "post_001",
      "status": "pending",              // pending|published|failed|partial
      "workflow": "instagram_post",      // nombre del workflow a usar
      "title": "Título del post",
      "prompt": "descripción de la imagen",
      "negative_prompt": "qué evitar",
      "caption": "texto del post con hashtags",
      "platforms": ["instagram", "twitter", "facebook"],
      "checkpoint": "juggernautXL_v9.safetensors",
      "seed": 123456789,
      "width": 1080,
      "height": 1080,
      "batch_size": 1,
      "output_prefix": "post_001",
      "scheduled_at": "2026-07-03T10:00:00",
      "created_at": "2026-07-03T00:00:00Z"
    }
  ]
}
```

**Plantilla**: `config/calendar_template.json` — copia a `calendar.json` y personaliza.

### 2. Orquestador (`scripts/auto_publish.py`)

Script Python que:

1. **Carga el calendario** desde `config/calendar.json`
2. **Filtra posts pendientes** (con `status: "pending"`)
3. **Para cada post**:
   - Carga el workflow API Format JSON correspondiente
   - Sustituye dinámicamente: prompt, seed, dimensiones, checkpoint, batch_size
   - Llama a ComfyUI API: `POST /prompt` para encolar
   - Conecta a WebSocket: `ws://127.0.0.1:8188/ws` para recibir eventos
   - Cuando recibe evento `executing` con `node: null`, el workflow terminó
   - Descarga las imágenes generadas vía `GET /view`
   - Publica a cada plataforma usando la librería correspondiente
   - Actualiza el estado del post en el calendario

**Modos de operación**:
- `python auto_publish.py` — procesa todos los pendientes
- `python auto_publish.py --dry-run` — solo simula
- `python auto_publish.py --once POST_ID` — solo un post
- `python auto_publish.py --platforms instagram` — filtra plataformas
- `python auto_publish.py --schedule` — solo posts cuya fecha ya pasó
- `python auto_publish.py --daemon` — modo continuo (cron)

### 3. Cliente API de ComfyUI (`scripts/comfyui_api_client.py`)

Wrapper Python que encapsula toda la comunicación con ComfyUI:

```python
from comfyui_api_client import ComfyUIClient, load_workflow_api_json, set_workflow_input

client = ComfyUIClient()
workflow = load_workflow_api_json("workflows/instagram_post_api.json")
workflow = set_workflow_input(workflow, "6", "text", "mi prompt aqui")

prompt_id = client.queue_prompt(workflow)
history = client.wait_for_completion(prompt_id, timeout=1800)
images = client.get_output_images(history)

for fname, data in images:
    with open(f"output_{fname}", "wb") as f:
        f.write(data)
```

**API de ComfyUI utilizada**:
| Endpoint | Método | Uso |
|----------|--------|-----|
| `/system_stats` | GET | Health check |
| `/object_info/{folder}` | GET | Listar modelos disponibles |
| `/prompt` | POST | Encolar workflow |
| `/history/{id}` | GET | Estado de ejecución |
| `/queue` | GET | Cola actual |
| `/view` | GET | Descargar imagen generada |
| `/upload/image` | POST | Subir imagen de referencia |
| `/ws` | WebSocket | Eventos en tiempo real |
| `/interrupt` | POST | Cancelar generación |

### 4. Workflows Preconfigurados (`workflows/`)

Cada workflow es un JSON exportable con la estructura de nodos de ComfyUI. **Para uso vía API**, exporta con *Save (API Format)* desde ComfyUI (Settings → Enable Dev Mode → Save (API Format)).

| Workflow | Plataforma | Resolución | Descripción |
|----------|-----------|------------|-------------|
| `instagram_post.json` | Instagram | 1080×1080 | Post cuadrado con Juggernaut XL |
| `instagram_story.json` | Instagram | 1080×1920 | Story/Reel vertical |
| `tiktok_video.json` | TikTok | 1080×1920 | Cover vertical |
| `youtube_thumbnail.json` | YouTube | 1280×720 | Miniatura 16:9 |
| `twitter_post.json` | X/Twitter | 1200×675 | Imagen 16:9 |
| `carousel_5.json` | Instagram | 1080×1080 | Carrusel 5 imágenes |
| `animatediff_video.json` | TikTok/Reels | 512×768×16f | Video animado |
| `logo_brand.json` | General | 1024×1024 | Logo minimalista |
| `cr_aspect_ratio_social.json` | Multi | 4 crops | 1 render → 4 crops IG/Story/X |

### 5. Capa de Publicación

Cada red social tiene su propia función publicadora en `auto_publish.py`:

```python
PUBLISHERS = {
    "instagram": publish_instagram,   # instagrapi
    "twitter":   publish_twitter,     # tweepy
    "facebook":  publish_facebook,    # facebook-sdk
    "pinterest": publish_pinterest,   # py3-pinterest
}
```

Cada función:
- Carga credenciales desde variables de entorno (`.env`)
- Sube la imagen/video
- Publica con el caption
- Devuelve `{"success": bool, "url": str, "error": str}`

---

## Integración con Agentes AI (Hermes, etc.)

El sistema está preparado para integrarse con agentes AI autónomos como **Hermes Agent** (Nous Research) a través de dos caminos:

### Camino A: MCP Server (recomendado)

`comfyui-mcp-server` (custom node incluido) expone ComfyUI como un servidor MCP (Model Context Protocol). Cualquier agente compatible con MCP (Hermes, Claude, Cursor, etc.) puede:

- Listar workflows disponibles
- Ejecutar workflows con parámetros
- Obtener resultados
- Instalar modelos y custom nodes

**Doc oficial de Hermes + ComfyUI**: https://hermes-agent.nousresearch.com/docs/user-guide/skills/bundled/creative/creative-comfyui

### Camino B: API REST directa

El agente llama directamente a `auto_publish.py` o al `comfyui_api_client.py` como herramienta (tool calling). El LLM (ej: Hermes-3) usa function calling para:

```python
# Tool schema que el LLM usaría
{
  "name": "create_social_post",
  "description": "Crea y publica un post en redes sociales",
  "parameters": {
    "prompt": "string",
    "platforms": ["instagram", "twitter"],
    "workflow": "instagram_post",
    "caption": "string"
  }
}
```

### Camino C: n8n / Make.com (no-code)

Para integración visual sin código, usar n8n con el nodo comunitario `n8n-nodes-comfyui`:

```
Trigger (Schedule/Airtable) → HTTP POST /prompt → Wait /ws
  → HTTP GET /view → nodo Ayrshare → Publicar 5 redes
```

**Plantilla n8n**: https://n8n.io/workflows/3066-automate-multi-platform-social-media-content-creation-with-ai

---

## Flujo de Datos Completo

```
[Usuario define post en calendar.json]
                │
                ▼
[auto_publish.py lee calendario]
                │
                ▼
[Carga workflow instagram_post.json]
                │
                ▼
[Sustituye prompt, seed, dimensiones]
                │
                ▼
[POST /prompt a ComfyUI] ────► [ComfyUI ejecuta workflow]
                │                          │
                │                          │ (15-30s en RTX 3060)
                │                          ▼
                │                  [WebSocket: ejecución completada]
                │                          │
                ▼                          ▼
[GET /history/{prompt_id}] ◄──────────────┘
                │
                ▼
[GET /view?filename=...]
                │
                ▼
[Imagen descargada a ComfyUI/output/]
                │
                ├─► [instagrapi → Instagram] → post_id
                ├─► [tweepy → Twitter/X]    → tweet_id
                └─► [facebook-sdk → FB]     → post_id
                │
                ▼
[Actualiza calendar.json: status=published, publish_results={...}]
```

---

## Plan de Implementación por Fases

### Fase 1 — MVP (1 semana) ✅
- ComfyUI local + 8 workflows preconfigurados
- Script `auto_publish.py` con publicación a IG, X, FB
- Calendario JSON simple
- Cliente API de ComfyUI (`comfyui_api_client.py`)

### Fase 2 — Multi-plataforma (2 semanas)
- Añadir Pinterest, YouTube Shorts, TikTok
- Batch generation con `ComfyUI-batching-nodes`
- Auto-captioning con WD14 Tagger + LLM party
- Workflow `cr_aspect_ratio_social` (1 render → 4 crops)

### Fase 3 — Orquestación Avanzada (2 semanas)
- Migrar calendar a **Airtable** (API REST + UI visual)
- Integrar **Hermes Agent** vía MCP server para:
  - Auto-mejora de prompts
  - Decisión de workflow según objetivo
  - Self-improvement sobre resultados
- Programación con **n8n** self-hosted
- Analytics de engagement

### Fase 4 — Producción (1 semana)
- Migrar a **Ayrshare** o **Blotato** (API unificada 13+ redes)
- A/B testing de captions
- Dashboard de métricas
- ComfyDeploy para entorno productivo

---

## Consideraciones de Seguridad

1. **Credenciales**: NUNCA hardcodear tokens. Usar `.env` (ya en `.gitignore`)
2. **APIs privadas**: `instagrapi` y `tiktok-uploader` violan ToS — riesgo de ban. Para producción, migrar a Graph API oficial
3. **Rate limits**: Cada plataforma tiene límites. Ver tabla en `docs/USAGE.md`
4. **Contenido AI**: TikTok y Meta exigen marcar contenido AI generado. Implementar antes de producción
5. **Backup**: Calendar.json y workflows deben versionarse en git
6. **Tokens de larga vida**: Facebook Page Token expira — renovar cada 60 días

---

## Métricas y Monitoreo

El sistema registra logs en `auto_publish.log` con:
- Timestamp de cada post procesado
- Tiempo de generación (ComfyUI)
- Tiempo de publicación por plataforma
- Errores detallados
- Post IDs generados

Para monitoring avanzado, integrar con:
- **Grafana** + Prometheus (métricas técnicas)
- **Ayrshare Analytics API** (engagement unificado)
- **YouTube Analytics API** (engagement YouTube)

---

## Estimaciones de Rendimiento (RTX 3060 12GB)

| Operación | Tiempo estimado |
|-----------|----------------|
| SDXL 1024×1024, 30 steps | 15-25 segundos |
| SD 1.5 512×512, 25 steps | 3-5 segundos |
| AnimateDiff 16 frames SD 1.5 | 2-5 minutos |
| Wan 2.1 video 5s 1.3B | 8-15 minutos |
| Upscale 4x (post-generation) | 5-10 segundos |
| **Post completo (generar + publicar)** | **30-60 segundos** |

Con esto, puedes generar y publicar **~60 posts/hora** en flujo continuo, ideal para campañas de carrusel o batch de contenido semanal.
