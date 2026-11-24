import { Logo, Waves } from "./Brand.jsx";
import Icon from "./Icon.jsx";

// Moldura das telas de acesso: painel da marca + cartão branco + ondas.
export default function AuthShell({ title, subtitle, children, footer }) {
  return (
    <div className="auth-shell">
      <div className="auth-hero">
        <Logo size={46} light textSize={26} />
        <p className="tagline">Ecossistema de compras inteligentes. Compare preços e pague menos.</p>
        <ul className="auth-points">
          <li><Icon name="tag" /> Compare preços entre lojas</li>
          <li><Icon name="bolt" /> Noor monta a cesta mais barata</li>
          <li><Icon name="shield" /> Seus dados protegidos (LGPD)</li>
        </ul>
      </div>
      <div className="auth-main">
        <div className="auth-card">
          <h2>{title}</h2>
          {subtitle && <p className="sub">{subtitle}</p>}
          {children}
          {footer && <p className="auth-foot">{footer}</p>}
        </div>
        <Waves />
      </div>
    </div>
  );
}
