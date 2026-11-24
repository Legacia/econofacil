import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, brl } from "../api/client.js";
import { useCart } from "../context/CartContext.jsx";
import { Loading, Empty, emojiFor, RecoRow, NoorTag } from "../components/ui.jsx";
import Icon from "../components/Icon.jsx";

export default function Cart() {
  const navigate = useNavigate();
  const { cart, refresh, setQty, add } = useCart();
  const [plan, setPlan] = useState(null);
  const [loadingPlan, setLoadingPlan] = useState(false);
  const [usual, setUsual] = useState([]);
  const [busyId, setBusyId] = useState(null);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function optimize() {
    setLoadingPlan(true);
    try {
      setPlan(await api.optimize());
    } finally {
      setLoadingPlan(false);
    }
  }

  useEffect(() => {
    if (cart && cart.items.length > 0) optimize();
    else setPlan(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cart?.item_count]);

  // Noor V2: itens recorrentes que ainda não estão no carrinho
  useEffect(() => {
    if (!cart) return;
    api.usual(6).then(setUsual).catch(() => setUsual([]));
  }, [cart?.item_count]);

  async function addUsual(r) {
    setBusyId(r.product_id);
    try {
      await add(r.product_id, 1);
    } finally {
      setBusyId(null);
    }
  }

  if (!cart) return <Loading />;

  const expira = cart.expires_at
    ? new Date(cart.expires_at).toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" })
    : null;
  const chosen = plan ? (plan.recommended === "split" ? plan.split : plan.single_store) : null;

  return (
    <>
      <header className="appbar plain">
        <h1>Carrinho</h1>
        {expira && <div className="sub muted">Reservado até {expira}</div>}
      </header>
      <main className="content">
        {cart.items.length === 0 ? (
          <>
            <Empty emoji="🛒">
              Seu carrinho está vazio.
              <br />
              <Link to="/" className="link">Ver ofertas</Link>
            </Empty>
            {usual.length > 0 && (
              <>
                <div className="sectitle"><span>Você costuma comprar <NoorTag /></span></div>
                <RecoRow items={usual} onAdd={addUsual} busyId={busyId} />
              </>
            )}
          </>
        ) : (
          <div className="twocol">
            <div>
              <div className="stack">
                {cart.items.map((it) => (
                  <div key={it.product_id} className="card line">
                    <div className="thumb" style={{ width: 46, height: 46, margin: 0, fontSize: 22 }}>{emojiFor(it.name)}</div>
                    <div style={{ flex: 1 }}>
                      <div className="pname" style={{ minHeight: 0 }}>{it.name}</div>
                      <div className="price" style={{ fontSize: 14 }}>
                        {it.available ? brl(it.best_price * it.quantity) : <span style={{ color: "var(--danger)" }}>indisponível</span>}
                      </div>
                    </div>
                    <div className="qty">
                      <button onClick={() => setQty(it.product_id, it.quantity - 1)} aria-label="Diminuir"><Icon name="minus" size={16} /></button>
                      <b>{it.quantity}</b>
                      <button onClick={() => setQty(it.product_id, it.quantity + 1)} aria-label="Aumentar"><Icon name="plus" size={16} /></button>
                    </div>
                  </div>
                ))}
              </div>

              {usual.length > 0 && (
                <>
                  <div className="sectitle"><span>Você costuma comprar <NoorTag /></span></div>
                  <RecoRow items={usual} onAdd={addUsual} busyId={busyId} />
                </>
              )}
            </div>

            <div className="side">
              {loadingPlan && <div className="spinner">Calculando a melhor compra…</div>}

              {plan && plan.unavailable_items?.length > 0 && (
                <div className="alert info">
                  <b>Itens sem estoque.</b>
                  {plan.unavailable_items.map((u) => (
                    <div key={u.product_id} style={{ marginTop: 6 }}>
                      {u.product_name}
                      {u.suggestions.length > 0 && (
                        <span className="muted"> · substituto: {u.suggestions[0].name} ({brl(u.suggestions[0].price)})</span>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {plan?.split && plan.recommended === "split" && (
                <div className="split" style={{ marginTop: 0 }}>
                  <div className="h">
                    <span><Icon name="bolt" size={16} /> Split sugerido · {plan.split.store_count} lojas</span>
                    <span>−{brl(plan.savings)}</span>
                  </div>
                  <p className="muted" style={{ margin: "6px 0 0", fontSize: 12 }}>
                    Dividindo a compra você economiza {(plan.savings_pct * 100).toFixed(1)}%.
                    Cada loja recebe o seu próprio pagamento e faz a sua própria entrega.
                  </p>
                </div>
              )}

              {chosen && (
                <div className="card" style={{ padding: "6px 14px", marginTop: 12 }}>
                  {chosen.stores.map((s) => (
                    <div key={s.store_id} className="store">
                      <span className="nm">{s.store_name} <span className="muted">({s.items.length} {s.items.length === 1 ? "item" : "itens"})</span></span>
                      <span className="p">{brl(s.subtotal)}</span>
                    </div>
                  ))}
                </div>
              )}

              {plan?.fulfillable && (
                <div className="card summary" style={{ padding: 14, marginTop: 12 }}>
                  {plan.single_store && (
                    <div className="row"><span>Em uma loja</span><span>{brl(plan.single_store.total)}</span></div>
                  )}
                  {plan.split && (
                    <div className="row" style={{ color: "var(--verde)" }}>
                      <span>Com split ({plan.split.store_count} lojas)</span><span>{brl(plan.split.total)}</span>
                    </div>
                  )}
                  <div className="row tot"><span>A pagar</span><span>{brl(chosen?.total)}</span></div>
                </div>
              )}

              <div style={{ height: 14 }} />
              <button className="btn" onClick={() => navigate("/checkout")} disabled={!plan?.fulfillable}>
                Ir para o checkout
              </button>
            </div>
          </div>
        )}
      </main>
    </>
  );
}
