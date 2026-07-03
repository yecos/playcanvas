#!/usr/bin/env bash
# ============================================================
#  ComfyUI Social Suite - BOOTSTRAP para Linux/macOS
#  Verifica e instala automaticamente:
#    1. Python 3.10/3.11/3.12
#    2. Git
#    3. Build essentials (gcc, make, python3-dev)
#    4. Driver NVIDIA + CUDA (verificacion)
#    5. FFmpeg (para videos)
#  Despues ejecuta install.sh automaticamente.
# ============================================================
set -e

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

cd "$(dirname "$0")"

echo ""
echo " ============================================================"
echo "  COMFYUI SOCIAL SUITE - BOOTSTRAP LINUX/MACOS"
echo "  Verificador e instalador automatico de prerrequisitos"
echo " ============================================================"
echo ""

NEED_REBOOT=false
BOOTSTRAP_OK=true

# Detectar distro
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo "$ID"
    elif [ -f /etc/debian_version ]; then
        echo "debian"
    elif [ -f /etc/redhat-release ]; then
        echo "rhel"
    elif [[ "$(uname)" == "Darwin" ]]; then
        echo "macos"
    else
        echo "unknown"
    fi
}

DISTRO=$(detect_distro)
echo -e "  ${CYAN}Distro detectada:${NC} $DISTRO"
echo ""

# Funcion: instalar paquetes segun distro
install_packages() {
    local packages=("$@")
    case "$DISTRO" in
        ubuntu|debian|pop|linuxmint)
            sudo apt-get update -qq
            sudo apt-get install -y -qq "${packages[@]}"
            ;;
        fedora|rhel|centos|rocky|alma)
            sudo dnf install -y -q "${packages[@]}"
            ;;
        arch|manjaro)
            sudo pacman -S --noconfirm --needed "${packages[@]}"
            ;;
        opensuse*|suse)
            sudo zypper install -y "${packages[@]}"
            ;;
        macos)
            if ! command -v brew &> /dev/null; then
                echo -e "  ${YELLOW}Homebrew no instalado. Instalando...${NC}"
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            brew install "${packages[@]}"
            ;;
        *)
            echo -e "  ${RED}Distro no soportada: $DISTRO${NC}"
            echo "  Instala manualmente: ${packages[*]}"
            return 1
            ;;
    esac
}

# ============================================================
# 1. Verificar Python 3.10/3.11/3.12
# ============================================================
echo -e "  ${CYAN}[1/5]${NC} Verificando Python..."
PYTHON_OK=false
PYTHON_CMD=""

for cmd in python3.12 python3.11 python3.10 python3 python; do
    if command -v $cmd &> /dev/null; then
        VER=$($cmd --version 2>&1 | awk '{print $2}')
        MAJOR=$(echo "$VER" | cut -d. -f1)
        MINOR=$(echo "$VER" | cut -d. -f2)
        if [[ "$MAJOR" == "3" ]] && [[ "$MINOR" =~ ^(10|11|12)$ ]]; then
            PYTHON_OK=true
            PYTHON_CMD=$cmd
            echo -e "  ${GREEN}OK:${NC} Python $VER ($cmd)"
            break
        fi
    fi
done

if [[ "$PYTHON_OK" != "true" ]]; then
    echo -e "  ${YELLOW}Python 3.10/3.11/3.12 no encontrado. Instalando...${NC}"
    case "$DISTRO" in
        ubuntu|debian|pop|linuxmint)
            # Ubuntu 22.04+ ya tiene 3.10/3.11
            sudo apt-get update -qq
            sudo apt-get install -y -qq software-properties-common
            # Anadir PPA deadsnakes para versiones recientes si hace falta
            if ! command -v python3.11 &> /dev/null; then
                sudo add-apt-repository -y ppa:deadsnakes/ppa
                sudo apt-get update -qq
            fi
            install_packages python3.11 python3.11-venv python3.11-dev python3-pip
            PYTHON_CMD="python3.11"
            ;;
        fedora|rhel|centos|rocky|alma)
            install_packages python3.11 python3-devel
            PYTHON_CMD="python3.11"
            ;;
        arch|manjaro)
            install_packages python
            PYTHON_CMD="python3"
            ;;
        macos)
            install_packages python@3.11
            PYTHON_CMD="python3.11"
            ;;
        *)
            echo -e "  ${RED}No se pudo instalar Python automaticamente.${NC}"
            echo "  Instala Python 3.11 manualmente."
            BOOTSTRAP_OK=false
            ;;
    esac

    if $PYTHON_CMD --version &> /dev/null; then
        echo -e "  ${GREEN}OK:${NC} Python instalado: $($PYTHON_CMD --version)"
    fi
fi

# ============================================================
# 2. Verificar Git
# ============================================================
echo ""
echo -e "  ${CYAN}[2/5]${NC} Verificando Git..."
if command -v git &> /dev/null; then
    echo -e "  ${GREEN}OK:${NC} $(git --version)"
else
    echo -e "  ${YELLOW}Git no encontrado. Instalando...${NC}"
    install_packages git
    if command -v git &> /dev/null; then
        echo -e "  ${GREEN}OK:${NC} $(git --version)"
    else
        echo -e "  ${RED}ERROR: No se pudo instalar Git${NC}"
        BOOTSTRAP_OK=false
    fi
fi

# ============================================================
# 3. Verificar build essentials
# ============================================================
echo ""
echo -e "  ${CYAN}[3/5]${NC} Verificando build essentials (gcc, make, headers)..."
if command -v gcc &> /dev/null && command -v make &> /dev/null; then
    echo -e "  ${GREEN}OK:${NC} gcc y make disponibles"
else
    echo -e "  ${YELLOW}Build essentials no encontrados. Instalando...${NC}"
    case "$DISTRO" in
        ubuntu|debian|pop|linuxmint)
            install_packages build-essential python3-dev
            ;;
        fedora|rhel|centos|rocky|alma)
            install_packages gcc gcc-c++ make
            ;;
        arch|manjaro)
            install_packages base-devel
            ;;
        macos)
            # Xcode command line tools
            xcode-select --install 2>/dev/null || true
            ;;
    esac
fi

# ============================================================
# 4. Verificar driver NVIDIA + CUDA
# ============================================================
echo ""
echo -e "  ${CYAN}[4/5]${NC} Verificando GPU NVIDIA..."
if command -v nvidia-smi &> /dev/null; then
    GPU_INFO=$(nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader 2>/dev/null | head -1)
    echo -e "  ${GREEN}OK:${NC} $GPU_INFO"

    # Verificar version del driver
    DRV_VER=$(echo "$GPU_INFO" | awk -F', ' '{print $3}' | awk -F. '{print $1}')
    if [[ -n "$DRV_VER" ]] && [[ "$DRV_VER" -lt 525 ]]; then
        echo -e "  ${YELLOW}ADVERTENCIA:${NC} Driver $DRV_VER puede ser antiguo (recomendado >= 525)"
    fi
else
    echo -e "  ${YELLOW}ADVERTENCIA:${NC} nvidia-smi no responde."
    echo "  Posibles causas:"
    echo "    - No tienes GPU NVIDIA (ComfyUI funcionara en modo CPU, muy lento)"
    echo "    - Driver NVIDIA no instalado"
    echo ""
    if [[ "$DISTRO" != "macos" ]]; then
        echo "  Para instalar driver NVIDIA en $DISTRO:"
        case "$DISTRO" in
            ubuntu|debian|pop|linuxmint)
                echo "    sudo apt install nvidia-driver-535"
                ;;
            fedora|rhel|centos|rocky|alma)
                echo "    sudo dnf install akmod-nvidia xorg-x11-drv-nvidia-cuda"
                ;;
        esac
        echo ""
        echo "  O descarga desde: https://www.nvidia.com/Download/index.aspx"
        NEED_REBOOT=true
    fi
    echo "  Continuando de todos modos..."
fi

# ============================================================
# 5. Verificar FFmpeg (para videos)
# ============================================================
echo ""
echo -e "  ${CYAN}[5/5]${NC} Verificando FFmpeg..."
if command -v ffmpeg &> /dev/null; then
    echo -e "  ${GREEN}OK:${NC} $(ffmpeg -version 2>&1 | head -1)"
else
    echo -e "  ${YELLOW}FFmpeg no encontrado. Instalando (necesario para videos)...${NC}"
    install_packages ffmpeg
    if command -v ffmpeg &> /dev/null; then
        echo -e "  ${GREEN}OK:${NC} FFmpeg instalado"
    else
        echo -e "  ${YELLOW}FFmpeg no se pudo instalar. Algunos workflows de video pueden fallar.${NC}"
    fi
fi

# ============================================================
# Final
# ============================================================
echo ""
echo " ============================================================"
if [[ "$BOOTSTRAP_OK" == "true" ]]; then
    echo -e "  ${GREEN}BOOTSTRAP COMPLETADO${NC}"
    if [[ "$NEED_REBOOT" == "true" ]]; then
        echo ""
        echo -e "  ${YELLOW}AVISO:${NC} Se instalaron componentes que requieren reinicio."
        echo "  Tras reiniciar, vuelve a ejecutar este script para continuar."
        echo ""
        exit 2
    fi
    echo ""
    echo "  Todos los prerrequisitos estan listos."
    echo "  Procediendo con la instalacion del ComfyUI Social Suite..."
    echo ""
    sleep 3
    chmod +x install.sh 2>/dev/null || true
    ./install.sh "$@"
else
    echo -e "  ${RED}BOOTSTRAP INCOMPLETO${NC}"
    echo ""
    echo "  Resuelve los errores arriba y vuelve a ejecutar este script."
    exit 1
fi
