import { Link } from "react-router-dom";
import { brl } from "../api/client.js";
import Icon from "./Icon.jsx";

// Ícone do produto por palavra-chave (o catálogo ainda não tem fotos)
const EMOJI_RULES = [
  [/tomate/, "🍅"], [/banana/, "🍌"], [/cebola/, "🧅"], [/arroz/, "🍚"], [/feij/, "🫘"],
  [/macarr|espaguete/, "🍝"], [/queijo/, "🧀"], [/[oó]leo|azeite/, "🫒"], [/a[cç][uú]car/, "🍬"],
  [/farinha/, "🌾"], [/ovo/, "🥚"], [/caf[eé]/, "☕"], [/leite/, "🥛"], [/suco|laranja/, "🧃"],
  [/[aá]gua/, "💧"], [/detergente|sab[aã]o/, "🧴"], [/p[aã]o/, "🍞"], [/carne|frango/, "🥩"],
];
export const emojiFor = (s = "") => {
  const t = s.toLowerCase();
  const hit = EMOJI_RULES.find(([re]) => re.test(t));
  return hit ? hit[1] : "🛒";
};

export function Loading({ label = "Carregando…" }) {
  return <div className="spinner">{label}</div>;
}

export function ErrorMsg({ children }) {
  return <div className="alert err">{children}</div>;
}

export function Empty({ emoji = "🗂️", children }) {
  return (
    <div className="empty">
      <div className="em">{emoji}</div>
      <p>{children}</p>
    </div>
  );
}

export function ProductCard({ p }) {
  return (
    <Link to={`/produto/${p.id}`} className="card prod">
      <div className="thumb">{emojiFor(p.name)}</div>
      <div className="pname">{p.name}</div>
      <div className="unit">{p.package_size} {p.package_unit}</div>
      <div className="price">
        {brl(p.best_unit_price)}
        <span className="unit"> {p.unit_label}</span>
      </div>
      <div className="storecount">
        {p.store_count} {p.store_count === 1 ? "loja" : "lojas"}
      </div>
    </Link>
  );
}

// ---------- Status de pedido e de cada loja (RN-019) ----------
export const ORDER_LABEL = {
  awaiting_payment: ["Aguardando pagamento", "stat wait"],
  placed: ["Confirmado", "stat ok"],
  separating: ["Separando", "stat go"],
  on_the_way: ["A caminho", "stat tr"],
  delivered: ["Entregue", "stat ok"],
  cancelled: ["Cancelado", "stat bad"],
};
// status de uma loja dentro do pedido
export const FULF_LABEL = {
  placed: "Confirmado",
  separating: "Separando",
  on_the_way: "A caminho",
  delivered: "Entregue",
  cancelled: "Cancelado",
};

export function StatusPill({ status }) {
  const [label, cls] = ORDER_LABEL[status] || [status, "stat"];
  return <span className={cls}>{label}</span>;
}

const STEPS = [
  ["placed", "Confirmado", "check"],
  ["separating", "Separando", "box"],
  ["on_the_way", "A caminho", "truck"],
  ["delivered", "Entregue", "home"],
];

// Linha do tempo de UMA loja
export function Tracker({ status, paid = true }) {
  if (status === "cancelled") return <span className="stat bad">Entrega cancelada</span>;
  if (!paid) return <span className="stat wait">Aguardando pagamento desta loja</span>;
  const idx = STEPS.findIndex(([k]) => k === status);
  return (
    <div className="track">
      {STEPS.map(([k, label, icon], i) => (
        <div key={k} style={{ display: "contents" }}>
          <div className={`st ${i < idx || (i === idx && status === "delivered") ? "done" : i === idx ? "now" : ""}`}>
            <span className="dot"><Icon name={icon} size={13} stroke={2.4} /></span>
            {label}
          </div>
          {i < STEPS.length - 1 && <div className={`bar ${i < idx ? "done" : ""}`} />}
        </div>
      ))}
    </div>
  );
}

// Faixa de recomendações da Noor V2
export function RecoRow({ items, onAdd, busyId }) {
  if (!items || items.length === 0) return null;
  return (
    <div className="reco">
      {items.map((r) => (
        <div key={r.product_id} className="card rc">
          <Link to={`/produto/${r.product_id}`}>
            <div className="thumb" style={{ height: 56, fontSize: 26, marginBottom: 6 }}>{emojiFor(r.name)}</div>
            <div className="pname" style={{ minHeight: "2.2em" }}>{r.name}</div>
          </Link>
          <div className="unit">{r.package}</div>
          <div className="price" style={{ fontSize: 14 }}>{brl(r.best_price)}</div>
          <span className="why">{r.reason}</span>
          {onAdd && (
            <button className="btn alt sm" style={{ marginTop: 6 }} disabled={busyId === r.product_id} onClick={() => onAdd(r)}>
              {busyId === r.product_id ? "…" : "+ Adicionar"}
            </button>
          )}
        </div>
      ))}
    </div>
  );
}

export function NoorTag({ children = "Noor" }) {
  return <span className="noor-tag"><Icon name="bolt" size={11} stroke={2.4} /> {children}</span>;
}
