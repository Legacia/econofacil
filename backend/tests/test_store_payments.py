"""RN-022 — liquidação Pix por loja: um pagamento (e um QR) para cada loja."""
from app.models.catalog import Store
from app.payments import pix
from app.core.config import settings
from tests.helpers import API, checkout, fill_cart, split_world


async def _pix_split(client, make_privileged_user):
    w = await split_world(client, make_privileged_user)
    await fill_cart(client, w["hc"], (w["arroz"], 1), (w["feijao"], 1))
    return w, await checkout(client, w["hc"], "pix")


def _webhook(client, txid):
    return client.post(f"{API}/payments/pix/webhook", json={"txid": txid},
                       headers={"X-Webhook-Token": settings.PIX_WEBHOOK_SECRET})


async def test_split_creates_one_payment_per_store_with_store_amounts(client, make_privileged_user):
    w, order = await _pix_split(client, make_privileged_user)
    pays = {p["store_id"]: p for p in order["payments"]}
    assert set(pays) == {w["store_a"], w["store_b"]}
    assert pays[w["store_a"]]["amount"] == 10.0
    assert pays[w["store_b"]]["amount"] == 8.0
    assert round(sum(p["amount"] for p in order["payments"]), 2) == order["total"] == 18.0


async def test_each_store_has_its_own_valid_qr(client, make_privileged_user):
    _, order = await _pix_split(client, make_privileged_user)
    codes = [p["pix"]["br_code"] for p in order["payments"]]
    assert len(set(codes)) == 2 and all(pix.verify_payload(c) for c in codes)
    assert len({p["pix"]["txid"] for p in order["payments"]}) == 2
    assert all(p["pix"]["qr_svg"].startswith("<svg") for p in order["payments"])
    assert all(p["status"] == "pending" for p in order["payments"])


async def test_order_placed_only_when_all_stores_paid(client, make_privileged_user):
    w, order = await _pix_split(client, make_privileged_user)
    first, second = [p["pix"]["txid"] for p in order["payments"]]

    assert (await _webhook(client, first)).status_code == 200
    mid = (await client.get(f"{API}/orders/{order['id']}", headers=w["hc"])).json()
    assert mid["status"] == "awaiting_payment"
    assert sorted(p["status"] for p in mid["payments"]) == ["paid", "pending"]

    await _webhook(client, second)
    done = (await client.get(f"{API}/orders/{order['id']}", headers=w["hc"])).json()
    assert done["status"] == "placed"


async def test_paid_store_can_start_before_the_other_pays(client, make_privileged_user):
    w, order = await _pix_split(client, make_privileged_user)
    pay_a = next(p for p in order["payments"] if p["store_id"] == w["store_a"])
    await _webhook(client, pay_a["pix"]["txid"])
    ok = await client.patch(f"{API}/merchant/orders/{order['id']}/status", json={"status": "separating"}, headers=w["ha"])
    blocked = await client.patch(f"{API}/merchant/orders/{order['id']}/status", json={"status": "separating"}, headers=w["hb"])
    assert ok.status_code == 200 and blocked.status_code == 409


async def test_store_own_pix_key_is_used_in_its_qr(client, make_privileged_user):
    w = await split_world(client, make_privileged_user)
    r = await client.patch(f"{API}/merchant/stores/{w['store_a']}", json={"pix_key": "loja-a@pix.com.br"}, headers=w["ha"])
    assert r.status_code == 200 and r.json()["pix_key"] == "loja-a@pix.com.br"
    await fill_cart(client, w["hc"], (w["arroz"], 1), (w["feijao"], 1))
    order = await checkout(client, w["hc"], "pix")
    by_store = {p["store_id"]: p["pix"]["br_code"] for p in order["payments"]}
    assert "loja-a@pix.com.br" in by_store[w["store_a"]]
    assert "loja-a@pix.com.br" not in by_store[w["store_b"]]
    assert settings.PIX_KEY in by_store[w["store_b"]]          # sem chave própria -> chave da plataforma


async def test_merchant_cannot_set_pix_key_of_other_store(client, make_privileged_user):
    w = await split_world(client, make_privileged_user)
    r = await client.patch(f"{API}/merchant/stores/{w['store_b']}", json={"pix_key": "x@y.com"}, headers=w["ha"])
    assert r.status_code == 403


async def test_econopay_pays_every_store_instantly(client, make_privileged_user):
    w = await split_world(client, make_privileged_user)
    await fill_cart(client, w["hc"], (w["arroz"], 1), (w["feijao"], 1))
    order = await checkout(client, w["hc"], "econopay")
    assert order["status"] == "placed"
    assert len(order["payments"]) == 2 and all(p["status"] == "paid" and p["pix"] is None for p in order["payments"])


async def test_single_store_order_has_one_payment(client, make_privileged_user):
    w = await split_world(client, make_privileged_user)
    await fill_cart(client, w["hc"], (w["arroz"], 1), (w["feijao"], 1))
    order = await checkout(client, w["hc"], "pix", strategy="single")
    assert len(order["payments"]) == 1 and order["store_count"] == 1
