#!/usr/bin/env bash
# ============================================================
#  Lanzador de ComfyUI Social Media Suite (Linux/macOS)
# ============================================================
cd "$(dirname "$0")"

if [ ! -f "venv/bin/activate" ]; then
    echo "ERROR: No se encontro el entorno virtual."
    echo "Ejecuta ./install.sh primero."
    exit 1
fi

if [ ! -f "ComfyUI/main.py" ]; then
    echo "ERROR: No se encontro ComfyUI."
    echo "Ejecuta ./install.sh primero."
    exit 1
fi

# ---- Leer argumentos de lanzamiento ----
LAUNCH_ARGS=""
if [ -f "config/launch_args.txt" ]; then
    while IFS= read -r line; do
        # Ignorar comentarios y lineas vacias
        [[ "$line" =~ ^[[:space:]]*# ]] && continue
        [[ -z "${line// }" ]] && continue
        LAUNCH_ARGS="$LAUNCH_ARGS $line"
    done < "config/launch_args.txt"
fi

echo ""
echo " ============================================================"
echo "  Iniciando ComfyUI Social Media Suite..."
echo " ============================================================"
echo "  Argumentos: $LAUNCH_ARGS"
echo "  URL: http://127.0.0.1:8188"
echo " ============================================================"
echo ""

source venv/bin/activate
cd ComfyUI

# Abrir navegador cuando ComfyUI responda (poll cada 2s, max 60s)
(
    for i in $(seq 1 30); do
        if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8188/system_stats 2>/dev/null | grep -q "200"; then
            if command -v xdg-open &> /dev/null; then
                xdg-open http://127.0.0.1:8188
            elif command -v open &> /dev/null; then
                open http://127.0.0.1:8188
            fi
            break
        fi
        sleep 2
    done
) &

python main.py $LAUNCH_ARGS
