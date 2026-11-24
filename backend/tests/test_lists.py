"""RN-020 — listas de compras permanentes, com comparação da lista inteira."""
from tests.helpers import API, consumer, fill_cart, split_world


async def _list(client, hc, name="Mercado do mês"):
    return (await client.post(f"{API}/lists", json={"name": name}, headers=hc)).json()


async def test_create_and_list(client, make_privileged_user):
    w = await split_world(client, make_privileged_user)
    sl = await _list(client, w["hc"])
    assert sl["name"] == "Mercado do mês" and sl["items"] == []
    rows = (await client.get(f"{API}/lists", headers=w["hc"])).json()
    assert [r["name"] for r in rows] == ["Mercado do mês"]


async def test_requires_login(client):
    assert (await client.get(f"{API}/lists")).status_code == 401


async def test_add_item_merges_quantity(client, make_privileged_user):
    w = await split_world(client, make_privileged_user)
    sl = await _list(client, w["hc"])
    await client.post(f"{API}/lists/{sl['id']}/items", json={"product_id": w["arroz"], "quantity": 2}, headers=w["hc"])
    r = await client.post(f"{API}/lists/{sl['id']}/items", json={"product_id": w["arroz"], "quantity": 3}, headers=w["hc"])
    items = r.json()["items"]
    assert len(items) == 1 and items[0]["quantity"] == 5 and items[0]["best_price"] == 10.0


async def test_unknown_product_is_rejected(client, make_privileged_user):
    w = await split_world(client, make_privileged_user)
    sl = await _list(client, w["hc"])
    r = await client.post(f"{API}/lists/{sl['id']}/items",
                          json={"product_id": "00000000-0000-0000-0000-000000000000"}, headers=w["hc"])
    assert r.status_code == 404


async def test_check_update_and_remove_item(client, make_privileged_user):
    w = await split_world(client, make_privileged_user)
    sl = await _list(client, w["hc"])
    await client.post(f"{API}/lists/{sl['id']}/items", json={"product_id": w["arroz"]}, headers=w["hc"])
    r = await client.patch(f"{API}/lists/{sl['id']}/items/{w['arroz']}", json={"checked": True, "quantity": 4}, headers=w["hc"])
    it = r.json()["items"][0]
    assert it["checked"] is True and it["quantity"] == 4 and r.json()["checked_count"] == 1
    assert r.json()["estimated_total"] == 0.0            # marcado = já comprado, não entra no total
    r = await client.delete(f"{API}/lists/{sl['id']}/items/{w['arroz']}", headers=w["hc"])
    assert r.json()["items"] == []


async def test_rename_and_delete(client, make_privileged_user):
    w = await split_world(client, make_privileged_user)
    sl = await _list(client, w["hc"])
    r = await client.patch(f"{API}/lists/{sl['id']}", json={"name": "Churrasco"}, headers=w["hc"])
    assert r.json()["name"] == "Churrasco"
    assert (await client.delete(f"{API}/lists/{sl['id']}", headers=w["hc"])).status_code == 204
    assert (await client.get(f"{API}/lists/{sl['id']}", headers=w["hc"])).status_code == 404


async def test_compare_whole_list_finds_split(client, make_privileged_user):
    w = await split_world(client, make_privileged_user)
    sl = await _list(client, w["hc"])
    for pid in (w["arroz"], w["feijao"]):
        await client.post(f"{API}/lists/{sl['id']}/items", json={"product_id": pid}, headers=w["hc"])
    plan = (await client.get(f"{API}/lists/{sl['id']}/compare", headers=w["hc"])).json()
    assert plan["recommended"] == "split"
    assert plan["split"]["total"] == 18.0 and plan["single_store"]["total"] == 28.0
    assert plan["savings"] == 10.0


async def test_compare_ignores_checked_and_rejects_empty(client, make_privileged_user):
    w = await split_world(client, make_privileged_user)
    sl = await _list(client, w["hc"])
    assert (await client.get(f"{API}/lists/{sl['id']}/compare", headers=w["hc"])).status_code == 400
    await client.post(f"{API}/lists/{sl['id']}/items", json={"product_id": w["arroz"]}, headers=w["hc"])
    await client.patch(f"{API}/lists/{sl['id']}/items/{w['arroz']}", json={"checked": True}, headers=w["hc"])
    assert (await client.get(f"{API}/lists/{sl['id']}/compare", headers=w["hc"])).status_code == 400


async def test_to_cart_adds_only_pending_items(client, make_privileged_user):
    w = await split_world(client, make_privileged_user)
    sl = await _list(client, w["hc"])
    await client.post(f"{API}/lists/{sl['id']}/items", json={"product_id": w["arroz"], "quantity": 2}, headers=w["hc"])
    await client.post(f"{API}/lists/{sl['id']}/items", json={"product_id": w["feijao"]}, headers=w["hc"])
    await client.patch(f"{API}/lists/{sl['id']}/items/{w['feijao']}", json={"checked": True}, headers=w["hc"])
    cart = (await client.post(f"{API}/lists/{sl['id']}/to-cart", headers=w["hc"])).json()
    assert [(i["product_id"], i["quantity"]) for i in cart["items"]] == [(w["arroz"], 2)]


async def test_lists_are_private_to_owner(client, make_privileged_user):
    w = await split_world(client, make_privileged_user)
    sl = await _list(client, w["hc"])
    other = await consumer(client, "outro@ef.com")
    for method, url in (("get", ""), ("patch", ""), ("delete", ""), ("get", "/compare"), ("post", "/to-cart")):
        kw = {"json": {"name": "x"}} if method == "patch" else {}
        r = await getattr(client, method)(f"{API}/lists/{sl['id']}{url}", headers=other, **kw)
        assert r.status_code == 404, (method, url)
    assert (await client.get(f"{API}/lists", headers=other)).json() == []
