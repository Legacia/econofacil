# EconoFácil

Ecossistema de compras inteligentes de supermercado: compara preços entre lojas, e a IA **Noor** monta a cesta mais barata, dividindo a compra entre até 3 lojas quando compensa (split).

> **Versão de demonstração local.** PIX simulado, banco SQLite, contas de teste com senha fixa. Não use para vendas reais nem exponha à internet.

## Funções

- Catálogo com comparação de preço unitário entre lojas
- Carrinho otimizado pela Noor (loja única × split, economia mínima de 2%)
- Checkout com **PIX por loja** (um QR Code para cada loja) e EconoPay
- **Andamento do pedido por loja**: cada lojista atualiza a sua parte; o pedido segue a loja mais lenta
- Receitas (com ajuste de porções) e listas de compras permanentes com comparação de preços
- **Noor V2**: "quem comprou também comprou" e "você costuma comprar"
- Portal do lojista (pedidos, estoque, promoções, relatório, chave PIX) e painel do admin
- Expirações automáticas (carrinhos, promoções, cobranças PIX)
- LGPD: consentimento, exportação e exclusão de dados

## Instalação rápida (quem só quer usar)

1. Extraia/clone a pasta.
2. Dê dois cliques em `Windows-INSTALAR.bat` (Mac: `Mac-INSTALAR.command`, Linux: `Linux-instalar.sh`).
3. Depois use `Windows-INICIAR.bat` (ou `...INICIAR-CELULAR` para abrir no celular, no mesmo Wi-Fi).

Detalhes e roteiro de teste em [`LEIA-ME.txt`](LEIA-ME.txt). Precisa de Python 3.10 a 3.13.

## Contas de teste (modo demonstração)

| Perfil  | E-mail                      | Senha       |
|---------|-----------------------------|-------------|
| Cliente | demo@econofacil.com         | demo12345   |
| Lojista | lojista1@econofacil.com (2 e 3 também) | lojista123 |
| Admin   | admin@econofacil.com        | admin12345  |

## Para desenvolvedores

```bash
# backend (API FastAPI)
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-local.txt pytest pytest-asyncio httpx
pytest -q                      # 96 testes
DATABASE_URL="sqlite+aiosqlite:///./dev.db" python seed.py
DATABASE_URL="sqlite+aiosqlite:///./dev.db" LOCAL_DEMO=true uvicorn app.main:app --reload

# frontend (React + Vite)
cd frontend
npm install
npm run dev                    # http://localhost:5173 (usa a API em VITE_API_URL)
VITE_API_URL=/api/v1 npm run build   # gera dist/ (copie para static/ para o backend servir)
```

## Estrutura

```
backend/      API FastAPI + SQLAlchemy 2.0 async + Noor (solver ILP)
frontend/     App React + Vite (código-fonte)
static/       Front-end já compilado (servido pelo backend)
tools/        Instalador e iniciador (Python, só biblioteca padrão)
android-app/  Casca Android (Capacitor) — workflow "Gerar APK do EconoFácil"
.github/      Testes automáticos e geração do APK
```

## Ainda não existe

EconoClub (pontos/cashback), pagamento por cartão, PSP de PIX real, envio de e-mail, banco persistente de produção (PostgreSQL) e agendador multi-worker.
