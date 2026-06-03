#!/bin/bash
# Instala dependências (só na primeira vez) e inicia o app

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "→ Verificando dependências..."
pip3 install pywebview psutil --quiet

echo "→ Iniciando PC Optimizer..."
python3 main.py
