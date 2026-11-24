"""RN-021 — expirações centralizadas (carrinho, promoções, cobranças Pix)."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.models.cart import Cart, CartStatus
from app.models.catalog import StoreProduct
from app.models.order import FulfillmentStatus, Order, OrderStatus
from app.models.payment import Payment, PaymentStatus
from app.models.promotion import Promotion, PromotionStatus
from app.services import expiration_service
from tests.helpers import API, admin, checkout, consumer, fill_cart, split_world

PAST = datetime.now(timezone.utc) - timedelta(hours=2)


async def test_expired_cart_is_closed(client, make_privileged_user, db):
    w = await split_world(client, make_privileged_user)
    await fill_cart(client, w["hc"], (w["arroz"], 1))
    cart = (await db.execute(select(Cart))).scalars().first()
    cart.expires_at = PAST
    await db.commit()
    res = await expiration_service.run_expirations(db)
    assert res["carts_expired"] == 1
    await db.refresh(cart)
    assert cart.status == CartStatus.EXPIRED


async def test_active_cart_is_untouched(client, make_privileged_user, db):
    w = await split_world(client, make_privileged_user)
    await fill_cart(client, w["hc"], (w["arroz"], 1))
    assert (await expiration_service.run_expirations(db))["carts_expired"] == 0


async def test_ended_promotion_restores_price(client, make_privileged_user, db):
    w = await split_world(client, make_privileged_user)
    promo = await client.post(
        f"{API}/merchant/stores/{w['store_a']}/promotions",
        json={"product_id": w["arroz"], "promo_price": 7.0,
              "ends_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()},
        headers=w["ha"],
    )
    assert promo.status_code == 201
    p = (await db.execute(select(Promotion))).scalars().first()
    p.ends_at = PAST
    await db.commit()

    res = await expiration_service.run_expirations(db)
    assert res["promotions_ended"] == 1
    offer = (await db.execute(
        select(StoreProduct).where(StoreProduct.store_id == p.store_id, StoreProduct.product_id == p.product_id)
    )).scalar_one()
    await db.refresh(offer)
    assert float(offer.price) == 10.0 and offer.original_price is None
    await db.refresh(p)
    assert p.status == PromotionStatus.ENDED


async def _pix_order(client, make_privileged_user):
    w = await split_world(client, make_privileged_user)
    await fill_cart(client, w["hc"], (w["arroz"], 1), (w["feijao"], 1))
    return w, await checkout(client, w["hc"], "pix")


async def test_expired_pix_cancels_the_order(client, make_privileged_user, db):
    w, order = await _pix_order(client, make_privileged_user)
    for pay in (await db.execute(select(Payment))).scalars().all():
        pay.expires_at = PAST
    await db.commit()

    res = await expiration_service.run_expirations(db)
    assert res["payments_expired"] == 2 and res["orders_cancelled"] == 1
    got = (await client.get(f"{API}/orders/{order['id']}", headers=w["hc"])).json()
    assert got["status"] == "cancelled"
    assert {f["status"] for f in got["fulfillments"]} == {"cancelled"}
    assert {p["status"] for p in got["payments"]} == {"expired"}


async def test_partially_paid_order_cancels_and_leaves_paid_payment(client, make_privileged_user, db):
    w, order = await _pix_order(client, make_privileged_user)
    pays = (await db.execute(select(Payment).order_by(Payment.store_name))).scalars().all()
    pays[0].status = PaymentStatus.PAID                     # loja A já pagou
    pays[1].expires_at = PAST                               # loja B venceu
    await db.commit()

    await expiration_service.run_expirations(db)
    got = (await client.get(f"{API}/orders/{order['id']}", headers=w["hc"])).json()
    assert got["status"] == "cancelled"
    assert sorted(p["status"] for p in got["payments"]) == ["expired", "paid"]   # o pago NÃO é apagado


async def test_paid_orders_never_expire(client, make_privileged_user, db):
    w = await split_world(client, make_privileged_user)
    await fill_cart(client, w["hc"], (w["arroz"], 1), (w["feijao"], 1))
    order = await checkout(client, w["hc"], "econopay")
    res = await expiration_service.run_expirations(db)
    assert res["orders_cancelled"] == 0 and res["payments_expired"] == 0
    assert (await client.get(f"{API}/orders/{order['id']}", headers=w["hc"])).json()["status"] == "placed"


async def test_run_is_idempotent(client, make_privileged_user, db):
    await _pix_order(client, make_privileged_user)
    for pay in (await db.execute(select(Payment))).scalars().all():
        pay.expires_at = PAST
    await db.commit()
    first = await expiration_service.run_expirations(db)
    second = await expiration_service.run_expirations(db)
    assert first["orders_cancelled"] == 1
    assert second == {"carts_expired": 0, "promotions_ended": 0, "payments_expired": 0, "orders_cancelled": 0}


async def test_admin_endpoint_is_admin_only(client, make_privileged_user):
    assert (await client.post(f"{API}/admin/expirations/run")).status_code == 401
    hc = await consumer(client)
    assert (await client.post(f"{API}/admin/expirations/run", headers=hc)).status_code == 403
    ha = await admin(client, make_privileged_user)
    ok = await client.post(f"{API}/admin/expirations/run", headers=ha)
    assert ok.status_code == 200
    assert set(ok.json()) == {"carts_expired", "promotions_ended", "payments_expired", "orders_cancelled"}


async def test_scheduler_status_endpoint(client, make_privileged_user):
    ha = await admin(client, make_privileged_user)
    r = await client.get(f"{API}/admin/scheduler", headers=ha)
    assert r.status_code == 200 and {"running", "interval", "runs"} <= set(r.json())
