import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import AuthShell from "../components/AuthShell.jsx";
import Icon from "../components/Icon.jsx";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ full_name: "", email: "", password: "" });
  const [accept, setAccept] = useState(false);
  const [show, setShow] = useState(false);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setErr("");
    if (!accept) return setErr("É preciso aceitar os Termos e a Política de Privacidade.");
    setBusy(true);
    try {
      await register(form.full_name.trim(), form.email.trim(), form.password);
      navigate("/", { replace: true });
    } catch (ex) {
      if (ex.status === 409) setErr("Já existe uma conta com este e-mail. Tente entrar.");
      else setErr(typeof ex.detail === "string" ? ex.detail : "Não foi possível criar a conta. Confira os dados.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthShell
      title="Criar conta"
      subtitle="Leva menos de 1 minuto"
      footer={<>Já tem conta? <Link to="/login" className="link">Entrar</Link></>}
    >
      {err && <div className="alert err" role="alert">{err}</div>}
      <form onSubmit={submit}>
        <label className="field">
          <span className="lab">Nome completo</span>
          <input value={form.full_name} onChange={set("full_name")} minLength={2} autoComplete="name" required autoFocus />
        </label>
        <label className="field">
          <span className="lab">E-mail</span>
          <input type="email" value={form.email} onChange={set("email")} autoComplete="email" required />
        </label>
        <label className="field">
          <span className="lab">Senha</span>
          <div className="pwwrap">
            <input type={show ? "text" : "password"} value={form.password} onChange={set("password")} minLength={8} autoComplete="new-password" required />
            <button type="button" className="eye" onClick={() => setShow(!show)} aria-label="Mostrar ou ocultar senha">
              <Icon name={show ? "eyeoff" : "eye"} />
            </button>
          </div>
          <span className="unit">Mínimo de 8 caracteres</span>
        </label>
        <label className="spread" style={{ alignItems: "flex-start", margin: "4px 0 16px", fontSize: 13, justifyContent: "flex-start" }}>
          <input type="checkbox" checked={accept} onChange={(e) => setAccept(e.target.checked)} style={{ marginTop: 3 }} />
          <span className="muted">
            Li e aceito os <span className="link">Termos</span> e a <span className="link">Política de Privacidade</span> (uso essencial dos dados — LGPD).
          </span>
        </label>
        <button className="btn" disabled={busy}>{busy ? "Criando…" : "Criar conta"}</button>
      </form>
    </AuthShell>
  );
}
