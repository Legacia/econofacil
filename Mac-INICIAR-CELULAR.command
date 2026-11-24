#!/bin/bash
cd "$(dirname "$0")"
if [ ! -x ".venv/bin/python" ]; then
  echo "O EconoFacil ainda nao foi instalado. De dois cliques em Mac-INSTALAR.command primeiro."
  read -n 1 -s -r -p "Pressione qualquer tecla para fechar..."
  exit 1
fi
.venv/bin/python tools/run.py --rede
read -n 1 -s -r -p "Pressione qualquer tecla para fechar..."
