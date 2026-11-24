import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api, brl } from "../api/client.js";
import { useAuth } from "../context/AuthContext.jsx";
import { useCart } from "../context/CartContext.jsx";
import { Loading, ErrorMsg, emojiFor, RecoRow, NoorTag } from "../components/ui.jsx";
import Icon from "../components/Icon.jsx";

const PINS = ["🟢", "🔵", "🟣", "🟠"];

export default function Product() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { add } = useCart();
  const [p, setP] = useState(null);
  const [also, setAlso] = useState([]);
  const [err, setErr] = useState("");
  const [added, setAdded] = useState(false);
  const [busy, setBusy] = useState(false);
  const [busyId, setBusyId] = useState(null);

  useEffect(() => {
    setP(null);
    setErr("");
    api.product(id).then(setP).catch((e) => setErr(e.detail || "Erro"));
    // Noor V2 (RN-023): quem comprou este também comprou
    api.alsoBought(id, 6).then(setAlso).catch(() => setAlso([]));
  }, [id]);

  async function addToCart() {
    if (!user) return navigate("/login", { state: { from: `/produto/${id}` } });
    setBusy(true);
    try {
      await add(id, 1);
      setAdded(true);
      setTimeout(() => setAdded(false), 2000);
    } catch (e) {
      setErr(e.detail || "Erro ao adicionar");
    } finally {
      setBusy(false);
    }
  }

  async function addReco(r) {
    if (!user) return navigate("/login", { state: { from: `/produto/${id}` } });
    setBusyId(r.product_id);
    try {
      await add(r.product_id, 1);
    } finally {
      setBusyId(null);
    }
  }

  if (err) return <main className="content"><ErrorMsg>{err}</ErrorMsg></main>;
  if (!p) return <Loading />;

  return (
    <>
      <header className="appbar plain">
        <button className="back" onClick={() => navigate(-1)}>← Voltar</button>
      </header>
      <main className="content">
        <div className="twocol">
          <div>
            <div className="thumb" style={{ height: 150, fontSize: 64 }}>{emojiFor(p.name)}</div>
            <h2 style={{ margin: "14px 0 2px" }}>{p.name}</h2>
            <div className="unit">{p.brand ? `${p.brand} · ` : ""}{p.package_size} {p.package_unit}</div>
            <div className="price" style={{ fontSize: 26, marginTop: 8 }}>
              {brl(p.best_unit_price)}<span className="unit"> {p.unit_label}</span>
            </div>
            {added && <div className="alert ok" style={{ marginTop: 14 }}>Adicionado ao carrinho ✓</div>}
            <div style={{ height: 14 }} />
            <button className="btn" onClick={addToCart} disabled={busy || p.offers.length === 0}>
              <Icon name="cart" size={18} /> {busy ? "Adicionando…" : "Adicionar ao carrinho"}
            </button>
          </div>

          <div className="side">
            <div className="sectitle" style={{ marginTop: 0 }}>Comparação entre lojas</div>
            <div className="card" style={{ padding: "2px 14px" }}>
              {p.offers.length === 0 && <p className="muted" style={{ padding: "14px 0" }}>Sem ofertas disponíveis.</p>}
              {p.offers.map((o, i) => (
                <div key={o.store_id} className={`store ${o.is_best ? "best" : ""}`}>
                  <span className="nm">
                    <span className="pin">{PINS[i % PINS.length]}</span>
                    {o.store_name}
                    {o.is_best && <span className="tag">melhor preço</span>}
                    {!o.in_stock && <span className="tag" style={{ background: "#fdecea", color: "var(--danger)" }}>sem estoque</span>}
                  </span>
                  <span className="p">
                    {brl(o.price)}
                    {o.original_price && <span className="old">{brl(o.original_price)}</span>}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {also.length > 0 && (
          <>
            <div className="sectitle"><span>Quem comprou este também comprou <NoorTag /></span></div>
            <RecoRow items={also} onAdd={addReco} busyId={busyId} />
          </>
        )}
      </main>
    </>
  );
}
