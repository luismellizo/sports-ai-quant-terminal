#!/bin/bash
# ==========================================
# Build Backend for Windows (via PyInstaller)
# ==========================================

echo "🛠️ Preparando Backend para empaquetado..."

# Directorio base
BASE_DIR=$(pwd)
WINDOWS_DIR="$BASE_DIR/WINDOWS"
DIST_DIR="$WINDOWS_DIR/dist"

mkdir -p "$DIST_DIR"

# 1. Empaquetar el Runner y el Backend
# Usamos PyInstaller para crear un ejecutable de un solo directorio
# Nota: Para un .exe real se recomienda correr esto en Windows o vía Wine
echo "🚀 Ejecutando PyInstaller..."

# Agregamos la carpeta backend como data
pyinstaller --noconfirm --onedir --console \
    --name "SportsAI_Runner" \
    --add-data "$BASE_DIR/backend:backend" \
    --add-data "$WINDOWS_DIR/loro.png:." \
    --paths "$BASE_DIR" \
    "$WINDOWS_DIR/runner.py"

# Movemos los resultados a la carpeta de distribución del instalador
cp -r dist/SportsAI_Runner/* "$DIST_DIR/"

echo "✅ Backend procesado en $DIST_DIR"
