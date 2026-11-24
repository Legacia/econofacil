"""Funções compartilhadas entre o instalador e o iniciador (somente biblioteca padrão)."""
from __future__ import annotations

import os
import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
STATIC = ROOT / "static"
DATA = ROOT / "data"
LOGS = ROOT / "logs"
VENV = ROOT / ".venv"
ENV_FILE = BACKEND / ".env"
DEFAULT_PORT = 8000

MIN_PY = (3, 10)
MAX_PY = (3, 13)  # versões testadas: 3.10 a 3.13


def venv_python() -> Path:
    if os.name == "nt":
        return VENV / "Scripts" / "python.exe"
    return VENV / "bin" / "python"


def port_is_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) != 0


def find_free_port(start: int = DEFAULT_PORT) -> int:
    for p in range(start, start + 50):
        if port_is_free(p):
            return p
    raise RuntimeError("Nenhuma porta livre encontrada entre %d e %d" % (start, start + 49))


def say(msg: str = "") -> None:
    print(msg, flush=True)


def check_python_version() -> bool:
    v = sys.version_info[:2]
    return MIN_PY <= v <= MAX_PY


def runtime_env(port: int | None = None) -> dict[str, str]:
    """Variáveis de ambiente do servidor local (sobrepõem o .env)."""
    env = os.environ.copy()
    DATA.mkdir(exist_ok=True)
    env["DATABASE_URL"] = "sqlite+aiosqlite:///" + (DATA / "econofacil.db").as_posix()
    env["STATIC_DIR"] = str(STATIC)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    # CORS não é necessário: site e API são servidos na mesma origem/porta.
    return env


def ensure_db_compatible():
    """Se existir um banco criado por uma versão ANTERIOR do EconoFácil (sem as tabelas/colunas
    novas), guarda uma cópia de segurança e deixa o instalador criar um banco novo.
    Devolve o caminho da cópia, ou None se nada precisou ser feito."""
    import sqlite3
    import time

    db = DATA / "econofacil.db"
    if not db.is_file():
        return None
    con = sqlite3.connect(str(db))
    try:
        tables = {r[0] for r in con.execute("select name from sqlite_master where type='table'")}
        pay_cols = {r[1] for r in con.execute("pragma table_info(payments)")}
        store_cols = {r[1] for r in con.execute("pragma table_info(stores)")}
    finally:
        con.close()
    needed = {"order_fulfillments", "recipes", "recipe_ingredients", "shopping_lists", "shopping_list_items"}
    if needed <= tables and "store_id" in pay_cols and "pix_key" in store_cols:
        return None
    backup = db.with_name("econofacil.db.antigo-" + time.strftime("%Y%m%d-%H%M%S"))
    db.rename(backup)
    return backup


def lan_ip() -> str | None:
    """Endereço do computador na rede local (Wi-Fi/cabo), ex.: 192.168.0.12."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))  # não envia nada; só descobre a interface de rede usada
        ip = s.getsockname()[0]
        return None if ip.startswith("127.") else ip
    except OSError:
        return None
    finally:
        s.close()
