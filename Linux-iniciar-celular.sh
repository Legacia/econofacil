#!/bin/bash
cd "$(dirname "$0")"
if [ ! -x ".venv/bin/python" ]; then
  echo "O EconoFacil ainda nao foi instalado. Rode primeiro:  ./Linux-instalar.sh"
  exit 1
fi
exec .venv/bin/python tools/run.py --rede
