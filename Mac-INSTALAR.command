#!/bin/bash
cd "$(dirname "$0")"
source tools/find_python.sh
echo "== EconoFacil - Instalador (Mac) =="
if ! find_python; then
  echo
  echo "Python (versao 3.10 a 3.13) nao encontrado."
  echo "1) Baixe o Python 3.12 em: https://www.python.org/downloads/macos/"
  echo "2) Instale (clique em Continuar ate o fim) e rode este instalador de novo."
  open "https://www.python.org/downloads/macos/" 2>/dev/null
  read -n 1 -s -r -p "Pressione qualquer tecla para fechar..."
  exit 1
fi
"$PYBIN" tools/installer.py
echo
read -n 1 -s -r -p "Pressione qualquer tecla para fechar..."
