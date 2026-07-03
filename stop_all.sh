#!/usr/bin/env bash
# Detener todos los servicios del ComfyUI Social Suite
cd "$(dirname "$0")"

GREEN='\033[0;32m'
NC='\033[0m'

echo ""
echo " ============================================================"
echo "  DETENIENDO TODOS LOS SERVICIOS"
echo " ============================================================"
echo ""

# Detener por PID files
for service in comfyui queue_worker webhook_server telegram_bot dashboard; do
    PID_FILE="run/${service}.pid"
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo "  Deteniendo $service (PID $PID)..."
            kill "$PID" 2>/dev/null || true
            # Dar 2s para shutdown graceful
            sleep 1
            kill -9 "$PID" 2>/dev/null || true
        fi
        rm -f "$PID_FILE"
    fi
done

# Backup: matar por puerto
echo "  Verificando puertos (8188, 8189, 8080)..."
for port in 8188 8189 8080; do
    PIDS=$(lsof -ti :$port 2>/dev/null || true)
    if [ -n "$PIDS" ]; then
        kill -9 $PIDS 2>/dev/null || true
    fi
done

echo ""
echo -e "  ${GREEN}Todos los servicios detenidos.${NC}"
echo ""
