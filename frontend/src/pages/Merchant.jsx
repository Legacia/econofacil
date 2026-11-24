import { useCallback, useEffect, useState } from "react";
import { api, brl } from "../api/client.js";
import { Loading, Empty, Tracker, StatusPill, FULF_LABEL } from "../components/ui.jsx";
import Icon from "../components/Icon.jsx";

const NEXT = {
  placed: ["separating", "Iniciar separação"],
  separating: ["on_the_way", "Despachar"],
  on_the_way: ["delivered", "Marcar entregue"],
};

export default function Merchant() {
  const [stores, setStores] = useState(null);
  const [storeId, setStoreId] = useState(null);
  const [tab, setTab] = useState("orders");

  useEffect(() => {
    api.myStores().then((s) => {
      setStores(s);
      if (s.length) setStoreId(s[0].id);
    }).catch(() => setStores([]));
  }, []);

  if (!stores) return <Loading />;
  const store = stores.find((s) => s.id === storeId);

  return (
    <>
      <header className="appbar">
        <h1>Portal do lojista</h1>
        <div className="sub">{store ? store.name : "Gerencie pedidos, estoque e promoções"}</div>
      </header>
      <main className="content">
        {stores.length === 0 ? (
          <Empty emoji="🏪">Nenhuma loja vinculada a esta conta.</Empty>
        ) : (
          <>
            {stores.length > 1 && (
              <div className="chips" style={{ marginBottom: 12 }}>
                {stores.map((s) => (
                  <span key={s.id} className={`chip ${s.id === storeId ? "on" : ""}`} onClick={() => setStoreId(s.id)}>{s.name}</span>
                ))}
              </div>
            )}
            <div className="tabsbar">
              {[["orders", "Pedidos"], ["inventory", "Estoque e preços"], ["promos", "Promoções"], ["report", "Relatório"], ["pix", "Recebimento PIX"]].map(([k, l]) => (
                <button key={k} className={tab === k ? "on" : ""} onClick={() => setTab(k)}>{l}</button>
              ))}
            </div>
            {tab === "orders" && <OrdersTab storeId={storeId} />}
            {tab === "inventory" && <InventoryTab storeId={storeId} />}
            {tab === "promos" && <PromosTab storeId={storeId} />}
            {tab === "report" && <ReportTab storeId={storeId} />}
            {tab === "pix" && <PixTab store={store} onSaved={(s) => setStores(stores.map((x) => (x.id === s.id ? s : x)))} />}
          </>
        )}
      </main>
    </>
  );
}

// ---------------- Pedidos (RN-019: cada loja cuida da sua parte) ----------------
function OrdersTab({ storeId }) {
  const [rows, setRows] = useState(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(null);

  const load = useCallback(() => api.merchantOrders().then(setRows).catch(() => setRows([])), []);
  useEffect(() => {
    load();
    const t = setInterval(load, 8000);
    return () => clearInterval(t);
  }, [load]);

  async function set(row, status) {
    setErr("");
    setBusy(row.order_id + status);
    try {
      await api.setFulfillment(row.order_id, status, row.store_id);
      await load();
    } catch (e) {
      setErr(typeof e.detail === "string" ? e.detail : "Não foi possível atualizar.");
    } finally {
      setBusy(null);
    }
  }

  if (!rows) return <Loading />;
  const mine = rows.filter((r) => r.store_id === storeId);
  if (mine.length === 0) return <Empty emoji="🧾">Nenhum pedido para esta loja ainda.</Empty>;

  return (
    <div className="stack">
      {err && <div className="alert err">{err}</div>}
      {mine.map((r) => {
        const next = NEXT[r.status];
        const closed = ["delivered", "cancelled"].includes(r.status);
        return (
          <div key={r.order_id + r.store_id} className="card storeblock">
            <div className="hd">
              <b>{r.code}</b>
              <span className="price" style={{ fontSize: 15, margin: 0 }}>{brl(r.store_subtotal)}</span>
            </div>
            <div className="unit">{new Date(r.created_at).toLocaleString("pt-BR")} · pedido geral: <StatusPill status={r.order_status} /></div>
            <div style={{ margin: "8px 0", fontSize: 13 }}>
              {r.items.map((i, n) => <div key={n}>{i.quantity}× {i.product_name} <span className="muted">· {brl(i.line_total)}</span></div>)}
            </div>
            <Tracker status={r.status} paid={r.paid} />
            {!closed && (
              <div className="spread" style={{ marginTop: 10, justifyContent: "flex-start", flexWrap: "wrap" }}>
                {next && (
                  <button className="btn sm" disabled={!r.paid || busy === r.order_id + next[0]} onClick={() => set(r, next[0])}>
                    {next[1]}
                  </button>
                )}
                <button className="btn danger sm" disabled={!r.paid && false} onClick={() => window.confirm("Cancelar a entrega desta loja?") && set(r, "cancelled")}>
                  Cancelar entrega
                </button>
                {!r.paid && <span className="unit">Aguardando o pagamento desta loja para começar.</span>}
              </div>
            )}
            {closed && <div className="unit" style={{ marginTop: 6 }}>Situação final: <b>{FULF_LABEL[r.status]}</b></div>}
          </div>
        );
      })}
    </div>
  );
}

// ---------------- Estoque e preços ----------------
function InventoryTab({ storeId }) {
  const [rows, setRows] = useState(null);
  const [edit, setEdit] = useState({});
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");

  const load = useCallback(() => api.inventory(storeId).then(setRows).catch(() => setRows([])), [storeId]);
  useEffect(() => {
    setRows(null);
    load();
  }, [load]);

  async function save(r) {
    const e = edit[r.product_id] || {};
    const price = e.price !== undefined ? Number(String(e.price).replace(",", ".")) : r.price;
    const stock = e.stock !== undefined ? Number(e.stock) : r.stock_quantity;
    setErr("");
    setMsg("");
    try {
      await api.saveOffer(storeId, r.product_id, {
        price, original_price: r.original_price ?? null, in_stock: stock === null || stock > 0, stock_quantity: stock,
      });
      setEdit((cur) => { const n = { ...cur }; delete n[r.product_id]; return n; });
      setMsg(`${r.product_name} atualizado ✓`);
      load();
    } catch (ex) {
      setErr(typeof ex.detail === "string" ? ex.detail : "Verifique os valores informados.");
    }
  }

  if (!rows) return <Loading />;
  const set = (id, k, v) => setEdit({ ...edit, [id]: { ...(edit[id] || {}), [k]: v } });

  return (
    <>
      {msg && <div className="alert ok">{msg}</div>}
      {err && <div className="alert err">{err}</div>}
      <div className="card scroll-x" style={{ padding: 8 }}>
        <table className="tbl">
          <thead><tr><th>Produto</th><th>Preço (R$)</th><th>Estoque</th><th /></tr></thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.product_id}>
                <td>
                  <b>{r.product_name}</b>
                  <div className="unit">{r.package_size} {r.package_unit}{r.original_price ? ` · em promoção (era ${brl(r.original_price)})` : ""}</div>
                </td>
                <td><input inputMode="decimal" defaultValue={r.price.toFixed(2).replace(".", ",")} onChange={(e) => set(r.product_id, "price", e.target.value)} /></td>
                <td><input inputMode="numeric" defaultValue={r.stock_quantity ?? ""} onChange={(e) => set(r.product_id, "stock", e.target.value)} /></td>
                <td><button className="btn alt sm" disabled={!edit[r.product_id]} onClick={() => save(r)}>Salvar</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

// ---------------- Promoções ----------------
function PromosTab({ storeId }) {
  const [promos, setPromos] = useState(null);
  const [inv, setInv] = useState([]);
  const [form, setForm] = useState({ product_id: "", promo_price: "", ends: "" });
  const [err, setErr] = useState("");

  const load = useCallback(() => {
    api.promotions(storeId).then(setPromos).catch(() => setPromos([]));
    api.inventory(storeId).then(setInv).catch(() => {});
  }, [storeId]);
  useEffect(() => { setPromos(null); load(); }, [load]);

  async function create(e) {
    e.preventDefault();
    setErr("");
    try {
      await api.createPromotion(storeId, {
        product_id: form.product_id,
        promo_price: Number(String(form.promo_price).replace(",", ".")),
        ends_at: new Date(form.ends).toISOString(),
      });
      setForm({ product_id: "", promo_price: "", ends: "" });
      load();
    } catch (ex) {
      setErr(typeof ex.detail === "string" ? ex.detail : "Confira os dados (o preço promocional deve ser menor e a data, futura).");
    }
  }
  async function end(p) {
    await api.endPromotion(p.id);
    load();
  }

  const nameOf = (pid) => inv.find((i) => i.product_id === pid)?.product_name || "Produto";
  return (
    <>
      <form className="card" style={{ padding: 14 }} onSubmit={create}>
        <div className="eyebrow" style={{ marginBottom: 10 }}>Nova promoção</div>
        {err && <div className="alert err">{err}</div>}
        <label className="field"><span className="lab">Produto</span>
          <select value={form.product_id} onChange={(e) => setForm({ ...form, product_id: e.target.value })} required>
            <option value="">Selecione…</option>
            {inv.map((i) => <option key={i.product_id} value={i.product_id}>{i.product_name} — {brl(i.price)}</option>)}
          </select>
        </label>
        <label className="field"><span className="lab">Preço promocional (R$)</span>
          <input inputMode="decimal" value={form.promo_price} onChange={(e) => setForm({ ...form, promo_price: e.target.value })} required />
        </label>
        <label className="field"><span className="lab">Termina em</span>
          <input type="datetime-local" value={form.ends} onChange={(e) => setForm({ ...form, ends: e.target.value })} required />
        </label>
        <button className="btn">Criar promoção</button>
      </form>

      <div className="sectitle">Promoções da loja</div>
      {promos === null ? <Loading /> : promos.length === 0 ? <Empty emoji="🏷️">Nenhuma promoção ainda.</Empty> : (
        <div className="stack">
          {promos.map((p) => (
            <div key={p.id} className="card rowcard">
              <div>
                <div style={{ fontWeight: 700 }}>{nameOf(p.product_id)}</div>
                <div className="unit">{brl(p.base_price)} → <b style={{ color: "var(--verde)" }}>{brl(p.promo_price)}</b> · até {new Date(p.ends_at).toLocaleString("pt-BR")}</div>
              </div>
              {p.status === "active" ? <button className="btn danger sm" onClick={() => end(p)}>Encerrar</button> : <span className="stat">Encerrada</span>}
            </div>
          ))}
        </div>
      )}
    </>
  );
}

// ---------------- Relatório ----------------
function ReportTab({ storeId }) {
  const [rep, setRep] = useState(null);
  useEffect(() => {
    setRep(null);
    api.storeReport(storeId).then(setRep).catch(() => setRep({ orders_count: 0, revenue: 0, units_sold: 0, top_products: [] }));
  }, [storeId]);
  if (!rep) return <Loading />;
  return (
    <>
      <div className="kpis">
        <div className="card kpi"><div className="v">{rep.orders_count}</div><div className="l">pedidos</div></div>
        <div className="card kpi"><div className="v">{brl(rep.revenue)}</div><div className="l">vendido</div></div>
        <div className="card kpi"><div className="v">{rep.units_sold}</div><div className="l">unidades</div></div>
      </div>
      <div className="sectitle">Mais vendidos</div>
      {rep.top_products.length === 0 ? <Empty emoji="📊">Sem vendas ainda.</Empty> : (
        <div className="card" style={{ padding: "2px 14px" }}>
          {rep.top_products.map((t) => (
            <div key={t.product_name} className="store"><span className="nm">{t.product_name}</span><span className="p">{t.quantity} un · {brl(t.revenue)}</span></div>
          ))}
        </div>
      )}
    </>
  );
}

// ---------------- Recebimento PIX por loja (RN-022) ----------------
function PixTab({ store, onSaved }) {
  const [key, setKey] = useState(store?.pix_key || "");
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");
  useEffect(() => setKey(store?.pix_key || ""), [store?.id]);
  if (!store) return null;

  async function save(e) {
    e.preventDefault();
    setErr("");
    setMsg("");
    try {
      const s = await api.setStorePix(store.id, key.trim() || null);
      onSaved(s);
      setMsg(s.pix_key ? "Chave PIX salva ✓" : "Chave removida: a plataforma volta a receber por você.");
    } catch (ex) {
      setErr("Chave inválida (sem espaços, até 77 caracteres).");
    }
  }
  return (
    <form className="card" style={{ padding: 14 }} onSubmit={save}>
      <div className="eyebrow" style={{ marginBottom: 6 }}>Chave PIX da loja</div>
      <p className="muted" style={{ fontSize: 13, marginTop: 0 }}>
        Quando o cliente divide a compra entre lojas, cada loja recebe o seu próprio PIX. Com a chave cadastrada, o QR Code leva o dinheiro direto para a sua conta.
        Sem chave, o pagamento usa a chave da plataforma.
      </p>
      {msg && <div className="alert ok">{msg}</div>}
      {err && <div className="alert err">{err}</div>}
      <label className="field"><span className="lab">Chave PIX (e-mail, CPF/CNPJ, telefone ou aleatória)</span>
        <input value={key} onChange={(e) => setKey(e.target.value)} placeholder="ex.: financeiro@minhaloja.com.br" maxLength={77} />
      </label>
      <button className="btn">Salvar chave</button>
    </form>
  );
}
