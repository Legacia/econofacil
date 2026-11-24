import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client.js";
import { useAuth } from "../context/AuthContext.jsx";
import { Loading } from "../components/ui.jsx";
import Icon from "../components/Icon.jsx";
import { Link } from "react-router-dom";

const PURPOSES = {
  data_processing: "Tratamento essencial de dados",
  marketing: "Comunicações de marketing",
  analytics: "Métricas de uso",
  personalization: "Personalização (Noor)",
};

export default function Profile() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [consents, setConsents] = useState(null);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    api.consents().then(setConsents).catch(() => setConsents([]));
  }, []);

  async function toggle(purpose, granted) {
    const updated = await api.setConsents([{ purpose, granted }]);
    setConsents(updated);
  }

  async function exportData() {
    const data = await api.exportData();
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "meus-dados-econofacil.json";
    a.click();
    URL.revokeObjectURL(url);
    setMsg("Seus dados foram exportados.");
  }

  async function deleteAccount() {
    if (!window.confirm("Excluir sua conta? Seus dados pessoais serão anonimizados (LGPD).")) return;
    await api.deleteAccount();
    await logout();
    navigate("/login", { replace: true });
  }

  if (!user) return <Loading />;
  const has = (p) => consents?.find((c) => c.purpose === p)?.granted ?? (p === "data_processing");

  return (
    <>
      <header className="appbar"><h1>Minha conta</h1></header>
      <main className="content narrow">
        {msg && <div className="alert ok">{msg}</div>}

        <div className="card line" style={{ alignItems: "center" }}>
          <div className="thumb" style={{ width: 46, height: 46, margin: 0, borderRadius: "50%" }}><Icon name="user" size={22} /></div>
          <div>
            <div style={{ fontFamily: "var(--disp)", fontWeight: 700 }}>{user.full_name}</div>
            <div className="unit">{user.email}</div>
          </div>
        </div>

        <div className="card" style={{ background: "var(--grad)", color: "#fff", border: 0, padding: 16, marginTop: 12 }}>
          <div style={{ fontSize: 12, opacity: 0.9 }}>EconoClub</div>
          <div style={{ fontFamily: "var(--disp)", fontWeight: 800, fontSize: 18 }}>Pontos e cashback — em breve</div>
        </div>

        <div className="sectitle">Atalhos</div>
        <div className="card" style={{ padding: "4px 14px" }}>
          <Link to="/listas" className="menu-row"><span className="ic"><Icon name="list" size={18} /></span><span style={{ flex: 1 }}>Minhas listas de compras</span><span>›</span></Link>
          <Link to="/pedidos" className="menu-row"><span className="ic"><Icon name="receipt" size={18} /></span><span style={{ flex: 1 }}>Meus pedidos</span><span>›</span></Link>
          {user.role === "merchant" && <Link to="/lojista" className="menu-row"><span className="ic"><Icon name="store" size={18} /></span><span style={{ flex: 1 }}>Portal do lojista</span><span>›</span></Link>}
          {user.role === "admin" && <Link to="/admin" className="menu-row"><span className="ic"><Icon name="settings" size={18} /></span><span style={{ flex: 1 }}>Painel do administrador</span><span>›</span></Link>}
        </div>

        <div className="sectitle">Privacidade (LGPD)</div>
        <div className="card" style={{ padding: "4px 14px" }}>
          {consents === null ? (
            <p className="muted" style={{ padding: 14 }}>Carregando…</p>
          ) : (
            Object.entries(PURPOSES).map(([p, label]) => (
              <div key={p} className="menu-row">
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600, fontSize: 14 }}>{label}</div>
                  {p === "data_processing" && <div className="unit">Necessário para operar a conta</div>}
                </div>
                <button
                  className={`toggle ${has(p) ? "on" : ""}`}
                  disabled={p === "data_processing"}
                  onClick={() => toggle(p, !has(p))}
                  aria-label={label}
                />
              </div>
            ))
          )}
        </div>

        <div className="sectitle">Meus dados</div>
        <div className="card" style={{ padding: "4px 14px" }}>
          <div className="menu-row" onClick={exportData} style={{ cursor: "pointer" }}>
            <span className="ic"><Icon name="box" size={18} /></span>
            <span style={{ flex: 1 }}>Exportar meus dados (portabilidade)</span>
            <span>›</span>
          </div>
          <div className="menu-row" onClick={deleteAccount} style={{ cursor: "pointer", color: "var(--danger)" }}>
            <span className="ic"><Icon name="x" size={18} /></span>
            <span style={{ flex: 1 }}>Excluir minha conta</span>
            <span>›</span>
          </div>
        </div>

        <div style={{ height: 16 }} />
        <button className="btn ghost" onClick={async () => { await logout(); navigate("/login"); }}>
          Sair
        </button>
      </main>
    </>
  );
}
