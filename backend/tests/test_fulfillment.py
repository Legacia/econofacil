"""RN-019 — andamento do pedido por loja; status do pedido = loja mais lenta."""
from tests.helpers import API, checkout, fill_cart, split_world


async def _split_order(client, make_privileged_user, method="econopay"):
    w = await split_world(client, make_privileged_user)
    await fill_cart(client, w["hc"], (w["arroz"], 1), (w["feijao"], 1))
    order = await checkout(client, w["hc"], method)
    return w, order


def _patch(client, h, order_id, status, store_id=None):
    body = {"status": status}
    if store_id:
        body["store_id"] = store_id
    return client.patch(f"{API}/merchant/orders/{order_id}/status", json=body, headers=h)


async def _status(client, w, order_id):
    return (await client.get(f"{API}/orders/{order_id}", headers=w["hc"])).json()


async def test_split_creates_one_fulfillment_per_store(client, make_privileged_user):
    w, order = await _split_order(client, make_privileged_user)
    assert order["store_count"] == 2
    assert len(order["fulfillments"]) == 2
    assert {f["status"] for f in order["fulfillments"]} == {"placed"}
    assert {f["store_id"] for f in order["fulfillments"]} == {w["store_a"], w["store_b"]}


async def test_merchant_cannot_advance_before_store_is_paid(client, make_privileged_user):
    w, order = await _split_order(client, make_privileged_user, method="pix")
    r = await _patch(client, w["ha"], order["id"], "separating")
    assert r.status_code == 409


async def test_order_status_follows_the_slowest_store(client, make_privileged_user):
    w, order = await _split_order(client, make_privileged_user)
    oid = order["id"]
    assert order["status"] == "placed"

    # loja A avança, B ainda não -> pedido continua "placed"
    assert (await _patch(client, w["ha"], oid, "separating")).status_code == 200
    assert (await _status(client, w, oid))["status"] == "placed"

    # B alcança A -> pedido passa a "separating"
    assert (await _patch(client, w["hb"], oid, "separating")).status_code == 200
    assert (await _status(client, w, oid))["status"] == "separating"

    # A entrega tudo; B só a caminho -> pedido "on_the_way"
    await _patch(client, w["ha"], oid, "on_the_way")
    await _patch(client, w["ha"], oid, "delivered")
    await _patch(client, w["hb"], oid, "on_the_way")
    assert (await _status(client, w, oid))["status"] == "on_the_way"

    # B entrega -> pedido "delivered"
    await _patch(client, w["hb"], oid, "delivered")
    final = await _status(client, w, oid)
    assert final["status"] == "delivered"
    assert {f["status"] for f in final["fulfillments"]} == {"delivered"}


async def test_cannot_go_backwards(client, make_privileged_user):
    w, order = await _split_order(client, make_privileged_user)
    await _patch(client, w["ha"], order["id"], "on_the_way")
    r = await _patch(client, w["ha"], order["id"], "separating")
    assert r.status_code == 422


async def test_merchant_only_touches_own_store(client, make_privileged_user):
    w, order = await _split_order(client, make_privileged_user)
    r = await _patch(client, w["ha"], order["id"], "separating", store_id=w["store_b"])
    assert r.status_code == 403
    assert all(f["status"] == "placed" for f in (await _status(client, w, order["id"]))["fulfillments"])


async def test_cancelling_one_store_keeps_the_others(client, make_privileged_user):
    w, order = await _split_order(client, make_privileged_user)
    oid = order["id"]
    await _patch(client, w["ha"], oid, "cancelled")
    await _patch(client, w["hb"], oid, "delivered")
    after = await _status(client, w, oid)
    assert after["status"] == "delivered"            # só a loja B conta
    await_all = {f["store_id"]: f["status"] for f in after["fulfillments"]}
    assert await_all[w["store_a"]] == "cancelled"


async def test_all_stores_cancelled_cancels_the_order(client, make_privileged_user):
    w, order = await _split_order(client, make_privileged_user)
    await _patch(client, w["ha"], order["id"], "cancelled")
    await _patch(client, w["hb"], order["id"], "cancelled")
    assert (await _status(client, w, order["id"]))["status"] == "cancelled"


async def test_merchant_sees_only_own_store_row(client, make_privileged_user):
    w, order = await _split_order(client, make_privileged_user)
    rows = (await client.get(f"{API}/merchant/orders", headers=w["ha"])).json()
    assert len(rows) == 1
    assert rows[0]["store_id"] == w["store_a"] and rows[0]["paid"] is True
    assert rows[0]["store_subtotal"] == 10.0            # só o Arroz da loja A
    assert rows[0]["order_status"] == "placed"
