#!/usr/bin/env bash
# ============================================================
#  ComfyUI Social Media Suite - Instalador Linux/macOS
#  Optimizado para NVIDIA RTX 3060 12GB
# ============================================================
set -e

cd "$(dirname "$0")"

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo " ============================================================"
echo "  COMFYUI SOCIAL MEDIA SUITE - INSTALADOR PARA LINUX/MAC"
echo "  Optimizado para NVIDIA RTX 3060 12GB"
echo " ============================================================"
echo ""
echo "  Este instalador configurara todo lo necesario para usar"
echo "  ComfyUI como herramienta profesional de creacion de"
echo "  contenido para redes sociales."
echo ""
echo "  Proceso:"
echo "    1. Verificacion del sistema"
echo "    2. Clonado de ComfyUI"
echo "    3. Entorno virtual Python"
echo "    4. Instalacion de PyTorch + CUDA"
echo "    5. ComfyUI-Manager"
echo "    6. Custom nodes esenciales"
echo "    7. Descarga de modelos (~20GB)"
echo "    8. Workflows preconfigurados"
echo ""
echo "  Tiempo estimado: 30-90 minutos segun conexion."
echo ""
# Modo automatico: si se pasa --yes, no preguntar
AUTO_CONFIRM=false
if [[ "$1" == "--yes" ]]; then
    AUTO_CONFIRM=true
fi
if [[ "$AUTO_CONFIRM" != "true" ]]; then
    read -p "Presiona ENTER para continuar o Ctrl+C para cancelar..."
fi

# ---- 0. Verificar Python ----
echo ""
echo "  [0/8] Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: Python 3 no esta instalado.${NC}"
    echo "  Instalalo con:"
    echo "    Ubuntu/Debian: sudo apt install python3 python3-venv python3-pip"
    echo "    Fedora:        sudo dnf install python3 python3-pip"
    echo "    macOS:         brew install python@3.11"
    exit 1
fi
PYVER=$(python3 --version 2>&1)
echo -e "  ${GREEN}OK:${NC} $PYVER detectado."

# ---- Verificar Git ----
echo "  Verificando Git..."
if ! command -v git &> /dev/null; then
    echo -e "${RED}ERROR: Git no esta instalado.${NC}"
    echo "  Instalalo con: sudo apt install git  (o equivalente)"
    exit 1
fi
echo -e "  ${GREEN}OK:${NC} Git detectado."

# ---- Verificar NVIDIA ----
echo "  Verificando GPU NVIDIA..."
if ! command -v nvidia-smi &> /dev/null; then
    echo -e "${YELLOW}ADVERTENCIA:${NC} No se detecto GPU NVIDIA."
    echo "  ComfyUI funcionara en modo CPU (MUY lento)."
    read -p "  Continuar de todos modos? (s/N): " CONFIRM
    if [[ ! "$CONFIRM" =~ ^[sS]$ ]]; then exit 1; fi
else
    echo -e "  ${GREEN}OK:${NC} GPU NVIDIA detectada."
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
fi

# ---- 1. Check System ----
echo ""
echo "  [1/8] Verificacion detallada del sistema..."
python3 scripts/check_system.py || {
    echo -e "${RED}ERROR: Verificacion del sistema fallida.${NC}"
    exit 1
}

# ---- 2. Clonar ComfyUI ----
echo ""
echo "  [2/8] Clonando ComfyUI..."
if [ -d "ComfyUI" ]; then
    echo "  La carpeta ComfyUI ya existe. Omitiendo clonado."
else
    git clone https://github.com/comfyanonymous/ComfyUI.git
fi
echo -e "  ${GREEN}OK:${NC} ComfyUI listo."

# ---- 3. Entorno virtual ----
echo ""
echo "  [3/8] Creando entorno virtual Python..."
if [ -d "venv" ]; then
    echo "  Entorno virtual ya existe. Omitiendo."
else
    python3 -m venv venv
fi
source venv/bin/activate
python -m pip install --upgrade pip wheel setuptools
echo -e "  ${GREEN}OK:${NC} Entorno virtual activado."

# ---- 4. PyTorch + CUDA ----
echo ""
echo "  [4/8] Instalando PyTorch con soporte CUDA 12.1..."
echo "  Esto puede tardar varios minutos..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 || {
    echo -e "${YELLOW}ADVERTENCIA:${NC} Fallo CUDA, intentando version CPU..."
    pip install torch torchvision torchaudio
}

# Verificar CUDA
echo "  Verificando CUDA..."
python -c "import torch; assert torch.cuda.is_available(), 'CUDA NO disponible. Reinstala driver NVIDIA.'; print(f'CUDA OK: {torch.cuda.get_device_name(0)}')" || {
    echo -e "${YELLOW}ADVERTENCIA:${NC} CUDA no disponible. ComfyUI funcionara en modo CPU (muy lento)."
    echo "  Solucion: actualiza driver NVIDIA desde https://www.nvidia.com/Download/index.aspx"
    echo "  Continuando de todos modos en modo CPU..."
}
echo -e "  ${GREEN}OK:${NC} PyTorch instalado."

# ---- ComfyUI requirements ----
echo ""
echo "  Instalando dependencias de ComfyUI..."
pip install -r ComfyUI/requirements.txt
pip install -r requirements.txt
echo -e "  ${GREEN}OK:${NC} Dependencias base instaladas."

# ---- Dependencias del orquestador de publicacion ----
echo ""
echo "  Instalando dependencias del orquestador (auto_publish)..."
pip install -r requirements_extended.txt || {
    echo -e "${YELLOW}ADVERTENCIA:${NC} Algunas dependencias extendidas fallaron."
    echo "  El orquestador auto_publish.py puede no funcionar completo."
    echo "  Puedes instalarlas mas tarde: pip install -r requirements_extended.txt"
}
echo -e "  ${GREEN}OK:${NC} Dependencias del orquestador instaladas."

# ---- 5. ComfyUI-Manager ----
echo ""
echo "  [5/8] Instalando ComfyUI-Manager..."
if [ -d "ComfyUI/custom_nodes/ComfyUI-Manager" ]; then
    echo "  ComfyUI-Manager ya existe. Omitiendo."
else
    git clone https://github.com/comfy-org/ComfyUI-Manager.git ComfyUI/custom_nodes/ComfyUI-Manager
fi
echo -e "  ${GREEN}OK:${NC} ComfyUI-Manager listo."

# ---- 6. Custom nodes ----
echo ""
echo "  [6/8] Instalando custom nodes esenciales..."
python scripts/install_custom_nodes.py
echo -e "  ${GREEN}OK:${NC} Custom nodes instalados."

# ---- 7. Descarga de modelos ----
echo ""
echo "  [7/8] Descargando modelos (~20GB)..."
echo "  Este paso es el mas largo. Se mostrara progreso."
echo "  Si falla, puedes reanudar ejecutando:"
echo "    python scripts/download_models.py --retry"
echo ""
# CivitAI token: si esta en entorno, usarlo; si no, mostrar nota y continuar
if [[ -n "$CIVITAI_TOKEN" ]]; then
    echo -e "  ${GREEN}CIVITAI_TOKEN detectado en entorno.${NC}"
else
    echo -e "  ${YELLOW}NOTA:${NC} Juggernaut XL requiere token CivitAI (gratis)."
    echo "  Si falla la descarga, registrate en https://civitai.com,"
    echo "  crea API key y ejecuta:"
    echo "    export CIVITAI_TOKEN=tu_token && python scripts/download_models.py --retry"
fi
# Descarga automatica (sin prompt)
python scripts/download_models.py || echo -e "${YELLOW}Algunos modelos pudieron fallar. Reejecuta con --retry${NC}"

# Copiar extra_model_paths.yaml a ComfyUI
if [ -f "config/extra_model_paths.yaml" ] && [ ! -f "ComfyUI/extra_model_paths.yaml" ]; then
    cp config/extra_model_paths.yaml ComfyUI/extra_model_paths.yaml
    echo -e "  ${GREEN}OK:${NC} extra_model_paths.yaml copiado a ComfyUI"
fi

# ---- 8. Workflows ----
echo ""
echo "  [8/8] Copiando workflows preconfigurados..."
mkdir -p ComfyUI/user/default/workflows
cp -f workflows/*.json ComfyUI/user/default/workflows/ 2>/dev/null || true
echo -e "  ${GREEN}OK:${NC} Workflows copiados a ComfyUI/user/default/workflows/"

# Convertir workflows a API Format (necesario para auto_publish)
echo ""
echo "  Convirtiendo workflows a API Format (necesario para auto_publish)..."
python scripts/convert_workflow_format.py --all || echo -e "${YELLOW}Algunos workflows fallaron conversion${NC}"
echo -e "  ${GREEN}OK:${NC} Workflows API Format generados."

# Inicializar configuracion del usuario (.env, calendar.json)
echo ""
echo "  Inicializando configuracion (.env, calendar.json)..."
python scripts/init_config.py

# Aplicar tema de marca a ComfyUI
echo ""
echo "  Aplicando tema de marca a ComfyUI..."
python scripts/apply_theme.py

# Validacion post-instalacion
echo ""
echo " ============================================================"
echo "  VALIDACION POST-INSTALACION"
echo " ============================================================"
python scripts/post_install.py

# Preguntar si iniciar todo ahora
echo ""
if [[ "$AUTO_CONFIRM" == "true" ]]; then
    START_NOW="s"
else
    read -p "Iniciar todos los servicios ahora? (S/n): " START_NOW
fi
if [[ ! "$START_NOW" =~ ^[nN]$ ]]; then
    echo ""
    echo "  Iniciando todos los servicios..."
    chmod +x start_all.sh stop_all.sh 2>/dev/null || true
    ./start_all.sh
    exit 0
fi

# ---- Final ----
echo ""
echo " ============================================================"
echo "  INSTALACION COMPLETA"
echo " ============================================================"
echo ""
echo "  Para iniciar TODO automatico:"
echo "    ./start_all.sh"
echo ""
echo "  Para detener todo:"
echo "    ./stop_all.sh"
echo ""
echo "  Dashboard de estado:"
echo "    http://127.0.0.1:8080 (despues de iniciar)"
echo ""
echo "  Documentacion en la carpeta docs/"
echo ""
chmod +x start.sh update.sh uninstall.sh 2>/dev/null || true
exit 0
