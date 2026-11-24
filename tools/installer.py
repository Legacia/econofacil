"""Instalador do EconoFácil (uso local).

Passos: confere o Python -> cria ambiente isolado (.venv) -> instala dependências
-> gera configuração com chaves aleatórias -> cria o banco com dados de exemplo
-> faz um teste automático de funcionamento -> (Windows) cria atalho na área de trabalho.
"""
from __future__ import annotations

import os
import secrets
import subprocess
import sys
import venv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    BACKEND, DATA, ENV_FILE, LOGS, ROOT, STATIC, VENV,
    check_python_version, ensure_db_compatible, runtime_env, say, venv_python,
)


def fail(msg: str) -> None:
    say()
    say("=" * 60)
    say("  NÃO FOI POSSÍVEL CONCLUIR A INSTALAÇÃO")
    say("=" * 60)
    say(msg)
    say()
    say("Se precisar de ajuda, envie o arquivo  logs/instalacao.log  para quem te mandou o pacote.")
    sys.exit(1)


def run(cmd: list[str], log, cwd: Path | None = None, env: dict | None = None) -> int:
    log.write("\n$ " + " ".join(map(str, cmd)) + "\n")
    log.flush()
    p = subprocess.run(cmd, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT)
    return p.returncode


def main() -> None:
    say("=" * 60)
    say("  EconoFácil — Instalação")
    say("=" * 60)

    # 1) Python
    v = sys.version_info
    say(f"[1/6] Verificando o Python... (encontrado {v.major}.{v.minor}.{v.micro})")
    if not check_python_version():
        fail(
            f"Esta instalação funciona com Python 3.10 a 3.13 (recomendado: 3.12).\n"
            f"Versão encontrada: {v.major}.{v.minor}.{v.micro}.\n"
            "Baixe o Python 3.12 em https://www.python.org/downloads/ e rode o instalador de novo.\n"
            "No Windows, marque a opção 'Add python.exe to PATH' durante a instalação."
        )
    if not (STATIC / "index.html").is_file():
        fail("A pasta 'static' (site pronto) não foi encontrada. O pacote parece incompleto.")

    LOGS.mkdir(exist_ok=True)
    DATA.mkdir(exist_ok=True)
    with open(LOGS / "instalacao.log", "w", encoding="utf-8") as log:
        # 2) Ambiente isolado
        say("[2/6] Criando ambiente isolado (.venv)...")
        if not venv_python().is_file():
            try:
                venv.EnvBuilder(with_pip=True, clear=False).create(VENV)
            except Exception as e:  # noqa: BLE001
                log.write(repr(e))
                fail(
                    "Não consegui criar o ambiente isolado.\n"
                    "No Linux (Ubuntu/Debian), instale com:  sudo apt install python3-venv  e tente de novo."
                )
        py = str(venv_python())

        # 3) Dependências
        say("[3/6] Instalando componentes (precisa de internet; pode levar 1–3 minutos)...")
        run([py, "-m", "pip", "install", "--upgrade", "pip", "--disable-pip-version-check", "-q"], log)
        rc = run(
            [py, "-m", "pip", "install", "-r", str(BACKEND / "requirements-local.txt"),
             "--disable-pip-version-check", "-q"], log,
        )
        if rc != 0:
            fail("Falha ao baixar/instalar os componentes. Verifique sua conexão com a internet e tente de novo.")

        # 4) Configuração
        say("[4/6] Gerando configuração com chaves de segurança próprias...")
        if not ENV_FILE.exists():
            ENV_FILE.write_text(
                "# Gerado automaticamente pelo instalador — não compartilhe este arquivo.\n"
                'ENVIRONMENT="development"\n'
                "DEBUG=false\n"
                f'SECRET_KEY="{secrets.token_urlsafe(64)}"\n'
                f'PIX_WEBHOOK_SECRET="{secrets.token_urlsafe(32)}"\n'
                'PIX_KEY="pagamentos@econofacil.com.br"\n'
                "LOCAL_DEMO=true\n",
                encoding="utf-8",
            )

        # 5) Banco de dados
        say("[5/6] Criando o banco de dados com produtos de exemplo...")
        old = ensure_db_compatible()
        if old:
            say(f"      (Banco de uma versão anterior guardado em: data/{old.name})")
        rc = run([py, "seed.py"], log, cwd=BACKEND, env=runtime_env())
        if rc != 0:
            fail("Falha ao criar o banco de dados local.")

        # 6) Autoteste
        say("[6/6] Testando se tudo está funcionando...")
        rc = run([py, str(ROOT / "tools" / "run.py"), "--selftest"], log, cwd=ROOT)
        if rc != 0:
            fail("O teste automático falhou. O detalhe está em logs/instalacao.log.")

    create_shortcut()
    say()
    say("=" * 60)
    say("  INSTALAÇÃO CONCLUÍDA COM SUCESSO!")
    say("=" * 60)
    say("Para usar o EconoFácil, dê dois cliques em:")
    if os.name == "nt":
        say("   Windows-INICIAR.bat   (ou no atalho 'EconoFácil' da área de trabalho)")
    elif sys.platform == "darwin":
        say("   Mac-INICIAR.command")
    else:
        say("   Linux-iniciar.sh")
    say()
    say("Contas de teste (modo demonstração):")
    say("   Cliente : demo@econofacil.com      / demo12345")
    say("   Lojista : lojista1@econofacil.com  / lojista123   (também lojista2 e lojista3)")
    say("   Admin   : admin@econofacil.com     / admin12345")


def create_shortcut() -> None:
    """Atalho na área de trabalho (apenas Windows; falha silenciosa)."""
    if os.name != "nt":
        return
    try:
        target = ROOT / "Windows-INICIAR.bat"
        ps = (
            "$d=[Environment]::GetFolderPath('Desktop');"
            "$s=(New-Object -ComObject WScript.Shell).CreateShortcut($d+'\\EconoFacil.lnk');"
            f"$s.TargetPath='{target}';$s.WorkingDirectory='{ROOT}';"
            "$s.Description='Abrir o EconoFacil';$s.Save()"
        )
        subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=False,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
        say("      Atalho 'EconoFacil' criado na área de trabalho.")
    except Exception:  # noqa: BLE001
        pass


if __name__ == "__main__":
    main()
