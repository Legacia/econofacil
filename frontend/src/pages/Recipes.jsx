import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, brl } from "../api/client.js";
import { Loading, Empty } from "../components/ui.jsx";
import Icon from "../components/Icon.jsx";

export default function Recipes() {
  const [recipes, setRecipes] = useState(null);
  useEffect(() => {
    api.recipes().then(setRecipes).catch(() => setRecipes([]));
  }, []);

  return (
    <>
      <header className="appbar"><h1>Receitas</h1><div className="sub">Cozinhe gastando menos</div></header>
      <main className="content">
        {recipes === null ? (
          <Loading />
        ) : recipes.length === 0 ? (
          <Empty emoji="🍳">Nenhuma receita cadastrada ainda.</Empty>
        ) : (
          <div className="grid">
            {recipes.map((r) => (
              <Link key={r.id} to={`/receita/${r.id}`} className="card recipe prod" style={{ padding: 0 }}>
                <div className="img">{r.emoji}</div>
                <div style={{ padding: 14 }}>
                  <div style={{ fontFamily: "var(--disp)", fontWeight: 700 }}>{r.title}</div>
                  <div className="unit" style={{ margin: "4px 0 8px" }}>
                    {r.ingredient_count} ingredientes · {r.base_servings} porções
                    {r.prep_minutes ? ` · ${r.prep_minutes} min` : ""}
                  </div>
                  <div className="price" style={{ fontSize: 15 }}>
                    {brl(r.estimated_cost)} <span className="unit">custo estimado</span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
        <p className="muted" style={{ fontSize: 12, marginTop: 18 }}>
          <Icon name="bolt" size={13} /> O custo usa o menor preço de cada ingrediente entre as lojas.
        </p>
      </main>
    </>
  );
}
