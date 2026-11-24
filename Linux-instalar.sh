#!/bin/bash
cd "$(dirname "$0")"
source tools/find_python.sh
echo "== EconoFacil - Instalador (Linux) =="
if ! find_python; then
  echo "Python 3.10 a 3.13 nao encontrado. Instale com:"
  echo "  sudo apt install python3 python3-venv python3-pip    (Ubuntu/Debian)"
  echo "  sudo dnf install python3 python3-pip                 (Fedora)"
  exit 1
fi
"$PYBIN" tools/installer.py
