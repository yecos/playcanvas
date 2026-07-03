# Guía de Temas Visuales — ComfyUI Social Media Suite

Esta guía explica cómo personalizar la apariencia de ComfyUI para que se vea moderno y profesional, alineado con la identidad de tu marca.

---

## 🎨 Tema por defecto del Suite

El instalador aplica automáticamente:

1. **Nuevo frontend** (`ComfyUI_frontend@latest`) — Vue 3 + Svelte, más moderno y rápido
2. **Color palette de marca** (`config/brand_palette.json`) — esquema dark con acentos coral y turquesa
3. **user.css personalizado** (`config/user.css`) — tipografía Inter + JetBrains Mono, bordes redondeados, sombras suaves

Esto se aplica ejecutando:
```bash
python scripts/apply_theme.py
```

Para revertir:
```bash
python scripts/apply_theme.py --revert
```

---

## 🎯 Características del tema incluido

### Paleta de colores
- **Fondo principal**: `#1A1A2E` (azul oscuro casi negro)
- **Fondo secundario**: `#16213E` (azul medianoche)
- **Tarjetas/nodos**: `#2D2D44` (púrpura oscuro)
- **Texto principal**: `#F0E6D2` (crema cálido)
- **Acento**: `#FFB266` (coral suave)
- **Acento hover**: `#FFA931` (naranja)
- **Success**: `#3a784e` (verde)
- **Error**: `#aa534b` (rojo apagado)
- **Info**: `#4a749e` (azul info)

### Tipografía
- **UI**: Inter (sans-serif moderna, legible)
- **Código/prompts**: JetBrains Mono (monoespaciada, excelente para prompts largos)

### Detalles visuales
- Bordes redondeados (8px) en todos los elementos
- Sombras suaves en botones y modales
- Animaciones en hover (translateY -1px)
- Scrollbar moderna con thumb que cambia en hover
- Badge "ComfyUI Social Suite" discreto en esquina inferior derecha
- Backdrop-filter blur en menús superiores

---

## 🛠️ Personalización avanzada

### Cambiar colores de marca

1. Edita `config/brand_palette.json` con tus colores
2. Edita las variables CSS en `config/user.css` (línea 12-25):
   ```css
   :root {
     --suite-accent: #TU_COLOR;
     --suite-bg-primary: #TU_COLOR;
     /* ... */
   }
   ```
3. Re-aplica: `python scripts/apply_theme.py`

### Importar paleta manualmente

Si prefieres hacerlo desde la UI de ComfyUI:

1. Abre ComfyUI en el navegador
2. Settings (engranaje) → Appearance → Color Palette
3. Click **Import**
4. Selecciona `config/brand_palette.json`
5. Click **Save**

### Crear tu propia paleta desde cero

ComfyUI soporta 3 bloques en la paleta JSON:

```json
{
  "colors": {
    "node_slot": {
      "MODEL": "#B39DDB",
      "CLIP": "#FFD500",
      "IMAGE": "#64B5F6",
      "LATENT": "#FF9CF9",
      "VAE": "#FF6E6E",
      "CONDITIONING": "#FFA931",
      "*": "#B5A642"
    },
    "litegraph_base": {
      "BACKGROUND_COLOR": "#1A1A2E",
      "NODE_TITLE_COLOR": "#F0E6D2",
      "NODE_DEFAULT_BGCOLOR": "#1F1F35",
      "NODE_TEXT_COLOR": "#F0E6D2",
      "LINK_COLOR": "#9E9E9E",
      "GRID_COLOR": "#3C3C5C"
    },
    "comfy_base": {
      "bg-color": "#1A1A2E",
      "fg-color": "#F0E6D2",
      "comfy-menu-bg": "#16213E",
      "border-color": "#3C3C5C",
      "primary-bg": "#FFB266",
      "primary-fg": "#1A1A2E"
    }
  }
}
```

---

## 🌈 Temas adicionales (Niutonian)

El installer incluye Niutonian Themes en `custom_nodes_list.json`. Si lo instalas, tendrás 10 temas extra:

| Tema | Estilo | Recomendado para |
|------|--------|------------------|
| **Modern Dark** | Dark minimalista | Uso diario |
| **Glassmorphism** | Glass effect, blur | Presentaciones |
| **Neon Glow** | Neón brillante | Streams / gaming |
| **Minimal Clean** | Limpio, blanco | Work profesional |
| **Ocean Deep** | Azul profundo | Branding fresco |
| **Sunset Warm** | Cálido naranja | Lifestyle brands |
| **Cyberpunk** | Verde neón / magenta | Tech / dev audiences |
| **Forest Night** | Verde oscuro | Eco / naturaleza |
| **Midnight Purple** | Púrpura nocturno | Creative / art |
| **Ember Glow** | Rojo cálido | Food / passion |

### Instalar Niutonian Themes

**Vía ComfyUI Manager (recomendado)**:
1. Abre ComfyUI
2. Click en **Manager**
3. **Install Custom Nodes**
4. Busca "Niutonian Themes"
5. Click **Install** y reinicia

**Vía CLI**:
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/Niutonian/ComfyUI-Niutonian-Themes.git
```

### Activar un tema Niutonian

Después de instalar:
1. Settings → Appearance → Niutonian Themes
2. Selecciona el tema (ej: "Modern Dark")
3. Click **Apply**

Atajos de teclado: `Alt+1` hasta `Alt+0` para cambiar rápido entre temas.

---

## 🆕 Nuevo Frontend vs Legacy

ComfyUI tiene **dos frontends**:

### Nuevo frontend (recomendado)
- Repo: `Comfy-Org/ComfyUI_frontend`
- Tech: Vue 3 + Svelte + TypeScript
- Default desde: **15 noviembre 2024**
- Features:
  - Soporta `user.css` (override de estilos)
  - Nodes 2.0 (diseño moderno de nodos)
  - Sidebar flotante
  - Canvas background configurable
  - Node Opacity slider
  - Mejor performance
  - Soporte para subgraphs

### Legacy frontend (deprecated)
- Solo para compatibilidad con custom nodes antiguos
- No soporta `user.css`
- Activar con: `--front-end-version Comfy-Org/ComfyUI_legacy_frontend@latest`

### Verificar qué frontend usas

```bash
# En la UI:
Settings → About → "Frontend version"

# O en la terminal al arrancar ComfyUI:
# Busca: "Loading frontend: Comfy-Org/ComfyUI_frontend@..."
```

El `launch_args.txt` del Suite ya activa el nuevo frontend:
```
--front-end-version Comfy-Org/ComfyUI_frontend@latest
```

---

## 🎨 Nodes 2.0 (diseño moderno de nodos)

El nuevo frontend soporta **Nodes 2.0**, un rediseño visual de los nodos:

### Activar Nodes 2.0
1. Settings → Beta/Experimental → **Modern Node Design**
2. Toggle ON
3. Refresh (Ctrl+R)

### Características
- Bordes más suaves
- Mejor jerarquía visual
- Slots más grandes y clicables
- Animaciones de conexión
- Color coding por tipo de nodo (loader, sampler, save, etc.)

---

## 📸 Otros custom nodes visuales útiles

### ComfyUI-Custom-Scripts (pysssss)
Incluido en la instalación. Features visuales:
- **Image Feed**: galería de outputs en panel lateral
- **Custom Colors**: color picker por nodo con eyedropper
- **Favicon Status**: el favicon del browser muestra estado de la cola
- **Auto Organization**: organiza nodos automáticamente

Activar: Settings → pysssss

### rgthree-comfy
Incluido. Features:
- **Power Prompt**: prompt box más grande y cómodo
- **Context**: nodo que pasa todos los datos (model, clip, vae, etc.)
- **Reroute**: reroutes limpios para conexiones
- **Seed**: control de seed más visual
- **Mute/Bypass Switches**: switches para activar/desactivar nodos

### ComfyUI-Custom-Node-Color
No incluido pero recomendable si quieres control total sobre colores:
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/lovelybbq/ComfyUI-Custom-Node-Color.git
```
Permite color picker GUI + eyedropper para cualquier nodo.

---

## 🖼️ Background del canvas

Puedes personalizar el fondo del canvas (donde se dibujan los nodos):

1. Edita `config/brand_palette.json`
2. En `litegraph_base.BACKGROUND_IMAGE`, pon un base64 de tu imagen
3. O en `litegraph_base.CLEAR_COLOR`, pon un color sólido
4. Re-aplica: `python scripts/apply_theme.py`

Para un fondo sutil con tu logo (recomendado):
- Usa una imagen PNG transparente de 256×256
- Opacidad baja (10-15%)
- Repetición en mosaico

---

## 🔧 Troubleshooting visual

### "El tema no se aplica"
- Fuerza refresh: `Ctrl+Shift+R` (Windows) o `Cmd+Shift+R` (Mac)
- Verifica que `ComfyUI/user/default/user.css` existe
- Verifica que `ComfyUI/user/default/comfy.settings.json` tiene `Comfy.ColorPalette`

### "Las fuentes no cargan"
- Necesitas conexión a internet (Google Fonts)
- Sin internet, cae a fallback: `-apple-system, BlinkMacSystemFont, 'Segoe UI'`

### "Se ve mal en monitores pequeños"
- El tema está optimizado para 1920×1080 o superior
- En laptops pequeños, reduce zoom: `Ctrl + -`

### "Custom node no respeta el tema"
- Algunos custom nodes tienen su propio CSS hardcoded
- Solución: añade `!important` en `user.css` para esa clase específica
- Ejemplo:
  ```css
  .my-custom-node-class {
    background: var(--suite-bg-card) !important;
  }
  ```

### "Quiero volver al tema default de ComfyUI"
```bash
python scripts/apply_theme.py --revert
```

---

## 📋 Checklist de personalización completa

Para tener un ComfyUI 100% personalizado:

- [ ] Ejecutar `python scripts/apply_theme.py`
- [ ] Activar Nodes 2.0 (Settings → Experimental → Modern Node Design)
- [ ] Instalar Niutonian Themes (vía Manager)
- [ ] Probar tema "Modern Dark" o "Minimal Clean"
- [ ] Editar `config/brand_kit.yaml` con tu marca
- [ ] Editar `config/user.css` con tus colores exactos
- [ ] Re-aplicar tema: `python scripts/apply_theme.py`
- [ ] Activar Image Feed (Settings → pysssss → Image Feed)
- [ ] Reiniciar ComfyUI y verificar

---

## 🔗 Recursos adicionales

- **Galería de temas**: https://comfyui-themes.com
- **Niutonian Themes**: https://github.com/Niutonian/ComfyUI-Niutonian-Themes
- **Catppuccin**: https://github.com/typedrat/catppuccin-comfyui
- **shahshrey themes**: https://github.com/shahshrey/ComfyUI-themes
- **Docs oficiales frontend**: https://docs.comfy.org/guides/frontend
- **Custom node color**: https://github.com/lovelybbq/ComfyUI-Custom-Node-Color

---

## 💡 Recomendación final

Para el **ComfyUI Social Media Suite**, la configuración óptima es:

1. ✅ Nuevo frontend (ya activado en `launch_args.txt`)
2. ✅ Nodes 2.0 (activar manualmente)
3. ✅ Color palette de marca (ya aplicada por `apply_theme.py`)
4. ✅ user.css con tipografía Inter (ya aplicado)
5. ✅ Image Feed activado (Settings → pysssss)
6. ✅ Niutonian "Modern Dark" como base (opcional, encima del nuestro)
7. ✅ Brand kit con tu logo y handle (`config/brand_kit.yaml`)

Con esto tendrás un ComfyUI que:
- Se ve profesional y moderno
- Refleja tu identidad de marca
- Es cómodo para sesiones largas de creación
- Impresiona a clientes/equipo cuando lo muestras
