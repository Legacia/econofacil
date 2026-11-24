import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api, brl } from "../api/client.js";
import { useAuth } from "../context/AuthContext.jsx";
import { useCart } from "../context/CartContext.jsx";
import { Loading, ErrorMsg } from "../components/ui.jsx";
import Icon from "../components/Icon.jsx";

export default function RecipeDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { refresh } = useCart();
  const [r, setR] = useState(null);
  const [servings, setServings] = useState(null);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.recipe(id, servings).then((d) => {
      setR(d);
      if (servings === null) setServings(d.servings);
    }).catch((e) => setErr(e.detail || "Receita não encontrada"));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, servings]);

  async function addAll() {
    if (!user) return navigate("/login", { state: { from: `/receita/${id}` } });
    setBusy(true);
    setMsg("");
    try {
      await api.recipeToCart(id, servings);
      await refresh();
      setMsg("Ingredientes adicionados ao carrinho ✓");
    } catch (e) {
      setErr(typeof e.detail === "string" ? e.detail : "Não foi possível adicionar.");
    } finally {
      setBusy(false);
    }
  }

  if (err) return <main className="content"><ErrorMsg>{err}</ErrorMsg></main>;
  if (!r) return <Loading />;
  const missing = r.ingredients.filter((i) => !i.available).length;

  return (
    <>
      <header className="appbar plain">
        <button className="back" onClick={() => navigate(-1)}>← Voltar</button>
      </header>
      <main className="content">
        <div className="twocol">
          <div>
            <div className="thumb" style={{ height: 120, fontSize: 56 }}>{r.emoji}</div>
            <h2 style={{ margin: "12px 0 2px" }}>{r.title}</h2>
            {r.description && <p className="muted" style={{ margin: "0 0 8px" }}>{r.description}</p>}
            {r.prep_minutes && <div className="unit"><Icon name="clock" size={13} /> {r.prep_minutes} minutos</div>}

            <div className="sectitle">Modo de preparo</div>
            <div className="card" style={{ padding: "6px 16px" }}>
              {r.steps.map((s, i) => (
                <div key={i} className="menu-row" style={{ alignItems: "flex-start" }}>
                  <b style={{ color: "var(--verde)", fontFamily: "var(--disp)" }}>{i + 1}</b>
                  <span style={{ flex: 1, fontSize: 14 }}>{s}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="side">
            <div className="spread">
              <div className="eyebrow">Porções</div>
              <div className="stepper">
                <button onClick={() => setServings(Math.max(1, servings - 1))} aria-label="Menos"><Icon name="minus" size={16} /></button>
                <b>{servings}</b>
                <button onClick={() => setServings(Math.min(100, servings + 1))} aria-label="Mais"><Icon name="plus" size={16} /></button>
              </div>
            </div>

            <div className="card" style={{ padding: "4px 14px", marginTop: 10 }}>
              {r.ingredients.map((i) => (
                <div key={i.product_id} className="store">
                  <span className="nm" style={{ flexDirection: "column", alignItems: "flex-start", gap: 0 }}>
                    <span>{i.quantity}× {i.name}</span>
                    <span className="unit" style={{ fontWeight: 400 }}>{i.package}{i.note ? ` · ${i.note}` : ""}</span>
                  </span>
                  <span className="p">
                    {i.available ? brl(i.line_estimate) : <span style={{ color: "var(--danger)", fontSize: 12 }}>indisponível</span>}
                  </span>
                </div>
              ))}
            </div>

            <div className="card summary" style={{ padding: 14, marginTop: 12 }}>
              <div className="row tot" style={{ border: 0, margin: 0, padding: 0 }}>
                <span>Custo estimado</span><span>{brl(r.estimated_cost)}</span>
              </div>
              <div className="row unit"><span>por porção</span><span>{brl(r.cost_per_serving)}</span></div>
            </div>

            {missing > 0 && <div className="alert warn" style={{ marginTop: 12 }}>{missing} ingrediente(s) sem estoque no momento.</div>}
            {msg && <div className="alert ok" style={{ marginTop: 12 }}>{msg} <button className="link" onClick={() => navigate("/carrinho")}>Ver carrinho</button></div>}
            <div style={{ height: 12 }} />
            <button className="btn" onClick={addAll} disabled={busy}>
              <Icon name="cart" size={18} /> {busy ? "Adicionando…" : "Adicionar ao carrinho"}
            </button>
          </div>
        </div>
      </main>
    </>
  );
}
