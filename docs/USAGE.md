# Guía de Uso

## Iniciar ComfyUI

### Windows
- Doble clic en `start.bat`

### Linux / macOS
```bash
./start.sh
```

Se abrirá automáticamente tu navegador en `http://127.0.0.1:8188`.

> Si no se abre automáticamente, abre manualmente esa URL.

---

## Cargar un workflow preconfigurado

1. Abre ComfyUI en el navegador
2. Arrastra el archivo JSON desde la carpeta `workflows/` hacia la ventana de ComfyUI
3. El workflow se cargará con todos los nodos y conexiones

Alternativamente:
1. Click en el botón **Load** (carpeta) en el menú inferior
2. Navega a `ComfyUI/user/default/workflows/`
3. Selecciona el workflow que quieras usar

---

## Workflows disponibles

| Archivo | Plataforma | Resolución | Uso |
|---------|-----------|------------|-----|
| `instagram_post.json` | Instagram | 1080×1080 | Post cuadrado |
| `instagram_story.json` | Instagram | 1080×1920 | Story / Reel cover |
| `tiktok_video.json` | TikTok | 1080×1920 | Cover / preview |
| `youtube_thumbnail.json` | YouTube | 1280×720 | Miniatura de video |
| `twitter_post.json` | X/Twitter | 1200×675 | Imagen de post |
| `carousel_5.json` | Instagram | 1080×1080 | Carrusel (5 imágenes) |
| `animatediff_video.json` | TikTok/Reels | 512×768×16f | Video animado corto |
| `logo_brand.json` | General | 1024×1024 | Logo de marca |

---

## Personalizar un workflow

### Cambiar el prompt
1. Localiza el nodo **CLIP Text Encode (Positive)**
2. Edita el texto con tu descripción
3. Pulsa **Queue Prompt** (o Ctrl+Enter)

### Cambiar resolución
1. Localiza el nodo **Empty Latent Image**
2. Cambia `width` y `height`
3. Resoluciones comunes:
   - Instagram post: 1080×1080
   - Story/Reel: 1080×1920
   - Twitter: 1200×675
   - YouTube: 1280×720

### Cambiar seed (variaciones)
1. En el nodo **KSampler**, cambia el campo `seed`
2. O selecciona `randomize` para que cambie en cada generación

### Cambiar el modelo
1. En el nodo **Checkpoint Loader**, despliega el menú
2. Selecciona otro modelo (debes haberlo descargado antes)

---

## Usar LoRAs

Los LoRAs son "ajustes finos" para personalizar el estilo o añadir personajes.

1. Coloca el archivo `.safetensors` en `ComfyUI/models/loras/`
2. En ComfyUI, añade un nodo **LoraLoader** (Click derecho → loaders → LoraLoader)
3. Conéctalo entre el CheckpointLoader y el KSampler:
   - `MODEL` del checkpoint → `model` del LoraLoader
   - `CLIP` del checkpoint → `clip` del LoraLoader
   - `MODEL` del LoraLoader → `model` del KSampler
   - `CLIP` del LoraLoader → `clip` del CLIPTextEncode
4. Ajusta `strength_model` y `strength_clip` (típicamente 0.6-0.9)

---

## Usar ControlNet

ControlNet permite guiar la generación con imágenes de referencia.

1. Añade un nodo **ControlNetLoader**
2. Selecciona un modelo de ControlNet (ej: `control_v11f1p_sd15_depth.pth`)
3. Añade un nodo de preprocesador:
   - **DepthPreprocessor** para mapas de profundidad
   - **CannyEdgePreprocessor** para bordes
   - **OpenPosePreprocessor** para poses humanas
4. Conecta la imagen de referencia al preprocesador
5. Conecta la salida del preprocesador + el ControlNet al nodo **ControlNetApply**
6. Conecta el resultado al `positive` del KSampler

> Los preprocesadores están en el custom node `comfyui_controlnet_aux` (incluido en la instalación).

---

## Generar videos con AnimateDiff

1. Carga el workflow `animatediff_video.json`
2. Añade un nodo **AnimateDiffLoader** (del paquete ComfyUI-AnimateDiff-Evolved)
3. Selecciona `mm_sd_v15_v2.ckpt` como motion module
4. Conéctalo al modelo antes del KSampler
5. En el nodo **EmptyLatentImage**, ajusta `batch_size` (número de frames):
   - 8 frames ≈ 1 segundo a 8fps
   - 16 frames ≈ 2 segundos
   - 24 frames ≈ 3 segundos
6. Queue Prompt y espera

### Exportar a MP4

Opción A: Dentro de ComfyUI
- Instala `ComfyUI-VideoHelperSuite`
- Añade un nodo **VHS_VideoCombine** después del VAEDecode
- Configura formato MP4 y fps

Opción B: Fuera de ComfyUI
```bash
# Las imágenes se guardan en ComfyUI/output/
ffmpeg -framerate 8 -pattern_type glob -i 'ComfyUI/output/*.png' -c:v libx264 -pix_fmt yuv420p video.mp4
```

---

## Mejorar calidad con Upscaler

Para imágenes finales de alta resolución:

1. Después del VAEDecode, añade:
   - **UpscaleModelLoader** → carga `4x-UltraSharp.pth`
   - **ImageUpscaleWithModel** → conecta la imagen y el modelo
   - **ImageScale** → reduce a tamaño deseado (ej: 2160×2160)
   - **VAEEncode** → vuelve a latent
   - **KSampler** (denoise=0.25) → refina
   - **VAEDecode** → imagen final
   - **SaveImage**

Workflow simplificado:
```
VAEDecode → ImageUpscaleWithModel → ImageScale → VAEEncode → KSampler(denoise=0.25) → VAEDecode → SaveImage
```

---

## API REST de ComfyUI (automatización)

ComfyUI expone una API REST que puedes usar para automatizar la generación desde scripts externos.

### Generar una imagen vía API

```python
import json
import requests
import websocket
import uuid

# Cargar workflow
with open('workflows/instagram_post.json') as f:
    workflow = json.load(f)

# Conectar
client_id = str(uuid.uuid4())
ws = websocket.WebSocket()
ws.connect(f"ws://127.0.0.1:8188/ws?clientId={client_id}")

# Enviar prompt
payload = {
    "prompt": workflow,
    "client_id": client_id
}
response = requests.post('http://127.0.0.1:8188/prompt', json=payload)
prompt_id = response.json()['prompt_id']

# Esperar resultado
while True:
    msg = json.loads(ws.recv())
    if msg['type'] == 'executed' and msg['data']['node'] == '7':
        image_filename = msg['data']['output']['images'][0]['filename']
        print(f"Imagen lista: {image_filename}")
        break

# Descargar imagen
url = f"http://127.0.0.1:8188/view?filename={image_filename}"
img = requests.get(url)
with open('post.jpg', 'wb') as f:
    f.write(img.content)
```

---

## Atajos de teclado útiles

| Atajo | Acción |
|-------|--------|
| `Ctrl+Enter` | Queue Prompt (generar) |
| `Ctrl+Shift+Enter` | Queue Prompt (front of queue) |
| `Ctrl+Z` | Deshacer |
| `Ctrl+Y` | Rehacer |
| `Ctrl+D` | Duplicar nodo seleccionado |
| `Ctrl+Backspace` | Eliminar nodo seleccionado |
| `Ctrl+G` | Agrupar nodos seleccionados |
| `Ctrl+M` | Mute/Bypass nodo seleccionado |
| `B` | Bypass nodo seleccionado |
| `Space` (mantener) | Mover canvas |
| `Shift+drag` | Mover múltiples nodos |
| `Right click` | Menú de nodos |

---

## Organizar los outputs

Por defecto, las imágenes se guardan en `ComfyUI/output/` con timestamp. Para organizarlas mejor:

1. En el nodo **SaveImage**, cambia el prefijo del nombre:
   - `instagram_post` → `ComfyUI/output/instagram_post_001.png`
   - `youtube_thumb` → `ComfyUI/output/youtube_thumb_001.png`
2. Ejecuta este script para organizarlas por fecha:

```bash
# En Linux/macOS
cd ComfyUI/output
find . -type f -name "*.png" -exec bash -c '
  date=$(stat -c %y "$1" | cut -d" " -f1)
  mkdir -p "$date"
  mv "$1" "$date/"
' _ {} \;
```
