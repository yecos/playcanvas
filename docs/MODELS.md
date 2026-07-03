# Catálogo de Modelos

## Resumen

Total de modelos incluidos en la instalación: **~25GB**

| Categoría | Cantidad | Tamaño aprox. |
|-----------|----------|---------------|
| Checkpoints | 3 | 15 GB |
| LoRAs | 1 | 50 MB |
| VAEs | 2 | 600 MB |
| ControlNet | 3 | 4.2 GB |
| AnimateDiff | 1 | 1.6 GB |
| Upscalers | 1 | 70 MB |
| Embeddings | 2 | 40 MB |

---

## Checkpoints

### `sd_xl_base_1.0.safetensors` (6.5GB) ⭐ REQUERIDO
- **Fuente**: https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0
- **Uso**: Modelo base SDXL. Excelente para posts de Instagram, miniaturas YouTube, etc.
- **Resolución óptima**: 1024×1024 (o múltiplos)
- **VRAM**: 12GB+ para uso normal

### `juggernautXL_v9.safetensors` (6.5GB) ⭐ REQUERIDO
- **Fuente**: https://civitai.com/models/133005/juggernaut-xl
- **Uso**: Variante de SDXL optimizada para **fotografía realista y retratos**
- **Resolución óptima**: 1024×1024 (o múltiplos)
- **VRAM**: 12GB+
- **Requiere token CivitAI**: Sí (gratuito, regístrate en civitai.com)

### `dreamshaper_8.safetensors` (2GB) ⭐ REQUERIDO
- **Fuente**: https://huggingface.co/Lykon/DreamShaper
- **Uso**: Modelo SD 1.5 rápido y versátil. Ideal para:
  - Previews rápidos
  - Videos con AnimateDiff (SD 1.5 es lo que soporta)
  - Cuando tienes poca VRAM
- **Resolución óptima**: 512×512 o 512×768
- **VRAM**: 6GB+

---

## VAEs

### `sdxl_vae.safetensors` (335MB) ⭐ REQUERIDO
- **Fuente**: https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0
- **Uso**: VAE oficial de SDXL. Mejora los colores y el contraste.
- **Cuándo usarlo**: Siempre con checkpoints SDXL.

### `vae-ft-mse-840000-ema-pruned.safetensors` (335MB)
- **Fuente**: https://huggingface.co/stabilityai/sd-vae-ft-mse-original
- **Uso**: VAE fine-tuned para SD 1.5. Mejora rostros y detalles finos.
- **Cuándo usarlo**: Con checkpoints SD 1.5.

---

## LoRAs

### `detail_tweaker_xl.safetensors` (50MB)
- **Fuente**: https://huggingface.co/sterloDetailTweakerXL
- **Uso**: Ajusta el nivel de detalle en imágenes SDXL
- **Strenght recomendado**: 0.5 a 0.8 (positivo para más detalle, negativo para simplificar)

---

## ControlNet

> ⚠️ Estos ControlNets son para **SD 1.5**, no SDXL.

### `control_v11f1p_sd15_depth.pth` (1.4GB)
- **Uso**: Controla la composición con un mapa de profundidad
- **Ideal para**: Re-interpretar fotos manteniendo la estructura 3D

### `control_v11p_sd15_canny.pth` (1.4GB)
- **Uso**: Controla con bordes detectados (Canny)
- **Ideal para**: Mantener contornos precisos (logos, composiciones geométricas)

### `control_v11f1p_sd15_openpose.pth` (1.4GB)
- **Uso**: Controla la pose humana (cuerpo, manos, cara)
- **Ideal para**: Generar personas en poses específicas

---

## AnimateDiff

### `mm_sd_v15_v2.ckpt` (1.6GB)
- **Fuente**: https://huggingface.co/guoyww/AnimateDiff
- **Uso**: Motion module para animar imágenes SD 1.5
- **Limitación**: Solo funciona con modelos SD 1.5 (no SDXL)
- **Cuántos frames**: 16 frames = ~2 segundos a 8fps

---

## Upscalers

### `4x-UltraSharp.pth` (67MB)
- **Fuente**: https://huggingface.co/lokCX/4x-Ultrasharp
- **Uso**: Upscaling 4x con nitidez. Lleva un 1024×1024 a 4096×4096.
- **Mejor uso**: Posts de Instagram donde quieres máxima nitidez

---

## Embeddings (Textual Inversions)

### `bad_prompt_version2.pt` (24MB)
- **Uso**: Negative prompt automático para SD 1.5
- **Cómo usar**: Añadir `<bad_prompt_version2>` al prompt negativo

### `EasyNegative.safetensors` (24MB)
- **Uso**: Negative prompt para SD 1.5
- **Cómo usar**: Añadir `<EasyNegative>` al prompt negativo

---

## Cómo añadir más modelos

### Checkpoints
1. Descarga archivos `.safetensors` desde:
   - **CivitAI**: https://civitai.com (requiere cuenta)
   - **HuggingFace**: https://huggingface.co
2. Colócalos en `ComfyUI/models/checkpoints/`
3. Recarga ComfyUI (F5)

### LoRAs
1. Descarga desde CivitAI (muchos gratis)
2. Colócalos en `ComfyUI/models/loras/`
3. Recarga ComfyUI

### Modelos SDXL vs SD 1.5 — cuándo usar cada uno

| Característica | SDXL | SD 1.5 |
|----------------|------|--------|
| Calidad | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| VRAM requerida | 12GB+ | 6GB+ |
| Velocidad | Lento | Rápido |
| Resolución nativa | 1024×1024 | 512×512 |
| LoRAs disponibles | En crecimiento | Miles |
| AnimateDiff soportado | Parcial | ✅ Sí |
| Mejor para | Posts, thumbnails | Videos, previews rápidos |

---

## Configurar token de CivitAI (opcional, para descargar modelos de CivitAI)

1. Regístrate en https://civitai.com
2. Ve a **Account Settings → API Keys**
3. Crea una API key
4. Configúrala como variable de entorno:

**Windows:**
```bat
setx CIVITAI_TOKEN "tu_token_aqui"
```

**Linux/macOS:**
```bash
echo 'export CIVITAI_TOKEN="tu_token_aqui"' >> ~/.bashrc
source ~/.bashrc
```

5. Re-ejecuta `python scripts/download_models.py --retry`

---

## Verificar modelos instalados

```bash
# Windows
dir ComfyUI\models\checkpoints\

# Linux/macOS
ls -lh ComfyUI/models/checkpoints/
```

O lista solo lo que falta:
```bash
python scripts/download_models.py --list
```
