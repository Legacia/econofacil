import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client.js";
import { Loading } from "../components/ui.jsx";
import Icon from "../components/Icon.jsx";

const LABELS = {
  carts_expired: "Carrinhos expirados",
  promotions_ended: "Promoções encerradas",
  payments_expired: "Cobranças PIX vencidas",
  orders_cancelled: "Pedidos cancelados (PIX não pago)",
};

export default function Admin() {
  const [sched, setSched] = useState(null);
  const [noor, setNoor] = useState(null);
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    api.scheduler().then(setSched).catch(() => setSched({}));
    api.noorStatus().then(setNoor).catch(() => setNoor(null));
  }, []);
  useEffect(() => {
    load();
    const t = setInterval(load, 10000);
    return () => clearInterval(t);
  }, [load]);

  async function run() {
    setBusy(true);
    try {
      setResult(await api.runExpirations());
      load();
    } finally {
      setBusy(false);
    }
  }

  if (!sched) return <Loading />;
  return (
    <>
      <header className="appbar"><h1>Painel do administrador</h1><div className="sub">Agendador, Noor e operações</div></header>
      <main className="content">
        <div className="twocol">
          <div>
            <div className="sectitle" style={{ marginTop: 0 }}>Expirações automáticas</div>
            <div className="card" style={{ padding: 14 }}>
              <div className="spread">
                <span><Icon name="clock" size={16} /> Agendador</span>
                <span className={`stat ${sched.running ? "ok" : "bad"}`}>{sched.running ? "Ativo" : "Parado"}</span>
              </div>
              <div className="unit" style={{ marginTop: 8 }}>
                Roda a cada {sched.interval ?? "—"} s · {sched.runs ?? 0} execuções
                {sched.last_run_at && <> · última: {new Date(sched.last_run_at).toLocaleTimeString("pt-BR")}</>}
              </div>
              {sched.last_result && (
                <div style={{ marginTop: 8, fontSize: 13 }}>
                  {Object.entries(sched.last_result).map(([k, v]) => <div key={k} className="spread"><span className="muted">{LABELS[k] || k}</span><b>{v}</b></div>)}
                </div>
              )}
              <div style={{ height: 12 }} />
              <button className="btn blue" onClick={run} disabled={busy}>{busy ? "Executando…" : "Executar expirações agora"}</button>
              {result && (
                <div className="alert ok" style={{ marginTop: 10 }}>
                  {Object.entries(result).map(([k, v]) => <div key={k}>{LABELS[k] || k}: <b>{v}</b></div>)}
                </div>
              )}
              <p className="unit" style={{ marginTop: 10 }}>
                Carrinhos expiram em 24 h, cobranças PIX conforme o prazo configurado e promoções na data de término. Pedido com PIX vencido é cancelado.
              </p>
            </div>
          </div>

          <div className="side">
            <div className="sectitle" style={{ marginTop: 0 }}>Noor Monitor</div>
            <div className="card" style={{ padding: 14 }}>
              {!noor ? <span className="muted">Indisponível</span> : (
                <>
                  <div className="spread"><span>Motor de otimização</span><b>{noor.engine}</b></div>
                  <div className="spread unit"><span>Versão</span><span>{noor.version}</span></div>
                  <div className="spread unit"><span>Recomendações (V2)</span><span>{noor.recommendations?.version}</span></div>
                  <div className="spread unit"><span>Otimizações feitas</span><span>{noor.metrics?.optimizations ?? 0}</span></div>
                  <div className="spread unit"><span>Economia mínima p/ split</span><span>{(noor.min_split_savings * 100).toFixed(0)}%</span></div>
                  <div className="spread unit"><span>Máximo de lojas</span><span>{noor.max_stores}</span></div>
                </>
              )}
            </div>
          </div>
        </div>
      </main>
    </>
  );
}
