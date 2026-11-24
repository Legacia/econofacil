# Procura um Python 3.10–3.13 no Mac/Linux. Define PYBIN.
find_python() {
  for c in python3.12 python3.13 python3.11 python3.10 \
           /Library/Frameworks/Python.framework/Versions/3.12/bin/python3 \
           /opt/homebrew/bin/python3 /usr/local/bin/python3 python3 python; do
    if command -v "$c" >/dev/null 2>&1 && \
       "$c" -c 'import sys; sys.exit(0 if (3,10)<=sys.version_info[:2]<=(3,13) else 1)' >/dev/null 2>&1; then
      PYBIN="$(command -v "$c")"
      return 0
    fi
  done
  return 1
}
