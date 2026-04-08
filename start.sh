#!/bin/bash

# ==============================================================================
# Sports AI - Script de Inicio
# ==============================================================================

# Colores para la salida en terminal
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # Sin color

echo -e "${BLUE}Iniciando sistema Sports AI...${NC}\n"

# 0. Limpieza automática de procesos previos y lock files
echo -e "${YELLOW}Limpiando procesos anteriores...${NC}"
lsof -ti:3000,3001,3002,3003,3004,3005,8000 2>/dev/null | xargs -r kill -9 2>/dev/null
rm -f "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/frontend/.next/dev/lock" 2>/dev/null
sleep 0.5

# 1. Obtener la ruta base del script
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Función para detener ambos servidores al cancelar el script
cleanup() {
    echo -e "\n${YELLOW}Deteniendo servicios...${NC}"
    if [ -n "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
    fi
    if [ -n "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
    fi
    echo -e "${GREEN}Servicios detenidos correctamente. ¡Hasta luego!${NC}"
    exit 0
}

# Capturar las señales de interrupción (Ctrl+C) o terminación
trap cleanup SIGINT SIGTERM

# ------------------------------------------------------------------------------
# 2. Iniciar Backend (FastAPI)
# ------------------------------------------------------------------------------
echo -e "${YELLOW}[1/2] Arrancando Backend...${NC}"
cd "$BASE_DIR"

# Activar entorno global de Python como se indica en tus reglas
PYTHON_ENV_BACKEND="$BASE_DIR/backend/venv/bin/activate"
PYTHON_ENV_GLOBAL="$HOME/.python-global/bin/activate"
if [ -f "$PYTHON_ENV_BACKEND" ]; then
    source "$PYTHON_ENV_BACKEND"
    echo -e " - Entorno virtual activado: $PYTHON_ENV_BACKEND"
elif [ -f "$PYTHON_ENV_GLOBAL" ]; then
    source "$PYTHON_ENV_GLOBAL"
    echo -e " - Entorno virtual activado: $PYTHON_ENV_GLOBAL"
else
    echo -e "${YELLOW}Advertencia: no se encontró un entorno virtual, se usará el Python del sistema.${NC}"
fi

# Iniciar backend en segundo plano
python3 -m uvicorn backend.main:app --reload --port 8000 &
BACKEND_PID=$!
echo -e "${GREEN} -> Backend iniciado correctamente (PID: $BACKEND_PID)${NC}\n"

# ------------------------------------------------------------------------------
# 3. Iniciar Frontend (Next.js)
# ------------------------------------------------------------------------------
echo -e "${YELLOW}[2/2] Arrancando Frontend...${NC}"
cd "$BASE_DIR/frontend"

# Iniciar frontend en segundo plano
npm run dev &
FRONTEND_PID=$!
echo -e "${GREEN} -> Frontend iniciado correctamente (PID: $FRONTEND_PID)${NC}\n"

# ------------------------------------------------------------------------------
# 4. Información de los servicios
# ------------------------------------------------------------------------------
echo -e "${BLUE}====================================================${NC}"
echo -e "${BLUE}Servicios en ejecución:${NC}"
echo -e " - ${GREEN}Frontend (Terminal):${NC}  http://localhost:3000"
echo -e " - ${GREEN}Backend (API):${NC}        http://localhost:8000"
echo -e " - ${GREEN}API Docs (Swagger):${NC}   http://localhost:8000/docs"
echo -e "${BLUE}====================================================${NC}"
echo -e "${YELLOW}Presiona Ctrl+C en esta terminal para detener ambos servicios.${NC}"

# Esperar de forma indefinida para mantener el script abierto
wait
