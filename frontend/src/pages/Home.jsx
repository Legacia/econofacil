import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client.js";
import { useAuth } from "../context/AuthContext.jsx";
import { useCart } from "../context/CartContext.jsx";
import { ProductCard, Loading, Empty, RecoRow, NoorTag } from "../components/ui.jsx";
import { Logo, Waves } from "../components/Brand.jsx";
import Icon from "../components/Icon.jsx";

export default function Home() {
  const { user } = useAuth();
  const { add } = useCart();
  const [categories, setCategories] = useState([]);
  const [products, setProducts] = useState(null);
  const [usual, setUsual] = useState([]);
  const [busyId, setBusyId] = useState(null);
  const [q, setQ] = useState("");
  const [active, setActive] = useState(null);

  async function load(params) {
    setProducts(null);
    try {
      const data = await api.products({ sort: "price", page_size: 24, ...params });
      setProducts(data.items);
    } catch {
      setProducts([]);
    }
  }

  useEffect(() => {
    api.categories().then(setCategories).catch(() => {});
    load();
  }, []);

  // Noor V2 (RN-023): "você costuma comprar"
  useEffect(() => {
    if (!user) return setUsual([]);
    api.usual(8).then(setUsual).catch(() => setUsual([]));
  }, [user]);

  async function addUsual(r) {
    setBusyId(r.product_id);
    try {
      await add(r.product_id, 1);
      setUsual((cur) => cur.filter((x) => x.product_id !== r.product_id));
    } finally {
      setBusyId(null);
    }
  }

  function onSearch(e) {
    e.preventDefault();
    load({ q: q || undefined, category_id: active || undefined });
  }

  function pickCategory(id) {
    const next = active === id ? null : id;
    setActive(next);
    load({ q: q || undefined, category_id: next || undefined });
  }

  return (
    <>
      <header className="appbar">
        <div className="brandrow">
          <Logo size={34} light textSize={20} />
          <div className="loc"><Icon name="pin" size={14} /> {user ? `Olá, ${user.full_name.split(" ")[0]}` : "Entrega · São Paulo, SP"}</div>
        </div>
        <form className="search" onSubmit={onSearch}>
          <Icon name="search" size={18} />
          <input placeholder="Buscar produtos…" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Buscar produtos" />
        </form>
      </header>

      <main className="content">
        <div className="hero">
          <div className="big">Compare, divida e economize</div>
          <div className="cap">A Noor monta a cesta mais barata entre as lojas.</div>
          <span className="spark"><Icon name="cart" size={86} stroke={1.4} /></span>
        </div>

        {usual.length > 0 && (
          <>
            <div className="sectitle">
              <span>Você costuma comprar <NoorTag /></span>
            </div>
            <RecoRow items={usual} onAdd={addUsual} busyId={busyId} />
          </>
        )}

        {categories.length > 0 && (
          <div className="chips" style={{ marginTop: 14 }}>
            <span className={`chip ${!active ? "on" : ""}`} onClick={() => pickCategory(null)}>Tudo</span>
            {categories.map((c) => (
              <span key={c.id} className={`chip ${active === c.id ? "on" : ""}`} onClick={() => pickCategory(c.id)}>
                {c.name}
              </span>
            ))}
          </div>
        )}

        <div className="sectitle">
          Menores preços
          <span style={{ display: "flex", gap: 14 }}>
            <Link to="/receitas">receitas</Link>
            <Link to="/listas">minhas listas</Link>
          </span>
        </div>

        {products === null ? (
          <Loading />
        ) : products.length === 0 ? (
          <Empty emoji="🛒">Nenhum produto encontrado.</Empty>
        ) : (
          <div className="grid">
            {products.map((p) => <ProductCard key={p.id} p={p} />)}
          </div>
        )}

        <div className="footer-waves"><Waves /></div>
      </main>
    </>
  );
}
