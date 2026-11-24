import { useEffect, useRef, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api, brl } from "../api/client.js";
import { Loading, StatusPill, Tracker } from "../components/ui.jsx";
import Icon from "../components/Icon.jsx";

export default function OrderConfirmed() {
  const { id } = useParams();
  const [order, setOrder] = useState(null);
  const [copied, setCopied] = useState(null);
  const [demo, setDemo] = useState(false);
  const [busy, setBusy] = useState(null);
  const timer = useRef(null);

  async function load() {
    setOrder(await api.order(id));
  }
  useEffect(() => {
    load();
    api.isDemo().then(setDemo);
    return () => clearInterval(timer.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  // acompanha o andamento enquanto o pedido não termina (as lojas atualizam por conta própria)
  useEffect(() => {
    clearInterval(timer.current);
    if (order && !["delivered", "cancelled"].includes(order.status)) {
      timer.current = setInterval(() => load().catch(() => {}), 5000);
    }
    return () => clearInterval(timer.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [order?.status]);

  if (!order) return <Loading />;

  const awaiting = order.status === "awaiting_payment";
  const cancelled = order.status === "cancelled";
  const payOf = (storeId) => order.payments.find((p) => p.store_id === storeId);
  const itemsOf = (storeId) => order.items.filter((i) => i.store_id === storeId);

  function copy(p) {
    navigator.clipboard?.writeText(p.pix.br_code);
    setCopied(p.id);
    setTimeout(() => setCopied(null), 2000);
  }
  async function simulate(p) {
    setBusy(p.id);
    try {
      await api.simulatePaid(p.id);
      await load();
    } finally {
      setBusy(null);
    }
  }

  return (
    <>
      <header className="appbar plain">
        <h1>{cancelled ? "Pedido cancelado" : awaiting ? "Pagamento pendente" : "Acompanhe seu pedido"}</h1>
      </header>
      <main className="content narrow">
        <div className="center">
          <div className="bigcheck" style={{ background: cancelled ? "var(--danger)" : awaiting ? "var(--warn)" : "var(--verde)" }}>
            <Icon name={cancelled ? "x" : awaiting ? "clock" : "check"} size={38} stroke={2.6} />
          </div>
          <h2 style={{ margin: "0 0 4px" }}>Pedido {order.code}</h2>
          <StatusPill status={order.status} />
          <div className="unit" style={{ marginTop: 6 }}>
            Total {brl(order.total)} · {order.store_count} {order.store_count === 1 ? "loja" : "lojas"}
          </div>
        </div>

        {order.savings > 0 && (
          <div className="card" style={{ background: "#e7f6ec", border: 0, marginTop: 16, padding: 14, textAlign: "center" }}>
            <div className="unit" style={{ color: "#2e6b45" }}>Você economizou com o split</div>
            <div className="amount" style={{ color: "var(--verde)" }}>{brl(order.savings)}</div>
          </div>
        )}

        {awaiting && order.store_count > 1 && (
          <div className="alert info" style={{ marginTop: 14 }}>
            Cada loja tem o seu PIX. O pedido é confirmado quando <b>todos</b> estiverem pagos, mas cada loja já começa a separar assim que o dela for pago.
          </div>
        )}

        <div style={{ height: 8 }} />
        {order.fulfillments.map((f) => {
          const pay = payOf(f.store_id);
          const paid = pay ? pay.status === "paid" : true;
          return (
            <div key={f.store_id} className="card storeblock">
              <div className="hd">
                <b><Icon name="store" size={16} /> {f.store_name}</b>
                <span className="price" style={{ fontSize: 14, margin: 0 }}>{brl(pay?.amount ?? itemsOf(f.store_id).reduce((a, i) => a + i.line_total, 0))}</span>
              </div>
              <div className="unit" style={{ marginBottom: 6 }}>
                {itemsOf(f.store_id).map((i) => `${i.quantity}× ${i.product_name}`).join(" · ")}
              </div>

              <Tracker status={f.status} paid={paid} />

              {pay?.pix && pay.status === "pending" && (
                <div className="pixbox" style={{ marginTop: 12, boxShadow: "none" }}>
                  <div className="eyebrow">Pague {f.store_name} com PIX</div>
                  <div dangerouslySetInnerHTML={{ __html: pay.pix.qr_svg }} />
                  <div className="copia">{pay.pix.br_code}</div>
                  <button className="btn alt sm" onClick={() => copy(pay)}>{copied === pay.id ? "Copiado ✓" : "Copiar código"}</button>
                  <p className="muted" style={{ fontSize: 12, margin: "10px 0 0" }}>
                    Valor: <b>{brl(pay.amount)}</b>. Após o pagamento, a loja é avisada automaticamente.
                  </p>
                  {demo && (
                    <div style={{ marginTop: 10 }}>
                      <button className="btn sm" disabled={busy === pay.id} onClick={() => simulate(pay)}>
                        {busy === pay.id ? "Confirmando…" : "Simular pagamento (modo demonstração)"}
                      </button>
                      <p className="muted" style={{ fontSize: 11, margin: "6px 0 0" }}>Nenhum dinheiro real é movimentado.</p>
                    </div>
                  )}
                </div>
              )}
              {pay && !pay.pix && <div className="alert ok" style={{ margin: "10px 0 0" }}>Pago via {pay.method === "econopay" ? "EconoPay" : pay.method} — {brl(pay.amount)}</div>}
              {pay?.pix && pay.status === "paid" && <div className="alert ok" style={{ margin: "10px 0 0" }}>PIX confirmado ✓</div>}
              {pay && ["expired", "cancelled"].includes(pay.status) && <div className="alert err" style={{ margin: "10px 0 0" }}>Cobrança {pay.status === "expired" ? "expirada" : "cancelada"}.</div>}
            </div>
          );
        })}

        <div style={{ height: 16 }} />
        <Link to="/pedidos" className="btn block">Meus pedidos</Link>
        <div style={{ height: 10 }} />
        <div className="center"><Link to="/" className="link">Voltar ao início</Link></div>
      </main>
    </>
  );
}
