import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api, brl } from "../api/client.js";
import { useCart } from "../context/CartContext.jsx";
import { Loading, ErrorMsg, NoorTag } from "../components/ui.jsx";
import Icon from "../components/Icon.jsx";

export default function ListDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { refresh } = useCart();
  const [list, setList] = useState(null);
  const [err, setErr] = useState("");
  const [q, setQ] = useState("");
  const [results, setResults] = useState([]);
  const [plan, setPlan] = useState(null);
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);

  const load = () => api.list(id).then(setList).catch((e) => setErr(e.detail || "Lista não encontrada"));
  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function search(e) {
    e.preventDefault();
    if (!q.trim()) return setResults([]);
    const d = await api.products({ q: q.trim(), page_size: 6, sort: "price" });
    setResults(d.items);
  }
  async function wrap(fn) {
    setPlan(null);
    setMsg("");
    try {
      setList(await fn());
    } catch (e) {
      setErr(typeof e.detail === "string" ? e.detail : "Algo deu errado.");
    }
  }
  const addProduct = (p) => wrap(() => api.addListItem(id, p.id, 1)).then(() => { setResults([]); setQ(""); });
  const toggle = (it) => wrap(() => api.updateListItem(id, it.product_id, { checked: !it.checked }));
  const setQty = (it, n) => n >= 1 && wrap(() => api.updateListItem(id, it.product_id, { quantity: n }));
  const remove = (it) => wrap(() => api.removeListItem(id, it.product_id));

  async function compare() {
    setErr("");
    setBusy(true);
    try {
      setPlan(await api.compareList(id));
    } catch (e) {
      setErr(typeof e.detail === "string" ? e.detail : "Não foi possível comparar.");
    } finally {
      setBusy(false);
    }
  }
  async function toCart() {
    setBusy(true);
    try {
      await api.listToCart(id);
      await refresh();
      setMsg("Itens pendentes enviados ao carrinho ✓");
    } catch (e) {
      setErr(typeof e.detail === "string" ? e.detail : "Não foi possível enviar ao carrinho.");
    } finally {
      setBusy(false);
    }
  }

  if (err && !list) return <main className="content"><ErrorMsg>{err}</ErrorMsg></main>;
  if (!list) return <Loading />;
  const chosen = plan ? (plan.recommended === "split" ? plan.split : plan.single_store) : null;
  const pending = list.items.filter((i) => !i.checked).length;

  return (
    <>
      <header className="appbar plain">
        <button className="back" onClick={() => navigate("/listas")}>← Listas</button>
        <h1 style={{ marginTop: 6 }}>{list.name}</h1>
        <div className="sub muted">{list.item_count} itens · {list.checked_count} marcados</div>
      </header>
      <main className="content">
        <div className="twocol">
          <div>
            {err && <div className="alert err" onClick={() => setErr("")}>{err}</div>}
            <form className="search" onSubmit={search} style={{ border: "1px solid var(--line)", marginTop: 0 }}>
              <Icon name="search" size={18} />
              <input placeholder="Buscar produto para adicionar…" value={q} onChange={(e) => setQ(e.target.value)} />
            </form>
            {results.length > 0 && (
              <div className="card" style={{ padding: "2px 14px", marginTop: 8 }}>
                {results.map((p) => (
                  <div key={p.id} className="store">
                    <span className="nm">{p.name} <span className="unit">{p.package_size} {p.package_unit}</span></span>
                    <button className="btn alt sm" onClick={() => addProduct(p)}>+ Adicionar</button>
                  </div>
                ))}
              </div>
            )}

            <div style={{ height: 12 }} />
            {list.items.length === 0 ? (
              <div className="empty"><div className="em">📝</div><p>Lista vazia. Busque produtos acima para adicionar.</p></div>
            ) : (
              <div className="card" style={{ padding: "4px 14px" }}>
                {list.items.map((it) => (
                  <div key={it.product_id} className="menu-row">
                    <button className={`checkbox ${it.checked ? "on" : ""}`} onClick={() => toggle(it)} aria-label="Marcar como comprado">
                      {it.checked && <Icon name="check" size={14} stroke={3} />}
                    </button>
                    <div style={{ flex: 1, opacity: it.checked ? 0.5 : 1, textDecoration: it.checked ? "line-through" : "none" }}>
                      <div style={{ fontWeight: 600, fontSize: 14 }}>{it.name}</div>
                      <div className="unit">{it.package}{it.best_price != null ? ` · ${brl(it.best_price)}` : " · indisponível"}</div>
                    </div>
                    <div className="qty">
                      <button onClick={() => setQty(it, it.quantity - 1)} aria-label="Diminuir"><Icon name="minus" size={15} /></button>
                      <b>{it.quantity}</b>
                      <button onClick={() => setQty(it, it.quantity + 1)} aria-label="Aumentar"><Icon name="plus" size={15} /></button>
                    </div>
                    <button className="back" onClick={() => remove(it)} aria-label="Remover"><Icon name="x" size={16} /></button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="side">
            <div className="card summary" style={{ padding: 14 }}>
              <div className="row tot" style={{ border: 0, margin: 0, padding: 0 }}>
                <span>Estimativa (pendentes)</span><span>{brl(list.estimated_total)}</span>
              </div>
            </div>
            <div style={{ height: 10 }} />
            <button className="btn blue" onClick={compare} disabled={busy || pending === 0}>
              <Icon name="bolt" size={18} /> Comparar a lista inteira
            </button>
            <div style={{ height: 8 }} />
            <button className="btn alt" onClick={toCart} disabled={busy || pending === 0}>
              <Icon name="cart" size={18} /> Enviar pendentes ao carrinho
            </button>
            {msg && <div className="alert ok" style={{ marginTop: 10 }}>{msg} <button className="link" onClick={() => navigate("/carrinho")}>Ver carrinho</button></div>}

            {plan && (
              <div style={{ marginTop: 14 }}>
                <div className="sectitle" style={{ marginTop: 0 }}><span>Melhor compra <NoorTag /></span></div>
                {!plan.fulfillable ? (
                  <div className="alert warn">Alguns itens não podem ser atendidos em até 3 lojas.</div>
                ) : (
                  <>
                    {plan.recommended === "split" && plan.split && (
                      <div className="split" style={{ marginTop: 0 }}>
                        <div className="h"><span>Split · {plan.split.store_count} lojas</span><span>−{brl(plan.savings)}</span></div>
                      </div>
                    )}
                    <div className="card" style={{ padding: "6px 14px" }}>
                      {chosen?.stores.map((s) => (
                        <div key={s.store_id} style={{ padding: "8px 0", borderBottom: "1px solid var(--line)" }}>
                          <div className="spread"><b style={{ fontFamily: "var(--disp)" }}>{s.store_name}</b><b>{brl(s.subtotal)}</b></div>
                          <div className="unit">{s.items.map((i) => `${i.quantity}× ${i.product_name}`).join(" · ")}</div>
                        </div>
                      ))}
                      <div className="spread" style={{ padding: "10px 0 4px" }}><b>Total</b><b className="price" style={{ margin: 0 }}>{brl(chosen?.total)}</b></div>
                    </div>
                    {plan.single_store && plan.recommended === "split" && (
                      <div className="unit" style={{ marginTop: 6 }}>Em uma só loja: {brl(plan.single_store.total)}</div>
                    )}
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      </main>
    </>
  );
}
