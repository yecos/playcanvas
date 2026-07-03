# Solución de Problemas

## Problemas de instalación

### ❌ "Python no está instalado" o "python: command not found"

**Windows:**
1. Instala Python 3.10 o 3.11 desde https://www.python.org/downloads/
2. ⚠️ Marca "Add Python to PATH" durante la instalación
3. Reinicia la terminal/cmd

**Linux:**
```bash
sudo apt install python3.11 python3.11-venv python3-pip
```

### ❌ "git clone fallido" o "fatal: unable to access"

- Verifica tu conexión a internet
- Si estás en una red que bloquea GitHub, usa una VPN
- Intenta con HTTPS en vez de SSH:
  ```bash
  git clone https://github.com/comfyanonymous/ComfyUI.git
  ```

### ❌ "pip install torch fallido"

**Causa común**: Driver NVIDIA muy antiguo o CUDA no disponible.

**Solución 1**: Actualiza el driver NVIDIA
- https://www.nvidia.com/Download/index.aspx
- Reinicia el PC después de instalar

**Solución 2**: Instala PyTorch CPU como fallback:
```bash
venv\Scripts\activate
pip install torch torchvision torchaudio
```
⚠️ ComfyUI funcionará en modo CPU (10-50x más lento)

**Solución 3**: Prueba otra versión de CUDA:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### ❌ "nvidia-smi no se reconoce como comando"

- Driver NVIDIA no instalado o no en PATH
- Descarga el driver desde https://www.nvidia.com/Download/index.aspx

### ❌ "CUDA out of memory" durante la instalación

No debería pasar durante la instalación. Si pasa, es por otra app usando la GPU:
- Cierra Chrome, Discord, juegos, etc.
- Reinicia el PC y reintenta

---

## Problemas de ejecución

### ❌ "CUDA out of memory" al generar imagen

**Síntomas**: Error rojo en ComfyUI: `CUDA out of memory. Tried to allocate X GiB.`

**Soluciones** (de menor a mayor impacto):

1. **Activa `--lowvram`** en `config/launch_args.txt` (añade la línea `--lowvram`)
2. **Reduce la resolución**:
   - SDXL: 1024×1024 → 768×768
   - SD 1.5: 512×512 → 384×384
3. **Usa SD 1.5** en vez de SDXL (mucho menos consumo)
4. **Cierra apps que usan GPU**: Chrome, Discord, Steam, juegos
5. **Activa `--fp16-vae`** y `--use-pytorch-cross-attention` (ya en launch_args)
6. **Desactiva xformers temporalmente** (a veces causa OOM en algunas configs)

### ❌ ComfyUI se abre pero no aparece el botón "Manager"

- El ComfyUI-Manager no se instaló correctamente
- Verifica:
  ```bash
  ls ComfyUI/custom_nodes/ComfyUI-Manager
  ```
- Si no existe, instálalo manualmente:
  ```bash
  cd ComfyUI/custom_nodes
  git clone https://github.com/comfy-org/ComfyUI-Manager.git
  ```
- Reinicia ComfyUI

### ❌ "ModuleNotFoundError: No module named 'torch'"

- El entorno virtual no se activó correctamente
- Ejecuta:
  ```bash
  # Windows
  venv\Scripts\activate
  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

  # Linux/macOS
  source venv/bin/activate
  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
  ```

### ❌ ComfyUI muy lento (5+ minutos por imagen en RTX 3060)

**Esperado en RTX 3060 12GB**:
- SDXL 1024×1024: 15-30 segundos
- SD 1.5 512×512: 3-5 segundos

**Si es más lento de eso**:
1. Verifica que GPU está siendo usada:
   ```bash
   nvidia-smi
   ```
   Mientras generas, deberías ver `python.exe` usando la GPU.

2. Si no aparece, PyTorch no está usando CUDA:
   ```bash
   venv\Scripts\activate
   python -c "import torch; print(torch.cuda.is_available())"
   ```
   Debería imprimir `True`.

3. Si imprime `False`, reinstala PyTorch con CUDA:
   ```bash
   pip uninstall torch torchvision torchaudio
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
   ```

### ❌ Imágenes salen corruptas / ruido / negro total

**Causas**:
1. **Falta VAE**: Conecta el VAE del checkpoint al VAEDecode
2. **VAE incompatible**: SDXL necesita VAE de SDXL, SD 1.5 necesita VAE de SD 1.5
3. **fp16 VAE conflictivo**: Quita `--fp16-vae` de launch_args.txt

### ❌ "Error: no JSON object could be decoded" al cargar workflow

- El workflow está corrupto o incompleto
- Descárgalo de nuevo del repo
- Si lo modificaste, abre un issue

---

## Problemas con modelos

### ❌ "Model not found: juggernautXL_v9.safetensors"

- El modelo no se descargó o está corrupto
- Verifica:
  ```bash
  # Windows
  dir ComfyUI\models\checkpoints\juggernautXL_v9.safetensors

  # Linux/macOS
  ls -lh ComfyUI/models/checkpoints/juggernautXL_v9.safetensors
  ```
- Si no existe o pesa < 6GB, re-descarga:
  ```bash
  python scripts/download_models.py --retry --category checkpoints
  ```

### ❌ Descarga de modelos fallida (CivitAI)

CivitAI requiere autenticación. Configura tu token:

1. Regístrate en https://civitai.com (gratis)
2. Ve a **Account Settings → API Keys → Add API key**
3. Configura la variable de entorno:

**Windows (PowerShell)**:
```powershell
[System.Environment]::SetEnvironmentVariable('CIVITAI_TOKEN', 'tu_token_aqui', 'User')
```

**Linux/macOS**:
```bash
echo 'export CIVITAI_TOKEN="tu_token_aqui"' >> ~/.bashrc
source ~/.bashrc
```

4. Re-ejecuta:
   ```bash
   python scripts/download_models.py --retry
   ```

### ❌ "403 Forbidden" descargando modelos

- Tu IP puede estar bloqueada (CivitAI bloquea algunos rangos)
- Prueba con VPN
- Descarga manualmente desde el navegador y coloca el archivo en la carpeta correcta

---

## Problemas con custom nodes

### ❌ "ImportError: cannot import name X" al arrancar

- Un custom node tiene dependencias rotas
- Identifica cuál:
  ```bash
  # Linux/macOS
  cd ComfyUI
  python main.py 2>&1 | grep -i error
  ```
- Reinstala sus dependencias:
  ```bash
  cd ComfyUI/custom_nodes/ComfyUI-Impact-Pack  # ejemplo
  pip install -r requirements.txt
  ```

### ❌ Custom node no aparece tras instalar

- Reinicia ComfyUI
- Si no aparece, fue error de instalación
- Reinstala:
  ```bash
  rm -rf ComfyUI/custom_nodes/ComfyUI-Impact-Pack  # ejemplo
  python scripts/install_custom_nodes.py --force
  ```

---

## Problemas de video (AnimateDiff)

### ❌ "AnimateDiff module not found"

- Falta el motion module
- Verifica:
  ```bash
  ls ComfyUI/models/animatediff_models/
  ```
- Debe contener `mm_sd_v15_v2.ckpt`
- Si no, descárgalo:
  ```bash
  python scripts/download_models.py --category animatediff_models
  ```

### ❌ Video sale "fantasma" (imágenes superpuestas)

- El motion module es incompatible con el checkpoint
- Usa `dreamshaper_8.safetensors` (SD 1.5), no SDXL
- AnimateDiff v2 solo soporta SD 1.5

### ❌ Generación de video muy lenta

- 16 frames en SD 1.5 con RTX 3060: 2-5 minutos
- Si tarda más, reduce frames (8 en vez de 16)
- Cierra otras apps que usen GPU

---

## Problemas de red

### ❌ No puedo acceder a ComfyUI desde otro dispositivo

Por defecto, ComfyUI solo escucha en localhost. Para acceso en red local:

1. Edita `config/launch_args.txt`
2. Cambia `--listen 127.0.0.1` por `--listen 0.0.0.0`
3. Descomenta `--enable-cors-header`
4. Reinicia ComfyUI
5. Accede desde otro dispositivo usando la IP de tu PC: `http://192.168.1.100:8188`

> ⚠️ Esto expone ComfyUI a toda tu red. No lo uses en redes públicas.

### ❌ "Connection refused" en 127.0.0.1:8188

- ComfyUI no está corriendo
- Verifica que `start.bat`/`start.sh` está activo
- Si se cerró, abre un issue con el error que muestra la terminal

---

## Problemas de rendimiento

### ❌ Disco se está llenando

- Los outputs se acumulan en `ComfyUI/output/`
- Limpia periódicamente:
  ```bash
  # Windows
  del /Q ComfyUI\output\*.png

  # Linux/macOS
  rm ComfyUI/output/*.png
  ```
- También puedes moverlos a otro disco:
  ```bash
  # Linux
  mv ComfyUI/output /mnt/disco_grande/comfyui_output
  ln -s /mnt/disco_grande/comfyui_output ComfyUI/output
  ```

### ❌ Mucha RAM consumida

- Cierra workflows no usados (Ctrl+Shift+R resetea)
- Reduce el batch size en EmptyLatentImage (debería ser 1, salvo AnimateDiff)
- Aumenta la swap/pagefile de Windows

---

## Logs y depuración

### Ver logs de ComfyUI

Los logs se muestran en la terminal donde ejecutaste `start.bat`/`start.sh`.

Para guardarlos:
```bash
# Windows
start.bat > comfyui.log 2>&1

# Linux/macOS
./start.sh 2>&1 | tee comfyui.log
```

### Ver qué GPU está usando PyTorch

```bash
venv\Scripts\activate
python -c "import torch; print('CUDA:', torch.cuda.is_available()); print('Device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
```

### Reportar un issue

Si después de esta guía sigues con problemas:

1. Ejecuta `python scripts/check_system.py` y copia el output
2. Guarda el log de ComfyUI
3. Abre un issue en: https://github.com/yecos/playcanvas/issues
4. Incluye:
   - Output de check_system.py
   - Log de ComfyUI
   - Workflow JSON que causó el problema
   - Screenshot del error
