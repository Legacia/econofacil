import { useEffect, useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { api } from "../api/client.js";
import { useAuth } from "../context/AuthContext.jsx";
import AuthShell from "../components/AuthShell.jsx";
import Icon from "../components/Icon.jsx";

const DEMO_ACCOUNTS = [
  { label: "Cliente", email: "demo@econofacil.com", password: "demo12345", icon: "user" },
  { label: "Lojista", email: "lojista1@econofacil.com", password: "lojista123", icon: "store" },
  { label: "Admin", email: "admin@econofacil.com", password: "admin12345", icon: "settings" },
];

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [otp, setOtp] = useState("");
  const [need2fa, setNeed2fa] = useState(false);
  const [show, setShow] = useState(false);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [demo, setDemo] = useState(false);
  const flash = location.state?.flash;

  useEffect(() => {
    api.isDemo().then(setDemo);
  }, []);

  async function submit(e) {
    e.preventDefault();
    setErr("");
    setBusy(true);
    try {
      const me = await login(email.trim(), password, otp);
      const home = me.role === "admin" ? "/admin" : me.role === "merchant" ? "/lojista" : "/";
      navigate(location.state?.from || home, { replace: true });
    } catch (ex) {
      if (String(ex.detail).includes("2FA")) {
        setNeed2fa(true);
        setErr("Informe o código de 6 dígitos do seu app autenticador (2FA).");
      } else if (ex.status === 429) {
        setErr("Muitas tentativas. Aguarde um pouco e tente de novo.");
      } else if (ex.status === 401 || ex.status === 400) {
        setErr("E-mail ou senha incorretos.");
      } else {
        setErr(typeof ex.detail === "string" ? ex.detail : "Não foi possível entrar. Tente de novo.");
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthShell
      title="Bem-vindo de volta"
      subtitle="Entre para continuar economizando"
      footer={<>Não tem conta? <Link to="/cadastro" className="link">Criar conta</Link></>}
    >
      {flash && <div className="alert ok">{flash}</div>}
      {err && <div className="alert err" role="alert">{err}</div>}

      <form onSubmit={submit}>
        <label className="field">
          <span className="lab">E-mail</span>
          <input type="email" autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="voce@email.com" required autoFocus />
        </label>
        <label className="field">
          <span className="lab">Senha</span>
          <div className="pwwrap">
            <input type={show ? "text" : "password"} autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required />
            <button type="button" className="eye" onClick={() => setShow(!show)} aria-label={show ? "Ocultar senha" : "Mostrar senha"}>
              <Icon name={show ? "eyeoff" : "eye"} />
            </button>
          </div>
        </label>
        {need2fa && (
          <label className="field">
            <span className="lab">Código 2FA</span>
            <input value={otp} onChange={(e) => setOtp(e.target.value.replace(/\D/g, ""))} inputMode="numeric" maxLength={6} placeholder="000000" autoFocus />
          </label>
        )}
        <div style={{ textAlign: "right", marginBottom: 14 }}>
          <Link to="/recuperar-senha" className="link">Esqueci minha senha</Link>
        </div>
        <button className="btn" disabled={busy}>{busy ? "Entrando…" : "Entrar"}</button>
      </form>

      {demo && (
        <div className="demo-box">
          <div className="eyebrow">Modo demonstração · entrar como</div>
          <div className="chips">
            {DEMO_ACCOUNTS.map((a) => (
              <span key={a.label} className="chip" onClick={() => { setEmail(a.email); setPassword(a.password); setErr(""); }}>
                <Icon name={a.icon} size={13} /> {a.label}
              </span>
            ))}
          </div>
          <div className="unit" style={{ marginTop: 6 }}>Toque numa opção para preencher e depois em “Entrar”.</div>
        </div>
      )}
    </AuthShell>
  );
}
