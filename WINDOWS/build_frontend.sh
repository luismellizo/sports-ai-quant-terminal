#!/bin/bash
# ==========================================
# Build Frontend for Windows
# ==========================================

echo "🎨 Preparando Frontend para empaquetado..."

# Directorio base
BASE_DIR=$(pwd)
FRONTEND_DIR="$BASE_DIR/frontend"
WINDOWS_DIR="$BASE_DIR/WINDOWS"
DIST_DIR="$WINDOWS_DIR/dist/frontend"

mkdir -p "$DIST_DIR"

# 1. Compilar Next.js
cd "$FRONTEND_DIR" || exit
echo "📦 Instalando dependencias y compilando..."
npm install
npm run build

# Si usas modo 'export' (estático), los archivos estarán en 'out'
# Si usas modo 'standalone', estarán en '.next/standalone'
if [ -d "out" ]; then
    cp -r out/* "$DIST_DIR/"
else
    echo "⚠️ Nota: No se detectó carpeta 'out'. Copiando build estándar..."
    cp -r .next "$DIST_DIR/"
    cp -r public "$DIST_DIR/"
    cp package.json "$DIST_DIR/"
fi

echo "✅ Frontend procesado en $DIST_DIR"
