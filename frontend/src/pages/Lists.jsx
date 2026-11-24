import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client.js";
import { Loading, Empty } from "../components/ui.jsx";
import Icon from "../components/Icon.jsx";

export default function Lists() {
  const [lists, setLists] = useState(null);
  const [name, setName] = useState("");
  const [err, setErr] = useState("");

  const load = () => api.lists().then(setLists).catch(() => setLists([]));
  useEffect(() => {
    load();
  }, []);

  async function create(e) {
    e.preventDefault();
    const v = name.trim();
    if (!v) return;
    setErr("");
    try {
      await api.createList(v);
      setName("");
      load();
    } catch (ex) {
      setErr(typeof ex.detail === "string" ? ex.detail : "Não foi possível criar a lista.");
    }
  }

  async function remove(l) {
    if (!window.confirm(`Excluir a lista "${l.name}"?`)) return;
    await api.deleteList(l.id);
    load();
  }

  return (
    <>
      <header className="appbar plain"><h1>Minhas listas</h1><div className="sub muted">Listas permanentes com comparação de preços</div></header>
      <main className="content narrow">
        {err && <div className="alert err">{err}</div>}
        <form className="search" onSubmit={create} style={{ border: "1px solid var(--line)", marginTop: 0 }}>
          <Icon name="plus" size={18} />
          <input placeholder="Nova lista (ex.: Mercado do mês)" value={name} onChange={(e) => setName(e.target.value)} maxLength={120} />
          <button className="btn sm" style={{ width: "auto" }}>Criar</button>
        </form>

        <div style={{ height: 14 }} />
        {lists === null ? (
          <Loading />
        ) : lists.length === 0 ? (
          <Empty emoji="📝">Você ainda não tem listas. Crie a primeira acima.</Empty>
        ) : (
          <div className="stack">
            {lists.map((l) => (
              <div key={l.id} className="card rowcard">
                <Link to={`/listas/${l.id}`} style={{ flex: 1 }}>
                  <div style={{ fontFamily: "var(--disp)", fontWeight: 700 }}>{l.name}</div>
                  <div className="unit">{l.item_count} itens · {l.checked_count} marcados</div>
                </Link>
                <button className="btn danger sm" onClick={() => remove(l)} aria-label="Excluir lista"><Icon name="x" size={16} /></button>
              </div>
            ))}
          </div>
        )}
      </main>
    </>
  );
}
