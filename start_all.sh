#!/usr/bin/env bash
# ============================================================
#  ComfyUI Social Suite - Arranque Automatico de TODOS los servicios
#  Inicia:
#    1. ComfyUI (generacion de imagenes/video)
#    2. Queue Worker (cola con reintentos)
#    3. Webhook Server (event-driven publishing)
#    4. Telegram Bot (control remoto, opcional)
#    5. Dashboard web (estado, opcional)
# ============================================================
set -e
cd "$(dirname "$0")"

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

echo ""
echo " ============================================================"
echo "  COMFYUI SOCIAL SUITE - ARRANQUE AUTOMATICO"
echo " ============================================================"
echo ""

# Verificar instalacion
if [ ! -f "ComfyUI/main.py" ]; then
    echo -e "${RED}ERROR:${NC} ComfyUI no esta instalado. Ejecuta ./install.sh primero."
    exit 1
fi

if [ ! -f "venv/bin/activate" ]; then
    echo -e "${RED}ERROR:${NC} Entorno virtual no existe. Ejecuta ./install.sh primero."
    exit 1
fi

# Crear carpetas
mkdir -p logs run

# Detener procesos previos
echo -e "  ${CYAN}[0/5]${NC} Deteniendo servicios previos..."
./stop_all.sh 2>/dev/null || true
sleep 2

# Activar venv
source venv/bin/activate

# Leer launch_args
LAUNCH_ARGS=""
if [ -f "config/launch_args.txt" ]; then
    while IFS= read -r line; do
        [[ "$line" =~ ^[[:space:]]*# ]] && continue
        [[ -z "${line// }" ]] && continue
        LAUNCH_ARGS="$LAUNCH_ARGS $line"
    done < "config/launch_args.txt"
fi

# 1. ComfyUI
echo ""
echo -e "  ${CYAN}[1/5]${NC} Iniciando ComfyUI en http://127.0.0.1:8188 ..."
nohup bash -c "cd ComfyUI && python main.py $LAUNCH_ARGS" > logs/comfyui.log 2>&1 &
echo $! > run/comfyui.pid
echo -e "     PID: $(cat run/comfyui.pid). Log: logs/comfyui.log"

# Esperar a que ComfyUI responda (max 90s)
echo -e "     Esperando respuesta (max 90s)..."
WAIT=0
while [ $WAIT -lt 90 ]; do
    if curl -s -o /dev/null http://127.0.0.1:8188/system_stats 2>/dev/null; then
        echo -e "     ${GREEN}OK:${NC} ComfyUI responde (${WAIT}s)"
        break
    fi
    sleep 2
    WAIT=$((WAIT + 2))
done

if [ $WAIT -ge 90 ]; then
    echo -e "${RED}ERROR:${NC} ComfyUI no respondio en 90 segundos."
    echo "  Revisa logs/comfyui.log"
    exit 1
fi

# Abrir navegador
(
    sleep 1
    if command -v xdg-open &> /dev/null; then
        xdg-open http://127.0.0.1:8188
    elif command -v open &> /dev/null; then
        open http://127.0.0.1:8188
    fi
) &

# 2. Queue Worker
echo ""
echo -e "  ${CYAN}[2/5]${NC} Iniciando Queue Worker..."
nohup python scripts/queue_manager.py worker --poll-interval 10 > logs/queue_worker.log 2>&1 &
echo $! > run/queue_worker.pid
echo -e "     PID: $(cat run/queue_worker.pid). Log: logs/queue_worker.log"

# 3. Webhook Server
echo ""
echo -e "  ${CYAN}[3/5]${NC} Iniciando Webhook Server en http://127.0.0.1:8189 ..."
nohup python scripts/webhook_server.py --port 8189 > logs/webhook_server.log 2>&1 &
echo $! > run/webhook_server.pid
echo -e "     PID: $(cat run/webhook_server.pid). Log: logs/webhook_server.log"

# 4. Telegram Bot (si hay token)
TG_TOKEN=""
if [ -f ".env" ]; then
    TG_TOKEN=$(grep "^TELEGRAM_BOT_TOKEN=" .env 2>/dev/null | cut -d'=' -f2-)
fi
if [ -n "$TG_TOKEN" ]; then
    echo ""
    echo -e "  ${CYAN}[4/5]${NC} Iniciando Telegram Bot..."
    nohup python scripts/bot_telegram.py > logs/telegram_bot.log 2>&1 &
    echo $! > run/telegram_bot.pid
    echo -e "     PID: $(cat run/telegram_bot.pid). Log: logs/telegram_bot.log"
else
    echo ""
    echo -e "  ${CYAN}[4/5]${NC} Telegram Bot: ${YELLOW}SKIPPED${NC} (TELEGRAM_BOT_TOKEN no configurado)"
fi

# 5. Dashboard (si flask disponible)
if python -c "import flask" 2>/dev/null; then
    echo ""
    echo -e "  ${CYAN}[5/5]${NC} Iniciando Dashboard en http://127.0.0.1:8080 ..."
    nohup python scripts/dashboard.py > logs/dashboard.log 2>&1 &
    echo $! > run/dashboard.pid
    echo -e "     PID: $(cat run/dashboard.pid). Log: logs/dashboard.log"
    sleep 2
    (
        if command -v xdg-open &> /dev/null; then
            xdg-open http://127.0.0.1:8080
        elif command -v open &> /dev/null; then
            open http://127.0.0.1:8080
        fi
    ) &
else
    echo ""
    echo -e "  ${CYAN}[5/5]${NC} Dashboard: ${YELLOW}SKIPPED${NC} (flask no instalado)"
fi

# Final
echo ""
echo " ============================================================"
echo -e "  ${GREEN}TODOS LOS SERVICIOS INICIADOS${NC}"
echo " ============================================================"
echo ""
echo "  ComfyUI:         http://127.0.0.1:8188"
echo "  Webhook Server:  http://127.0.0.1:8189"
echo "  Dashboard:       http://127.0.0.1:8080"
echo ""
echo "  Logs en:         logs/"
echo "  PIDs en:         run/"
echo ""
echo "  Para detener todo:   ./stop_all.sh"
echo "  Para estado:         curl http://127.0.0.1:8080/api/status"
echo ""
chmod +x stop_all.sh 2>/dev/null || true
