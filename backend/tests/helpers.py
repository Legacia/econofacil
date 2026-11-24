"""Cenários compartilhados pelos testes das melhorias RN-019 a RN-023."""
from app.models.user import UserRole

LOGIN = "/api/v1/auth/login"
API = "/api/v1"


async def login(client, email, password):
    tok = (await client.post(LOGIN, json={"email": email, "password": password})).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


async def merchant(client, make_privileged_user, email):
    await make_privileged_user(email, "MerchPass1", UserRole.MERCHANT)
    return await login(client, email, "MerchPass1")


async def admin(client, make_privileged_user, email="adm@ef.com"):
    await make_privileged_user(email, "AdminPass1", UserRole.ADMIN)
    return await login(client, email, "AdminPass1")


async def consumer(client, email="cli@ef.com"):
    await client.post(f"{API}/auth/register", json={"email": email, "full_name": "Cli", "password": "SenhaForte1"})
    return await login(client, email, "SenhaForte1")


async def new_product(client, h, name, size=1, unit="kg"):
    return (await client.post(f"{API}/catalog/products", json={"name": name, "package_size": size, "package_unit": unit}, headers=h)).json()["id"]


async def new_store(client, h, slug):
    return (await client.post(f"{API}/catalog/stores", json={"name": f"Loja {slug}", "slug": slug}, headers=h)).json()["id"]


async def offer(client, h, store, product, price, stock=100):
    await client.put(f"{API}/catalog/stores/{store}/offers/{product}", json={"price": price, "stock_quantity": stock}, headers=h)


async def split_world(client, make_privileged_user):
    """2 lojas (A e B, de lojistas diferentes) e 2 produtos em que o SPLIT compensa:
    Arroz: A=10 / B=20; Feijão: A=20 / B=8  ->  split = 10 + 8 = 18 (loja única: 28)."""
    ha = await merchant(client, make_privileged_user, "a@ef.com")
    hb = await merchant(client, make_privileged_user, "b@ef.com")
    store_a = await new_store(client, ha, "a")
    store_b = await new_store(client, hb, "b")
    arroz = await new_product(client, ha, "Arroz")
    feijao = await new_product(client, ha, "Feijão")
    await offer(client, ha, store_a, arroz, 10.0)
    await offer(client, ha, store_a, feijao, 20.0)
    await offer(client, hb, store_b, arroz, 20.0)
    await offer(client, hb, store_b, feijao, 8.0)
    hc = await consumer(client)
    return dict(ha=ha, hb=hb, hc=hc, store_a=store_a, store_b=store_b, arroz=arroz, feijao=feijao)


async def fill_cart(client, hc, *pairs):
    for pid, qty in pairs:
        await client.post(f"{API}/cart/items", json={"product_id": pid, "quantity": qty}, headers=hc)


async def checkout(client, hc, method="econopay", strategy="split"):
    r = await client.post(f"{API}/cart/checkout", json={"strategy": strategy, "payment_method": method}, headers=hc)
    assert r.status_code == 200, r.text
    return r.json()
