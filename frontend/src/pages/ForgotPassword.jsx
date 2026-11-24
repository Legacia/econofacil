import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api/client.js";
import AuthShell from "../components/AuthShell.jsx";

export default function ForgotPassword() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    try {
      const res = await api.forgotPassword(email.trim());
      // Modo demonstração local: não há e-mail, então o servidor devolve o código na hora.
      if (res?.dev_token) return navigate("/redefinir-senha", { state: { token: res.dev_token } });
    } catch {
      /* a resposta é neutra de propósito (não revela se o e-mail existe) */
    } finally {
      setSent(true);
      setBusy(false);
    }
  }

  return (
    <AuthShell
      title="Recuperar senha"
      subtitle="Informe seu e-mail para redefinir a senha"
      footer={<Link to="/login" className="link">← Voltar para o login</Link>}
    >
      {sent ? (
        <div className="alert ok">
          Se o e-mail existir, enviaremos instruções para redefinir sua senha.
          <div style={{ marginTop: 8 }} className="unit">
            Já tem um código? <Link to="/redefinir-senha" className="link">Informar o código</Link>
          </div>
        </div>
      ) : (
        <form onSubmit={submit}>
          <label className="field">
            <span className="lab">E-mail</span>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoFocus />
          </label>
          <button className="btn" disabled={busy}>{busy ? "Enviando…" : "Enviar instruções"}</button>
        </form>
      )}
    </AuthShell>
  );
}
