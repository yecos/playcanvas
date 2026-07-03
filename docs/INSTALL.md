# Guía de Instalación

## Requisitos previos

Antes de ejecutar el instalador, asegúrate de tener:

### Windows
1. **Python 3.10 o 3.11** desde https://www.python.org/downloads/
   - ⚠️ Marca la casilla "Add Python to PATH" al instalar
2. **Git** desde https://git-scm.com/download/win
3. **Driver NVIDIA actualizado** (versión 525+) desde https://www.nvidia.com/Download/index.aspx
4. **Visual C++ Redistributable** (x64) desde https://aka.ms/vs/17/release/vc_redist.x64.exe

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip git
```

### Linux (Fedora)
```bash
sudo dnf install -y python3.11 python3-pip git
```

### macOS
```bash
brew install python@3.11 git
```

> ⚠️ macOS no soporta CUDA, así que ComfyUI funcionará en modo CPU (muy lento).

---

## Proceso de instalación

### Opción 1: Windows (recomendada)

1. Descarga el repositorio como ZIP desde GitHub, o clónalo:
   ```bat
   git clone https://github.com/yecos/playcanvas.git comfyui-social
   cd comfyui-social
   ```

2. Haz **doble clic en `install.bat`**

3. Sigue las instrucciones en pantalla. El instalador:
   - Verifica tu sistema (GPU, Python, Git, CUDA)
   - Clona ComfyUI oficial
   - Crea un entorno virtual Python aislado
   - Instala PyTorch con soporte CUDA 12.1
   - Instala ComfyUI-Manager
   - Instala 10 custom nodes esenciales
   - Descarga ~20GB de modelos
   - Copia workflows preconfigurados

4. Cuando termine, haz **doble clic en `start.bat`**

5. Se abrirá tu navegador en `http://127.0.0.1:8188`

### Opción 2: Linux / macOS

```bash
git clone https://github.com/yecos/playcanvas.git comfyui-social
cd comfyui-social
chmod +x install.sh
./install.sh
```

Para iniciar:
```bash
./start.sh
```

---

## Tiempo estimado

| Etapa | Tiempo |
|-------|--------|
| Verificación del sistema | 1 min |
| Clonado de ComfyUI | 1-3 min |
| Creación del venv | 1 min |
| Instalación de PyTorch | 5-15 min |
| Instalación de ComfyUI-Manager + custom nodes | 5-10 min |
| Descarga de modelos (~20GB) | 15-60 min |
| Copia de workflows | < 1 min |
| **Total** | **30-90 min** |

Depende principalmente de tu conexión a internet.

---

## Verificación post-instalación

Después de la instalación, deberías tener esta estructura:

```
comfyui-social/
├── ComfyUI/                    # <- Creado por el instalador
│   ├── main.py
│   ├── models/
│   │   ├── checkpoints/        # sd_xl_base_1.0.safetensors, juggernautXL_v9.safetensors, dreamshaper_8.safetensors
│   │   ├── vae/                # sdxl_vae.safetensors
│   │   ├── loras/
│   │   ├── controlnet/         # (opcional)
│   │   ├── animatediff_models/ # mm_sd_v15_v2.ckpt (opcional)
│   │   ├── upscale_models/     # 4x-UltraSharp.pth (opcional)
│   │   └── embeddings/
│   ├── custom_nodes/
│   │   ├── ComfyUI-Manager/
│   │   ├── ComfyUI-Impact-Pack/
│   │   ├── ComfyUI_essentials/
│   │   └── ...
│   └── user/default/workflows/  # <- workflows copiados
├── venv/                       # <- entorno virtual Python
├── install.bat / install.sh
├── start.bat / start.sh
├── ...
```

Para verificar que todo está OK:

```bash
# Windows
venv\Scripts\python.exe scripts\check_system.py

# Linux/macOS
./venv/bin/python scripts/check_system.py
```

---

## Si la instalación falla

### Error: "Python no está instalado"
- Instala Python 3.10/3.11 desde https://www.python.org/downloads/
- Marca "Add Python to PATH"

### Error: "git clone fallido"
- Verifica tu conexión a internet
- Si GitHub está bloqueado, usa una VPN
- Intenta clonar manualmente: `git clone https://github.com/comfyanonymous/ComfyUI.git`

### Error: "pip install torch fallido"
- Verifica que tienes el driver NVIDIA actualizado
- Intenta instalar PyTorch CPU-only como fallback:
  ```bash
  pip install torch torchvision torchaudio
  ```

### Error: "CUDA out of memory" al generar
- Edita `config/launch_args.txt` y añade `--lowvram`
- Reduce la resolución a 768×768

### Error: descarga de modelos interrumpida
- Reanuda con: `python scripts/download_models.py --retry`
- O descarga solo los esenciales: `python scripts/download_models.py --required`

Más ayuda en `TROUBLESHOOTING.md`.
