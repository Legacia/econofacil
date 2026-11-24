"""RN-020 — receitas: escala de porções e conversão em carrinho."""
from app.models.recipe import Recipe, RecipeIngredient
from app.services.recipe_service import scale_quantity
from tests.helpers import API, consumer, merchant, new_product, new_store, offer


def test_scale_quantity_rounds_up_with_minimum_one():
    assert scale_quantity(1, 4, 4) == 1
    assert scale_quantity(1, 4, 8) == 2
    assert scale_quantity(1, 4, 9) == 3          # 2.25 -> 3
    assert scale_quantity(0.5, 4, 4) == 1        # 0.5 -> mínimo 1
    assert scale_quantity(0.25, 4, 1) == 1


async def _recipe_world(client, make_privileged_user, db):
    hm = await merchant(client, make_privileged_user, "rec@ef.com")
    store = await new_store(client, hm, "rec")
    massa = await new_product(client, hm, "Macarrão", 500, "g")
    molho = await new_product(client, hm, "Molho", 340, "g")
    sumido = await new_product(client, hm, "Ingrediente raro", 1, "kg")      # sem oferta
    await offer(client, hm, store, massa, 4.0)
    await offer(client, hm, store, molho, 3.0)
    r = Recipe(title="Macarrão ao sugo", emoji="🍝", base_servings=4, prep_minutes=20, steps="Cozinhe\nMisture")
    db.add(r)
    await db.flush()
    import uuid
    for pid, qty in ((massa, 1), (molho, 2), (sumido, 1)):
        db.add(RecipeIngredient(recipe_id=r.id, product_id=uuid.UUID(pid), quantity=qty))
    await db.commit()
    return r.id, dict(massa=massa, molho=molho, sumido=sumido)


async def test_list_recipes_with_estimated_cost(client, make_privileged_user, db):
    await _recipe_world(client, make_privileged_user, db)
    rows = (await client.get(f"{API}/recipes")).json()
    assert len(rows) == 1 and rows[0]["title"] == "Macarrão ao sugo"
    assert rows[0]["ingredient_count"] == 3
    assert rows[0]["estimated_cost"] == 10.0          # 1×4 + 2×3 (o ingrediente sem oferta não entra)


async def test_detail_scales_servings(client, make_privileged_user, db):
    rid, ids = await _recipe_world(client, make_privileged_user, db)
    base = (await client.get(f"{API}/recipes/{rid}")).json()
    assert base["servings"] == 4 and base["steps"] == ["Cozinhe", "Misture"]
    big = (await client.get(f"{API}/recipes/{rid}?servings=8")).json()
    qty = {i["product_id"]: i["quantity"] for i in big["ingredients"]}
    assert qty[ids["massa"]] == 2 and qty[ids["molho"]] == 4
    assert big["estimated_cost"] == 20.0 and big["cost_per_serving"] == 2.5


async def test_unavailable_ingredient_is_flagged(client, make_privileged_user, db):
    rid, ids = await _recipe_world(client, make_privileged_user, db)
    det = (await client.get(f"{API}/recipes/{rid}")).json()
    raro = next(i for i in det["ingredients"] if i["product_id"] == ids["sumido"])
    assert raro["available"] is False and raro["best_price"] is None


async def test_add_to_cart_scales_and_requires_login(client, make_privileged_user, db):
    rid, ids = await _recipe_world(client, make_privileged_user, db)
    assert (await client.post(f"{API}/recipes/{rid}/add-to-cart", json={})).status_code == 401
    hc = await consumer(client)
    cart = (await client.post(f"{API}/recipes/{rid}/add-to-cart", json={"servings": 8}, headers=hc)).json()
    qty = {i["product_id"]: i["quantity"] for i in cart["items"]}
    assert qty[ids["massa"]] == 2 and qty[ids["molho"]] == 4
    # adicionar de novo soma às quantidades já existentes
    cart2 = (await client.post(f"{API}/recipes/{rid}/add-to-cart", json={"servings": 4}, headers=hc)).json()
    assert {i["product_id"]: i["quantity"] for i in cart2["items"]}[ids["massa"]] == 3


async def test_unknown_recipe_and_bad_servings(client, make_privileged_user, db):
    rid, _ = await _recipe_world(client, make_privileged_user, db)
    assert (await client.get(f"{API}/recipes/00000000-0000-0000-0000-000000000000")).status_code == 404
    assert (await client.get(f"{API}/recipes/{rid}?servings=0")).status_code == 422
