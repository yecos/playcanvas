# Workflows Incluidos

Esta carpeta contiene workflows preconfigurados para redes sociales, optimizados para RTX 3060 12GB.

## Lista de workflows

| Archivo | Plataforma | Resolución | Descripción |
|---------|-----------|------------|-------------|
| `instagram_post.json` | Instagram | 1080×1080 | Post cuadrado con Juggernaut XL |
| `instagram_story.json` | Instagram | 1080×1920 | Story/Reel vertical |
| `tiktok_video.json` | TikTok | 1080×1920 | Cover vertical |
| `youtube_thumbnail.json` | YouTube | 1280×720 | Miniatura 16:9 |
| `twitter_post.json` | X/Twitter | 1200×675 | Imagen 16:9 |
| `carousel_5.json` | Instagram | 1080×1080 | Carrusel 5 imágenes |
| `animatediff_video.json` | TikTok/Reels | 512×768×16f | Video animado |
| `logo_brand.json` | General | 1024×1024 | Logo minimalista |

## Cómo usar un workflow

1. **Abre ComfyUI** (start.bat / start.sh)
2. **Arrastra el archivo JSON** desde esta carpeta a la ventana de ComfyUI
3. **Personaliza**:
   - Edita el prompt en el nodo **CLIPTextEncode (Positive)**
   - Cambia el seed en **KSampler** para variaciones
4. **Genera** con Ctrl+Enter o el botón **Queue Prompt**

## Personalización rápida

### Cambiar resolución
- Encuentra el nodo **EmptyLatentImage**
- Cambia `width` y `height`

### Cambiar modelo
- Encuentra el nodo **CheckpointLoaderSimple**
- Cambia el widget desplegable

### Cambiar prompt
- Encuentra el nodo **CLIPTextEncode** (el de arriba es el positivo)
- Edita el widget de texto

## Workflows avanzados (crearlos tú mismo)

### Workflow con LoRA
Añade entre el CheckpointLoader y KSampler:
```
CheckpointLoader → LoraLoader → KSampler
```

### Workflow con ControlNet
```
LoadImage → ControlNetPreprocessor → ControlNetApply → KSampler
CheckpointLoader → ControlNetLoader ↗
```

### Workflow con Upscaler
```
VAEDecode → UpscaleImage → ImageScale → VAEEncode → KSampler(denoise=0.3) → VAEDecode → SaveImage
```

## Compartir tus workflows

Cuando crees un workflow que te guste:
1. En ComfyUI, click en el botón **Save** (disco)
2. Guárdalo en esta carpeta
3. Si quieres compartirlo, súbelo al repo en un PR
