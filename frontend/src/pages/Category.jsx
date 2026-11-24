import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../api/client.js";
import { ProductCard, Loading, Empty } from "../components/ui.jsx";

export default function Category() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [name, setName] = useState("Categoria");
  const [sort, setSort] = useState("price");
  const [products, setProducts] = useState(null);

  useEffect(() => {
    api.categories().then((cs) => {
      const c = cs.find((x) => x.id === id);
      if (c) setName(c.name);
    });
  }, [id]);

  useEffect(() => {
    setProducts(null);
    api
      .products({ category_id: id, sort, page_size: 30 })
      .then((d) => setProducts(d.items))
      .catch(() => setProducts([]));
  }, [id, sort]);

  return (
    <>
      <header className="appbar plain">
        <button className="back" onClick={() => navigate(-1)}>← Voltar</button>
        <h1 style={{ marginTop: 6 }}>{name}</h1>
      </header>
      <main className="content">
        <div className="chips">
          <span className={`chip ${sort === "price" ? "on" : ""}`} onClick={() => setSort("price")}>
            Menor preço
          </span>
          <span className={`chip ${sort === "name" ? "on" : ""}`} onClick={() => setSort("name")}>
            A–Z
          </span>
        </div>
        <div style={{ height: 12 }} />
        {products === null ? (
          <Loading />
        ) : products.length === 0 ? (
          <Empty emoji="📂">Nenhum produto nesta categoria.</Empty>
        ) : (
          <div className="grid">
            {products.map((p) => (
              <ProductCard key={p.id} p={p} />
            ))}
          </div>
        )}
      </main>
    </>
  );
}
