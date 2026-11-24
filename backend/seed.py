"""Popula o banco com dados de demonstração do EconoFácil.

Uso (com o ambiente do backend ativo e o DATABASE_URL configurado):

    python seed.py

Cria: admin, 3 lojas (cada uma com seu lojista), categorias, produtos com ofertas em
preços variados (comparação RN-001 e split RN-018), receitas (RN-020) e um cliente de
demonstração com histórico de pedidos (alimenta as recomendações da Noor V2, RN-023).
É seguro rodar mais de uma vez; se o admin já existir, sai sem alterar nada.
"""
import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.database import AsyncSessionLocal, engine
from app.models import (
    Base, FulfillmentStatus, Order, OrderFulfillment, OrderItem, OrderStatus,
    Payment, PaymentMethod, PaymentStatus, Recipe, RecipeIngredient,
)
from app.models.user import UserRole
from app.services import catalog_service, user_service

ADMIN = {"email": "admin@econofacil.com", "full_name": "Admin EconoFácil", "password": "admin12345"}
DEMO = {"email": "demo@econofacil.com", "full_name": "Cliente Demo", "password": "demo12345"}
MERCHANT_PASSWORD = "lojista123"

CATEGORIES = [
    ("Hortifruti", "hortifruti"),
    ("Mercearia", "mercearia"),
    ("Bebidas", "bebidas"),
    ("Limpeza", "limpeza"),
]

# (nome, slug, e-mail do lojista, chave Pix própria da loja — opcional, RN-022)
STORES = [
    ("Mercado Bom Preço", "bom-preco", "lojista1@econofacil.com", None),
    ("SuperEconomia", "supereconomia", "lojista2@econofacil.com", "pix@supereconomia.com.br"),
    ("Hiper Central", "hiper-central", "lojista3@econofacil.com", None),
]

# produto: (nome, tamanho, unidade, categoria_slug, [preço em A, B, C] — None = não vende)
PRODUCTS = [
    ("Tomate Italiano", 1, "kg", "hortifruti", [5.49, 6.20, 5.90]),
    ("Banana Prata", 1, "kg", "hortifruti", [4.19, 3.99, 4.50]),
    ("Cebola", 1, "kg", "hortifruti", [4.99, 5.40, 4.70]),
    ("Arroz Branco", 5, "kg", "mercearia", [24.90, 22.50, 26.00]),
    ("Feijão Carioca", 1, "kg", "mercearia", [8.90, 7.20, 8.10]),
    ("Macarrão Espaguete", 500, "g", "mercearia", [4.20, 4.80, 3.99]),
    ("Molho de Tomate", 340, "g", "mercearia", [2.99, 3.40, 2.79]),
    ("Queijo Ralado", 100, "g", "mercearia", [5.90, 5.50, 6.30]),
    ("Óleo de Soja", 900, "ml", "mercearia", [6.99, 7.40, 6.50]),
    ("Azeite de Oliva", 500, "ml", "mercearia", [32.90, 29.90, 34.50]),
    ("Açúcar Refinado", 1, "kg", "mercearia", [4.69, 4.40, 4.99]),
    ("Farinha de Trigo", 1, "kg", "mercearia", [5.20, 4.90, 5.60]),
    ("Ovos (dúzia)", 12, "un", "mercearia", [11.90, 12.90, 10.99]),
    ("Café Torrado", 500, "g", "mercearia", [17.90, 16.50, 18.90]),
    ("Leite Integral", 1, "l", "bebidas", [4.29, 4.59, 4.89]),
    ("Suco de Laranja", 1, "l", "bebidas", [8.90, 7.90, 9.20]),
    ("Água Mineral", 1.5, "l", "bebidas", [2.49, 2.29, 2.69]),
    ("Detergente Neutro", 500, "ml", "limpeza", [2.49, 2.79, 2.29]),
    ("Sabão em Pó", 1, "kg", "limpeza", [12.90, 11.90, 13.50]),
]

# receita: (título, emoji, descrição, porções, minutos, passos, [(produto, qtd p/ porções-base, observação)])
RECIPES = [
    ("Macarrão ao sugo", "🍝", "Clássico rápido de semana, com molho de tomate e queijo ralado.", 4, 20,
     ["Cozinhe o macarrão em água fervente com sal até ficar al dente.",
      "Aqueça o molho de tomate numa panela com um fio de azeite.",
      "Misture o macarrão ao molho e finalize com queijo ralado."],
     [("Macarrão Espaguete", 1, None), ("Molho de Tomate", 2, None),
      ("Queijo Ralado", 1, "para finalizar"), ("Azeite de Oliva", 0.5, "um fio")]),
    ("Arroz com feijão", "🍚", "A base da mesa brasileira, econômica e completa.", 4, 40,
     ["Deixe o feijão cozinhar na pressão até ficar macio.",
      "Refogue a cebola no óleo e junte o arroz; adicione água e cozinhe.",
      "Tempere o feijão com um refogado de cebola e sirva junto."],
     [("Arroz Branco", 0.5, None), ("Feijão Carioca", 1, None),
      ("Cebola", 1, None), ("Óleo de Soja", 0.5, None)]),
    ("Bolo simples de laranja", "🍰", "Bolo fofinho de liquidificador, ótimo para o café da tarde.", 8, 50,
     ["Bata no liquidificador o suco, os ovos, o óleo e o açúcar.",
      "Misture com a farinha de trigo e coloque o fermento por último.",
      "Asse em forno médio por cerca de 40 minutos."],
     [("Suco de Laranja", 1, None), ("Ovos (dúzia)", 0.5, None), ("Óleo de Soja", 0.5, None),
      ("Açúcar Refinado", 1, None), ("Farinha de Trigo", 1, None)]),
    ("Vitamina de banana", "🥤", "Cremosa, barata e pronta em 5 minutos.", 2, 5,
     ["Bata no liquidificador a banana, o leite e o açúcar.", "Sirva gelada."],
     [("Banana Prata", 0.5, None), ("Leite Integral", 1, None), ("Açúcar Refinado", 0.25, "a gosto")]),
]

# histórico do cliente demo: (dias atrás, [(produto, quantidade)]) — compras recorrentes
DEMO_HISTORY = [
    (45, [("Arroz Branco", 1), ("Feijão Carioca", 2), ("Leite Integral", 4), ("Macarrão Espaguete", 2), ("Molho de Tomate", 3)]),
    (30, [("Arroz Branco", 1), ("Feijão Carioca", 2), ("Leite Integral", 4), ("Café Torrado", 1)]),
    (14, [("Arroz Branco", 1), ("Feijão Carioca", 1), ("Leite Integral", 3), ("Macarrão Espaguete", 1), ("Molho de Tomate", 2), ("Queijo Ralado", 1)]),
]


async def _seed_demo_history(db, demo_user, stores, products, prices):
    """Pedidos já entregues, comprados na SuperEconomia (loja de índice 1)."""
    store = stores[1]
    for days_ago, lines in DEMO_HISTORY:
        when = datetime.now(timezone.utc) - timedelta(days=days_ago)
        items, total = [], 0.0
        for name, qty in lines:
            price = prices[name][1]
            items.append((products[name], qty, price))
            total += round(price * qty, 2)
        total = round(total, 2)
        order = Order(
            user_id=demo_user.id, code=f"EF-D{days_ago:04d}", status=OrderStatus.DELIVERED,
            subtotal=total, savings=0, total=total, store_count=1, created_at=when,
        )
        db.add(order)
        await db.flush()
        for prod, qty, price in items:
            db.add(OrderItem(
                order_id=order.id, store_id=store.id, store_name=store.name,
                product_id=prod.id, product_name=prod.name, quantity=qty,
                unit_price=price, line_total=round(price * qty, 2),
            ))
        db.add(OrderFulfillment(
            order_id=order.id, store_id=store.id, store_name=store.name,
            status=FulfillmentStatus.DELIVERED,
        ))
        db.add(Payment(
            order_id=order.id, store_id=store.id, store_name=store.name, method=PaymentMethod.PIX,
            status=PaymentStatus.PAID, amount=total, provider="mock-pix",
            txid=f"EFD{days_ago:04d}L1", paid_at=when,
        ))
    await db.commit()


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        if await user_service.get_by_email(db, ADMIN["email"]):
            print("Banco já parece populado (admin existe). Nada a fazer.")
            return

        await user_service.create_user(
            db, email=ADMIN["email"], full_name=ADMIN["full_name"],
            password=ADMIN["password"], role=UserRole.ADMIN,
        )
        demo_user = await user_service.create_user(
            db, email=DEMO["email"], full_name=DEMO["full_name"], password=DEMO["password"],
        )

        cats = {}
        for name, slug in CATEGORIES:
            cats[slug] = await catalog_service.create_category(db, name=name, slug=slug)

        stores = []
        for name, slug, email, pix_key in STORES:
            owner = await user_service.create_user(
                db, email=email, full_name=f"Lojista {name}",
                password=MERCHANT_PASSWORD, role=UserRole.MERCHANT,
            )
            store = await catalog_service.create_store(db, name=name, slug=slug, owner_id=owner.id)
            if pix_key:
                store.pix_key = pix_key
                await db.commit()
            stores.append(store)

        products, prices = {}, {}
        for name, size, unit, cat_slug, plist in PRODUCTS:
            product = await catalog_service.create_product(
                db, name=name, package_size=size, package_unit=unit, category_id=cats[cat_slug].id,
            )
            products[name], prices[name] = product, plist
            for store, price in zip(stores, plist):
                if price is None:
                    continue
                await catalog_service.upsert_offer(
                    db, store_id=store.id, product_id=product.id,
                    price=price, original_price=None, in_stock=True, stock_quantity=100,
                )

        for title, emoji, desc, servings, minutes, steps, ings in RECIPES:
            recipe = Recipe(
                title=title, emoji=emoji, description=desc, base_servings=servings,
                prep_minutes=minutes, steps="\n".join(steps),
            )
            db.add(recipe)
            await db.flush()
            for pname, qty, note in ings:
                db.add(RecipeIngredient(
                    recipe_id=recipe.id, product_id=products[pname].id, quantity=qty, note=note,
                ))
        await db.commit()

        await _seed_demo_history(db, demo_user, stores, products, prices)

    print("Seed concluído!")
    print(f"  Admin:      {ADMIN['email']} / {ADMIN['password']}")
    print(f"  Cliente:    {DEMO['email']} / {DEMO['password']}  (com histórico de pedidos)")
    print(f"  Lojistas:   lojista1|2|3@econofacil.com / {MERCHANT_PASSWORD}")
    print(f"  {len(CATEGORIES)} categorias, {len(STORES)} lojas, {len(PRODUCTS)} produtos, {len(RECIPES)} receitas.")


if __name__ == "__main__":
    asyncio.run(main())
