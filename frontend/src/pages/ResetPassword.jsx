import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { api } from "../api/client.js";
import AuthShell from "../components/AuthShell.jsx";

export default function ResetPassword() {
  const navigate = useNavigate();
  const location = useLocation();
  const [token, setToken] = useState(location.state?.token || "");
  const [pw, setPw] = useState("");
  const [pw2, setPw2] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setErr("");
    if (pw !== pw2) return setErr("As senhas não conferem.");
    setBusy(true);
    try {
      await api.resetPassword(token.trim(), pw);
      navigate("/login", { replace: true, state: { flash: "Senha redefinida! Entre com a nova senha." } });
    } catch (ex) {
      setErr(typeof ex.detail === "string" ? ex.detail : "Código inválido ou expirado. Peça um novo.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthShell
      title="Nova senha"
      subtitle="Escolha uma senha nova para sua conta"
      footer={<Link to="/login" className="link">← Voltar para o login</Link>}
    >
      {err && <div className="alert err" role="alert">{err}</div>}
      <form onSubmit={submit}>
        {!location.state?.token && (
          <label className="field">
            <span className="lab">Código recebido</span>
            <input value={token} onChange={(e) => setToken(e.target.value)} required />
          </label>
        )}
        <label className="field">
          <span className="lab">Nova senha</span>
          <input type="password" value={pw} onChange={(e) => setPw(e.target.value)} minLength={8} autoComplete="new-password" required autoFocus />
          <span className="unit">Mínimo de 8 caracteres</span>
        </label>
        <label className="field">
          <span className="lab">Repita a nova senha</span>
          <input type="password" value={pw2} onChange={(e) => setPw2(e.target.value)} minLength={8} autoComplete="new-password" required />
        </label>
        <button className="btn" disabled={busy}>{busy ? "Salvando…" : "Redefinir senha"}</button>
      </form>
    </AuthShell>
  );
}
