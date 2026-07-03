#!/usr/bin/env bash
# ============================================================
#  Instala el ComfyUI Social Suite como servicio systemd
#  Para auto-start en boot del sistema (Linux)
# ============================================================
set -e

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

SERVICE_NAME="comfyui-social"

# Detectar usuario actual
USER_NAME=$(whoami)
USER_HOME=$(eval echo "~$USER_NAME")
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo ""
echo " ============================================================"
echo "  INSTALACION DE SERVICIO SYSTEMD"
echo " ============================================================"
echo ""
echo "  Usuario:    $USER_NAME"
echo "  Proyecto:   $PROJECT_DIR"
echo "  Servicio:   ${SERVICE_NAME}@${USER_NAME}.service"
echo ""

# Copiar el template del servicio al directorio systemd
SERVICE_TEMPLATE="$PROJECT_DIR/services/comfyui-social@.service"
SERVICE_DEST="/etc/systemd/system/${SERVICE_NAME}@.service"

if [[ $EUID -ne 0 ]]; then
    echo -e "${YELLOW}AVISO:${NC} Se necesitan permisos sudo para instalar el servicio."
    sudo cp "$SERVICE_TEMPLATE" "$SERVICE_DEST"
else
    cp "$SERVICE_TEMPLATE" "$SERVICE_DEST"
fi

# Recargar systemd
echo -e "  Recargando systemd..."
sudo systemctl daemon-reload

# Habilitar el servicio para el usuario actual
echo -e "  Habilitando servicio..."
sudo systemctl enable "${SERVICE_NAME}@${USER_NAME}"

# Preguntar si iniciar ahora
read -p "Iniciar servicio ahora? (S/n): " START_NOW
if [[ ! "$START_NOW" =~ ^[nN]$ ]]; then
    sudo systemctl start "${SERVICE_NAME}@${USER_NAME}"
    sleep 5
    sudo systemctl status "${SERVICE_NAME}@${USER_NAME}" --no-pager || true
fi

echo ""
echo " ============================================================"
echo -e "  ${GREEN}SERVICIO INSTALADO${NC}"
echo " ============================================================"
echo ""
echo "  Comandos utiles:"
echo "    sudo systemctl start ${SERVICE_NAME}@${USER_NAME}     # iniciar"
echo "    sudo systemctl stop ${SERVICE_NAME}@${USER_NAME}      # detener"
echo "    sudo systemctl restart ${SERVICE_NAME}@${USER_NAME}   # reiniciar"
echo "    sudo systemctl status ${SERVICE_NAME}@${USER_NAME}    # estado"
echo "    sudo systemctl disable ${SERVICE_NAME}@${USER_NAME}   # desactivar auto-start"
echo "    journalctl -u ${SERVICE_NAME}@${USER_NAME} -f         # ver logs"
echo ""
