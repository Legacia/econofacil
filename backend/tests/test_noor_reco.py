"""RN-023 — Noor V2: recomendações contextuais (co-ocorrência e compra recorrente)."""
from tests.helpers import API, checkout, consumer, fill_cart, merchant, new_product, new_store, offer


async def _world(client, make_privileged_user):
    hm = await merchant(client, make_privileged_user, "reco@ef.com")
    store = await new_store(client, hm, "reco")
    ids = {}
    for name, price in (("Macarrão", 4.0), ("Molho", 3.0), ("Queijo", 6.0), ("Leite", 5.0), ("Esgotado", 9.0)):
        ids[name] = await new_product(client, hm, name)
        await offer(client, hm, store, ids[name], price)
    return hm, ids


async def _buy(client, hc, ids, *names):
    await fill_cart(client, hc, *[(ids[n], 1) for n in names])
    return await checkout(client, hc, "econopay", strategy="single")


async def test_also_bought_ranks_by_cooccurrence(client, make_privileged_user):
    _, ids = await _world(client, make_privileged_user)
    c1, c2, c3 = await consumer(client, "c1@ef.com"), await consumer(client, "c2@ef.com"), await consumer(client, "c3@ef.com")
    await _buy(client, c1, ids, "Macarrão", "Molho", "Queijo")
    await _buy(client, c2, ids, "Macarrão", "Molho")
    await _buy(client, c3, ids, "Macarrão", "Leite")
    res = (await client.get(f"{API}/noor/recommendations/also-bought?product_id={ids['Macarrão']}")).json()
    assert [r["name"] for r in res] == ["Molho", "Leite", "Queijo"]    # empate (Leite/Queijo): 1 pedido cada
    assert res[0]["name"] == "Molho" and res[0]["score"] == 2
    assert "Macarrão" not in [r["name"] for r in res]               # nunca recomenda o próprio produto
    assert res[0]["best_price"] == 3.0 and "2 pedidos" in res[0]["reason"]


async def test_also_bought_is_public_and_has_no_personal_data(client, make_privileged_user):
    _, ids = await _world(client, make_privileged_user)
    await _buy(client, await consumer(client, "p1@ef.com"), ids, "Macarrão", "Molho")
    r = await client.get(f"{API}/noor/recommendations/also-bought?product_id={ids['Macarrão']}")   # sem login
    assert r.status_code == 200
    assert set(r.json()[0]) == {"product_id", "name", "package", "best_price", "score", "reason"}


async def test_also_bought_ignores_cancelled_orders(client, make_privileged_user, db):
    from sqlalchemy import select
    from app.models.order import Order, OrderStatus
    _, ids = await _world(client, make_privileged_user)
    hc = await consumer(client, "canc@ef.com")
    order = await _buy(client, hc, ids, "Macarrão", "Molho")
    o = (await db.execute(select(Order).where(Order.code == order["code"]))).scalar_one()
    o.status = OrderStatus.CANCELLED
    await db.commit()
    assert (await client.get(f"{API}/noor/recommendations/also-bought?product_id={ids['Macarrão']}")).json() == []


async def test_also_bought_skips_items_without_offer(client, make_privileged_user, db):
    from sqlalchemy import delete
    from app.models.catalog import StoreProduct
    import uuid
    _, ids = await _world(client, make_privileged_user)
    await _buy(client, await consumer(client, "s1@ef.com"), ids, "Macarrão", "Esgotado")
    await db.execute(delete(StoreProduct).where(StoreProduct.product_id == uuid.UUID(ids["Esgotado"])))
    await db.commit()
    assert (await client.get(f"{API}/noor/recommendations/also-bought?product_id={ids['Macarrão']}")).json() == []


async def test_usual_requires_login(client):
    assert (await client.get(f"{API}/noor/recommendations/usual")).status_code == 401


async def test_usual_needs_repeat_purchases(client, make_privileged_user):
    _, ids = await _world(client, make_privileged_user)
    hc = await consumer(client)
    await _buy(client, hc, ids, "Macarrão", "Leite")
    assert (await client.get(f"{API}/noor/recommendations/usual", headers=hc)).json() == []     # 1 compra só
    await _buy(client, hc, ids, "Macarrão", "Molho")
    res = (await client.get(f"{API}/noor/recommendations/usual", headers=hc)).json()
    assert [r["name"] for r in res] == ["Macarrão"] and res[0]["score"] == 2
    assert "2 vezes" in res[0]["reason"]


async def test_usual_excludes_what_is_already_in_cart(client, make_privileged_user):
    _, ids = await _world(client, make_privileged_user)
    hc = await consumer(client)
    await _buy(client, hc, ids, "Macarrão")
    await _buy(client, hc, ids, "Macarrão")
    await fill_cart(client, hc, (ids["Macarrão"], 1))
    assert (await client.get(f"{API}/noor/recommendations/usual", headers=hc)).json() == []


async def test_usual_is_per_user(client, make_privileged_user):
    _, ids = await _world(client, make_privileged_user)
    a, b = await consumer(client, "ua@ef.com"), await consumer(client, "ub@ef.com")
    await _buy(client, a, ids, "Macarrão")
    await _buy(client, a, ids, "Macarrão")
    assert (await client.get(f"{API}/noor/recommendations/usual", headers=b)).json() == []
    assert len((await client.get(f"{API}/noor/recommendations/usual", headers=a)).json()) == 1


async def test_noor_status_lists_recommendation_engine(client):
    st = (await client.get(f"{API}/noor/status")).json()
    assert st["recommendations"]["methods"] == ["also-bought", "usual"]
