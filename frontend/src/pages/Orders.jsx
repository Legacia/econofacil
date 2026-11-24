import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, brl } from "../api/client.js";
import { Loading, Empty, StatusPill, FULF_LABEL } from "../components/ui.jsx";

export default function Orders() {
  const [orders, setOrders] = useState(null);
  useEffect(() => {
    api.orders().then(setOrders).catch(() => setOrders([]));
  }, []);

  if (!orders) return <Loading />;

  return (
    <>
      <header className="appbar plain"><h1>Meus pedidos</h1></header>
      <main className="content narrow">
        {orders.length === 0 ? (
          <Empty emoji="🧾">Você ainda não tem pedidos.</Empty>
        ) : (
          <div className="stack">
            {orders.map((o) => (
              <Link to={`/pedido/${o.id}`} key={o.id} className="card" style={{ display: "block", padding: 14 }}>
                <div className="spread">
                  <div>
                    <div style={{ fontFamily: "var(--disp)", fontWeight: 700 }}>{o.code}</div>
                    <div className="unit">
                      {new Date(o.created_at).toLocaleDateString("pt-BR")} · {o.store_count} {o.store_count === 1 ? "loja" : "lojas"} · {brl(o.total)}
                      {o.savings > 0 && <span style={{ color: "var(--verde)" }}> · −{brl(o.savings)}</span>}
                    </div>
                  </div>
                  <StatusPill status={o.status} />
                </div>
                {o.fulfillments?.length > 1 && o.status !== "awaiting_payment" && (
                  <div style={{ marginTop: 8, borderTop: "1px solid var(--line)", paddingTop: 8 }}>
                    {o.fulfillments.map((f) => (
                      <div key={f.store_id} className="spread unit" style={{ padding: "2px 0" }}>
                        <span>{f.store_name}</span>
                        <b style={{ color: "var(--ink)" }}>{FULF_LABEL[f.status] || f.status}</b>
                      </div>
                    ))}
                  </div>
                )}
              </Link>
            ))}
          </div>
        )}
      </main>
    </>
  );
}
