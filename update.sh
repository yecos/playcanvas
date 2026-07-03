#!/usr/bin/env bash
# Actualizar ComfyUI Social Media Suite
cd "$(dirname "$0")"

echo ""
echo " ============================================================"
echo "  Actualizando ComfyUI Social Media Suite"
echo " ============================================================"

if [ ! -f "venv/bin/activate" ]; then
    echo "ERROR: Ejecuta ./install.sh primero."
    exit 1
fi

source venv/bin/activate

echo "  [1/4] Actualizando ComfyUI..."
cd ComfyUI && git pull && cd ..

echo "  [2/4] Actualizando ComfyUI-Manager..."
cd ComfyUI/custom_nodes/ComfyUI-Manager && git pull && cd ../../..

echo "  [3/4] Actualizando dependencias..."
pip install -r ComfyUI/requirements.txt --upgrade
pip install -r requirements.txt --upgrade

echo "  [4/4] Actualizando custom nodes..."
python scripts/install_custom_nodes.py --update

echo ""
echo "  Actualizacion completa."
