import { Routes, Route, NavLink, Navigate, Outlet, Link, useLocation } from "react-router-dom";
import { useEffect } from "react";
import { useAuth } from "./context/AuthContext.jsx";
import { useCart } from "./context/CartContext.jsx";
import Icon from "./components/Icon.jsx";
import { Logo } from "./components/Brand.jsx";

import Home from "./pages/Home.jsx";
import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";
import ForgotPassword from "./pages/ForgotPassword.jsx";
import ResetPassword from "./pages/ResetPassword.jsx";
import Category from "./pages/Category.jsx";
import Product from "./pages/Product.jsx";
import Cart from "./pages/Cart.jsx";
import Checkout from "./pages/Checkout.jsx";
import OrderConfirmed from "./pages/OrderConfirmed.jsx";
import Orders from "./pages/Orders.jsx";
import Profile from "./pages/Profile.jsx";
import Recipes from "./pages/Recipes.jsx";
import RecipeDetail from "./pages/RecipeDetail.jsx";
import Lists from "./pages/Lists.jsx";
import ListDetail from "./pages/ListDetail.jsx";
import Merchant from "./pages/Merchant.jsx";
import Admin from "./pages/Admin.jsx";

const isPro = (user) => user && (user.role === "merchant" || user.role === "admin");

function useCartRefresh() {
  const { refresh } = useCart();
  const { user } = useAuth();
  useEffect(() => {
    refresh();
  }, [user, refresh]);
}

// Barra inferior (celular)
function Tabs() {
  const { count } = useCart();
  const tab = ({ isActive }) => (isActive ? "on" : "");
  return (
    <nav className="tabs" aria-label="Navegação principal">
      <NavLink to="/" className={tab} end><Icon name="home" />Início</NavLink>
      <NavLink to="/receitas" className={tab}><Icon name="chef" />Receitas</NavLink>
      <NavLink to="/carrinho" className={tab}>
        <Icon name="cart" />
        {count > 0 && <span className="cnt">{count}</span>}Carrinho
      </NavLink>
      <NavLink to="/pedidos" className={tab}><Icon name="receipt" />Pedidos</NavLink>
      <NavLink to="/perfil" className={tab}><Icon name="user" />Perfil</NavLink>
    </nav>
  );
}

// Barra superior (computador)
function TopNav() {
  const { count } = useCart();
  const { user } = useAuth();
  const tab = ({ isActive }) => (isActive ? "on" : "");
  return (
    <nav className="topnav" aria-label="Navegação principal">
      <Link to="/" className="logo-lockup" style={{ padding: 0 }}><Logo size={34} textSize={20} /></Link>
      <NavLink to="/" className={tab} end><Icon name="home" size={18} />Início</NavLink>
      <NavLink to="/receitas" className={tab}><Icon name="chef" size={18} />Receitas</NavLink>
      <NavLink to="/listas" className={tab}><Icon name="list" size={18} />Listas</NavLink>
      <NavLink to="/pedidos" className={tab}><Icon name="receipt" size={18} />Pedidos</NavLink>
      {isPro(user) && (
        <NavLink to={user.role === "admin" ? "/admin" : "/lojista"} className={tab}>
          <Icon name="store" size={18} />{user.role === "admin" ? "Admin" : "Minha loja"}
        </NavLink>
      )}
      <NavLink to="/carrinho" className={tab}>
        <Icon name="cart" size={18} />Carrinho{count > 0 && <span className="cnt">{count}</span>}
      </NavLink>
      {user ? (
        <NavLink to="/perfil" className={tab}><Icon name="user" size={18} />{user.full_name.split(" ")[0]}</NavLink>
      ) : (
        <NavLink to="/login" className={tab}><Icon name="user" size={18} />Entrar</NavLink>
      )}
    </nav>
  );
}

function Layout() {
  const { pathname } = useLocation();
  useCartRefresh();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return (
    <div className="app">
      <TopNav />
      <Outlet />
      <Tabs />
    </div>
  );
}

function RequireAuth({ children, roles }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return <div className="spinner">Carregando…</div>;
  if (!user) return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  if (roles && !roles.includes(user.role)) return <Navigate to="/" replace />;
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/cadastro" element={<Register />} />
      <Route path="/recuperar-senha" element={<ForgotPassword />} />
      <Route path="/redefinir-senha" element={<ResetPassword />} />

      <Route element={<Layout />}>
        <Route path="/" element={<Home />} />
        <Route path="/categoria/:id" element={<Category />} />
        <Route path="/produto/:id" element={<Product />} />
        <Route path="/receitas" element={<Recipes />} />
        <Route path="/receita/:id" element={<RecipeDetail />} />
        <Route path="/listas" element={<RequireAuth><Lists /></RequireAuth>} />
        <Route path="/listas/:id" element={<RequireAuth><ListDetail /></RequireAuth>} />
        <Route path="/carrinho" element={<RequireAuth><Cart /></RequireAuth>} />
        <Route path="/checkout" element={<RequireAuth><Checkout /></RequireAuth>} />
        <Route path="/pedido/:id" element={<RequireAuth><OrderConfirmed /></RequireAuth>} />
        <Route path="/pedidos" element={<RequireAuth><Orders /></RequireAuth>} />
        <Route path="/perfil" element={<RequireAuth><Profile /></RequireAuth>} />
        <Route path="/lojista" element={<RequireAuth roles={["merchant", "admin"]}><Merchant /></RequireAuth>} />
        <Route path="/admin" element={<RequireAuth roles={["admin"]}><Admin /></RequireAuth>} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
