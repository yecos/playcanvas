#!/usr/bin/env bash
# Desinstalar ComfyUI Social Media Suite
cd "$(dirname "$0")"

echo ""
echo " ============================================================"
echo "  DESINSTALAR ComfyUI Social Media Suite"
echo " ============================================================"
echo ""
echo "  Esto eliminara:"
echo "    - ComfyUI (carpeta completa)"
echo "    - Entorno virtual Python (venv)"
echo "    - Modelos descargados"
echo ""
echo "  NO se eliminara:"
echo "    - Este repositorio (scripts, workflows originales, docs)"
echo "    - Python, Git u otros programas del sistema"
echo ""
read -p "  Estas seguro? (s/N): " CONFIRM
if [[ ! "$CONFIRM" =~ ^[sS]$ ]]; then
    echo "  Operacion cancelada."
    exit 0
fi

echo ""
echo "  Eliminando ComfyUI..."
rm -rf ComfyUI

echo "  Eliminando entorno virtual..."
rm -rf venv

echo ""
echo "  Desinstalacion completa."
echo "  Para reinstalar: ejecuta ./install.sh"
