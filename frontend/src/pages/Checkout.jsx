import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, brl } from "../api/client.js";
import { useCart } from "../context/CartContext.jsx";
import { Loading } from "../components/ui.jsx";
import Icon from "../components/Icon.jsx";

export default function Checkout() {
  const navigate = useNavigate();
  const { setCart, refresh } = useCart();
  const [plan, setPlan] = useState(null);
  const [strategy, setStrategy] = useState("recommended");
  const [method, setMethod] = useState("pix");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => {
    api.optimize().then(setPlan).catch(() => setPlan(null));
  }, []);

  if (!plan) return <Loading />;

  const chosen =
    strategy === "split" ? plan.split : strategy === "single" ? plan.single_store : plan.recommended === "split" ? plan.split : plan.single_store;
  const many = (chosen?.store_count || 0) > 1;

  async function placeOrder() {
    setBusy(true);
    setErr("");
    try {
      const order = await api.checkout(strategy, method);
      setCart(null);
      await refresh();
      navigate(`/pedido/${order.id}`, { replace: true });
    } catch (e) {
      setErr(typeof e.detail === "string" ? e.detail : "Não foi possível finalizar.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <header className="appbar plain">
        <button className="back" onClick={() => navigate(-1)}>← Voltar</button>
        <h1 style={{ marginTop: 6 }}>Checkout</h1>
      </header>
      <main className="content narrow">
        {err && <div className="alert err">{err}</div>}

        <div className="eyebrow">Como comprar</div>
        <div className="chips" style={{ marginTop: 8 }}>
          <span className={`chip ${strategy === "recommended" ? "on" : ""}`} onClick={() => setStrategy("recommended")}>Recomendado</span>
          {plan.single_store && (
            <span className={`chip ${strategy === "single" ? "on" : ""}`} onClick={() => setStrategy("single")}>
              Uma loja · {brl(plan.single_store.total)}
            </span>
          )}
          {plan.split && (
            <span className={`chip ${strategy === "split" ? "on" : ""}`} onClick={() => setStrategy("split")}>
              Split · {brl(plan.split.total)}
            </span>
          )}
        </div>

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

        <div className="eyebrow" style={{ marginTop: 18 }}>Pagamento</div>
        <div className="chips" style={{ marginTop: 8 }}>
          <span className={`chip ${method === "pix" ? "on" : ""}`} onClick={() => setMethod("pix")}>PIX</span>
          <span className={`chip ${method === "econopay" ? "on" : ""}`} onClick={() => setMethod("econopay")}>EconoPay</span>
          <span className={`chip ${method === "card" ? "on" : ""}`} onClick={() => setMethod("card")}>Cartão</span>
        </div>
        {method === "card" && <div className="alert info" style={{ marginTop: 10 }}>Cartão ainda não disponível — use PIX ou EconoPay.</div>}
        {many && method === "pix" && (
          <div className="alert info" style={{ marginTop: 10 }}>
            <Icon name="store" size={15} /> Cada loja recebe direto: você terá <b>{chosen.store_count} códigos PIX</b>, um para cada loja.
          </div>
        )}

        <div className="card summary" style={{ padding: 14, marginTop: 16 }}>
          <div className="row tot" style={{ border: 0, margin: 0, padding: 0 }}>
            <span>Total</span>
            <span>{brl(chosen?.total)}</span>
          </div>
        </div>

        <div style={{ height: 14 }} />
        <button className="btn" onClick={placeOrder} disabled={busy || method === "card" || !chosen}>
          {busy ? "Finalizando…" : "Confirmar pedido"}
        </button>
      </main>
    </>
  );
}
