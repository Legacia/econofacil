"""Inicia o EconoFácil localmente (API + site na mesma porta) e abre o navegador.

  python tools/run.py            -> uso normal
  python tools/run.py --selftest -> sobe numa porta livre com banco temporário, testa e encerra
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import BACKEND, DATA, LOGS, ROOT, STATIC, ensure_db_compatible, find_free_port, lan_ip, runtime_env, say  # noqa: E402


def http(url: str, method: str = "GET", body: dict | None = None, headers: dict | None = None):
    data = json.dumps(body).encode() if body is not None else None
    h = {"Content-Type": "application/json", **(headers or {})}
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    with urllib.request.urlopen(req, timeout=15) as r:
        raw = r.read().decode("utf-8")
        return r.status, (json.loads(raw) if raw and raw.lstrip()[:1] in "{[" else raw)


def start_server(port: int, env: dict, logfile, host: str = "127.0.0.1") -> subprocess.Popen:
    return subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", host, "--port", str(port)],
        cwd=BACKEND, env=env, stdout=logfile, stderr=subprocess.STDOUT,
    )


def wait_ready(port: int, proc: subprocess.Popen, timeout: float = 40) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        if proc.poll() is not None:
            return False
        try:
            if http(f"http://127.0.0.1:{port}/health")[0] == 200:
                return True
        except Exception:  # noqa: BLE001
            time.sleep(0.4)
    return False


def selftest() -> int:
    """Teste de ponta a ponta: cadastro, login, catálogo, otimização, checkout e PIX."""
    LOGS.mkdir(exist_ok=True)
    port = find_free_port(8700)
    tmp = tempfile.mkdtemp(prefix="econofacil-selftest-")
    env = runtime_env(port)
    env["DATABASE_URL"] = "sqlite+aiosqlite:///" + (Path(tmp) / "t.db").as_posix()
    env["LOCAL_DEMO"] = "true"
    if subprocess.run([sys.executable, "seed.py"], cwd=BACKEND, env=env,
                      stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT).returncode != 0:
        say("seed falhou no autoteste")
        return 1
    with open(LOGS / "selftest.log", "w", encoding="utf-8") as lf:
        proc = start_server(port, env, lf)
        try:
            if not wait_ready(port, proc):
                say("servidor não iniciou")
                return 1
            base = f"http://127.0.0.1:{port}"
            api = base + "/api/v1"
            assert "<div id=\"root\"" in http(base + "/")[1], "site não carregou"
            assert "<div id=\"root\"" in http(base + "/carrinho")[1], "rota do site (SPA) falhou"

            def login(email, pw):
                _, t = http(api + "/auth/login", "POST", {"email": email, "password": pw})
                return {"Authorization": "Bearer " + t["access_token"]}

            # catálogo + comparação
            st, prods = http(api + "/catalog/products?page_size=50")
            items = prods["items"]
            assert st == 200 and len(items) >= 15, "catálogo vazio"
            by_name = {p["name"]: p["id"] for p in items}

            # contas de demonstração
            demo = login("demo@econofacil.com", "demo12345")
            admin = login("admin@econofacil.com", "admin12345")

            # Noor V2 (RN-023)
            _, usual = http(api + "/noor/recommendations/usual", "GET", None, demo)
            assert any(u["name"] == "Arroz Branco" for u in usual), "recomendação 'você costuma comprar' falhou"
            _, also = http(api + f"/noor/recommendations/also-bought?product_id={by_name['Macarrão Espaguete']}")
            assert any(a["name"] == "Molho de Tomate" and a["score"] >= 2 for a in also), "recomendação 'também comprou' falhou"

            # Receitas (RN-020)
            _, recs = http(api + "/recipes")
            assert len(recs) >= 4, "receitas não carregaram"
            http(api + f"/recipes/{recs[0]['id']}/add-to-cart", "POST", {"servings": 8}, demo)

            # Listas (RN-020)
            _, lst = http(api + "/lists", "POST", {"name": "Autoteste"}, demo)
            for pid in (by_name["Arroz Branco"], by_name["Feijão Carioca"], by_name["Leite Integral"]):
                http(api + f"/lists/{lst['id']}/items", "POST", {"product_id": pid, "quantity": 1}, demo)
            st, cmp_ = http(api + f"/lists/{lst['id']}/compare", "GET", None, demo)
            assert st == 200 and cmp_["fulfillable"], "comparação da lista falhou"
            http(api + f"/lists/{lst['id']}", "DELETE", None, demo)

            # Carrinho -> Noor (RN-018) -> checkout com PIX por loja (RN-022)
            for name in ("Arroz Branco", "Feijão Carioca", "Molho de Tomate", "Suco de Laranja"):
                http(api + "/cart/items", "POST", {"product_id": by_name[name], "quantity": 2}, demo)
            st, opt = http(api + "/cart/optimize", "GET", None, demo)
            assert st == 200 and opt["fulfillable"], "otimização falhou"
            st, order = http(api + "/cart/checkout", "POST", {"strategy": "split", "payment_method": "pix"}, demo)
            assert st == 200 and order["status"] == "awaiting_payment", "checkout falhou"
            assert len(order["payments"]) == order["store_count"] >= 2, "PIX por loja falhou"
            assert len({p["pix"]["br_code"] for p in order["payments"]}) == len(order["payments"])
            for pay in order["payments"]:
                st, paid = http(api + f"/payments/{pay['id']}/simulate-paid", "POST", None, demo)
                assert st == 200 and paid["status"] == "paid"
            _, o2 = http(api + f"/orders/{order['id']}", "GET", None, demo)
            assert o2["status"] == "placed", "pedido não foi confirmado após pagar todas as lojas"

            # Andamento por loja (RN-019): cada lojista avança só a sua parte
            owner = {"Mercado Bom Preço": "lojista1", "SuperEconomia": "lojista2", "Hiper Central": "lojista3"}
            for f in o2["fulfillments"]:
                lj = login(owner[f["store_name"]] + "@econofacil.com", "lojista123")
                st, _ = http(api + f"/merchant/orders/{order['id']}/status", "PATCH", {"status": "separating"}, lj)
                assert st == 200
            _, o3 = http(api + f"/orders/{order['id']}", "GET", None, demo)
            assert o3["status"] == "separating", "status do pedido deveria seguir a loja mais lenta"

            # Expirações (RN-021)
            st, ex = http(api + "/admin/expirations/run", "POST", None, admin)
            assert st == 200 and "carts_expired" in ex
        except Exception as e:  # noqa: BLE001
            say(f"autoteste falhou: {e!r}")
            return 1
        finally:
            proc.terminate()
            try:
                proc.wait(10)
            except subprocess.TimeoutExpired:
                proc.kill()
    say("      Autoteste OK (site, catálogo, Noor, receitas, listas, PIX por loja, andamento por loja e expirações).")
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()

    if not (BACKEND / ".env").is_file():
        say("O EconoFácil ainda não foi instalado. Rode primeiro o instalador (INSTALAR).")
        return 1
    LOGS.mkdir(exist_ok=True)
    rede = "--rede" in sys.argv   # libera o acesso por outros aparelhos da mesma rede (celular)
    port = find_free_port()
    env = runtime_env(port)

    old = ensure_db_compatible()
    if old:
        say(f"Banco de uma versão anterior guardado em data/{old.name}; criando um novo.")
    # garante banco/dados de exemplo (idempotente)
    subprocess.run([sys.executable, "seed.py"], cwd=BACKEND, env=env,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    say("=" * 60)
    say("  EconoFácil iniciando...")
    say("=" * 60)
    with open(LOGS / "servidor.log", "a", encoding="utf-8") as lf:
        proc = start_server(port, env, lf, "0.0.0.0" if rede else "127.0.0.1")
        if not wait_ready(port, proc):
            say("Não foi possível iniciar. Veja logs/servidor.log")
            proc.terminate()
            return 1
        url = f"http://localhost:{port}"
        say(f"\n  Pronto! Abra no navegador do computador:  {url}")
        if rede:
            ip = lan_ip()
            if ip:
                say("\n  ============ NO CELULAR ============")
                say(f"  Conecte o celular no MESMO Wi-Fi e abra:   http://{ip}:{port}")
                say("  ====================================")
                say("  Se o Windows perguntar sobre o Firewall, clique em 'Permitir acesso'")
                say("  (somente em rede PRIVADA/de casa).")
            else:
                say("\n  Não consegui descobrir o endereço de rede. Verifique se o computador está no Wi-Fi.")
            say("  ATENÇÃO: qualquer pessoa na sua rede consegue abrir o app. Use só em rede de confiança.")
        say("  (o navegador deve abrir sozinho)\n")
        say("  Cliente demo: demo@econofacil.com / demo12345")
        say("  Lojista:      lojista1@econofacil.com / lojista123")
        say("  Admin:        admin@econofacil.com / admin12345")
        say("  Documentação da API (técnica):  " + url + "/docs\n")
        say("  >>> Para ENCERRAR, feche esta janela (ou pressione Ctrl+C). <<<")
        try:
            webbrowser.open(url)
        except Exception:  # noqa: BLE001
            pass
        try:
            while proc.poll() is None:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(10)
                except subprocess.TimeoutExpired:
                    proc.kill()
    say("EconoFácil encerrado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
