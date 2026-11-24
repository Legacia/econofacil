// Cliente HTTP do EconoFácil — fala com a API FastAPI do backend.
// Gerencia tokens (access + refresh) e tenta renovar automaticamente no 401.

const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

const ACCESS_KEY = "ef_access";
const REFRESH_KEY = "ef_refresh";

export const tokens = {
  get access() {
    return localStorage.getItem(ACCESS_KEY);
  },
  get refresh() {
    return localStorage.getItem(REFRESH_KEY);
  },
  set({ access_token, refresh_token }) {
    if (access_token) localStorage.setItem(ACCESS_KEY, access_token);
    if (refresh_token) localStorage.setItem(REFRESH_KEY, refresh_token);
  },
  clear() {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};

export class ApiError extends Error {
  constructor(status, detail) {
    super(typeof detail === "string" ? detail : "Erro na requisição");
    this.status = status;
    this.detail = detail;
  }
}

async function tryRefresh() {
  const refresh_token = tokens.refresh;
  if (!refresh_token) return false;
  const res = await fetch(`${BASE}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token }),
  });
  if (!res.ok) {
    tokens.clear();
    return false;
  }
  tokens.set(await res.json());
  return true;
}

async function request(path, { method = "GET", body, auth = false, retry = true } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (auth && tokens.access) headers.Authorization = `Bearer ${tokens.access}`;

  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (res.status === 401 && auth && retry && (await tryRefresh())) {
    return request(path, { method, body, auth, retry: false });
  }

  const text = await res.text();
  const data = text ? JSON.parse(text) : null;
  if (!res.ok) throw new ApiError(res.status, data?.detail ?? res.statusText);
  return data;
}

export const api = {
  // Auth
  register: (payload) => request("/auth/register", { method: "POST", body: payload }),
  login: (payload) => request("/auth/login", { method: "POST", body: payload }),
  logout: (refresh_token) => request("/auth/logout", { method: "POST", body: { refresh_token } }),
  forgotPassword: (email) => request("/auth/password/forgot", { method: "POST", body: { email } }),
  resetPassword: (token, new_password) =>
    request("/auth/password/reset", { method: "POST", body: { token, new_password } }),

  // Usuário
  me: () => request("/users/me", { auth: true }),
  updateMe: (payload) => request("/users/me", { method: "PATCH", body: payload, auth: true }),

  // LGPD
  consents: () => request("/lgpd/consents", { auth: true }),
  setConsents: (consents) => request("/lgpd/consents", { method: "PUT", body: { consents }, auth: true }),
  exportData: () => request("/lgpd/export", { auth: true }),
  deleteAccount: () => request("/lgpd/account", { method: "DELETE", auth: true }),

  // Catálogo
  categories: () => request("/catalog/categories"),
  products: (params = {}) => {
    const q = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== undefined && v !== "" && v !== null)
    ).toString();
    return request(`/catalog/products${q ? `?${q}` : ""}`);
  },
  product: (id) => request(`/catalog/products/${id}`),

  // Modo demonstração local (PIX simulado)
  simulatePaid: (paymentId) => request(`/payments/${paymentId}/simulate-paid`, { method: "POST", auth: true }),
  isDemo: () => fetch("/health").then((r) => (r.ok ? r.json() : {})).then((d) => !!d.demo).catch(() => false),

  // Carrinho
  cart: () => request("/cart", { auth: true }),
  addItem: (product_id, quantity = 1) =>
    request("/cart/items", { method: "POST", body: { product_id, quantity }, auth: true }),
  setQuantity: (product_id, quantity) =>
    request(`/cart/items/${product_id}`, { method: "PATCH", body: { quantity }, auth: true }),
  removeItem: (product_id) => request(`/cart/items/${product_id}`, { method: "DELETE", auth: true }),
  optimize: () => request("/cart/optimize", { auth: true }),
  checkout: (strategy, payment_method) =>
    request("/cart/checkout", { method: "POST", body: { strategy, payment_method }, auth: true }),

  // Pedidos e pagamentos
  orders: () => request("/orders", { auth: true }),
  order: (id) => request(`/orders/${id}`, { auth: true }),
  payment: (id) => request(`/payments/${id}`, { auth: true }),

  // Noor
  noorStatus: () => request("/noor/status"),
  alsoBought: (product_id, limit = 5) => request(`/noor/recommendations/also-bought?product_id=${product_id}&limit=${limit}`),
  usual: (limit = 6) => request(`/noor/recommendations/usual?limit=${limit}`, { auth: true }),

  // Receitas (RN-020)
  recipes: () => request("/recipes"),
  recipe: (id, servings) => request(`/recipes/${id}${servings ? `?servings=${servings}` : ""}`),
  recipeToCart: (id, servings) =>
    request(`/recipes/${id}/add-to-cart`, { method: "POST", body: { servings }, auth: true }),

  // Listas de compras (RN-020)
  lists: () => request("/lists", { auth: true }),
  createList: (name) => request("/lists", { method: "POST", body: { name }, auth: true }),
  list: (id) => request(`/lists/${id}`, { auth: true }),
  renameList: (id, name) => request(`/lists/${id}`, { method: "PATCH", body: { name }, auth: true }),
  deleteList: (id) => request(`/lists/${id}`, { method: "DELETE", auth: true }),
  addListItem: (id, product_id, quantity = 1) =>
    request(`/lists/${id}/items`, { method: "POST", body: { product_id, quantity }, auth: true }),
  updateListItem: (id, product_id, patch) =>
    request(`/lists/${id}/items/${product_id}`, { method: "PATCH", body: patch, auth: true }),
  removeListItem: (id, product_id) =>
    request(`/lists/${id}/items/${product_id}`, { method: "DELETE", auth: true }),
  compareList: (id) => request(`/lists/${id}/compare`, { auth: true }),
  listToCart: (id) => request(`/lists/${id}/to-cart`, { method: "POST", auth: true }),

  // Portal do lojista
  myStores: () => request("/merchant/stores", { auth: true }),
  setStorePix: (storeId, pix_key) =>
    request(`/merchant/stores/${storeId}`, { method: "PATCH", body: { pix_key }, auth: true }),
  inventory: (storeId) => request(`/merchant/stores/${storeId}/inventory`, { auth: true }),
  saveOffer: (storeId, productId, body) =>
    request(`/catalog/stores/${storeId}/offers/${productId}`, { method: "PUT", body, auth: true }),
  promotions: (storeId) => request(`/merchant/stores/${storeId}/promotions`, { auth: true }),
  createPromotion: (storeId, body) =>
    request(`/merchant/stores/${storeId}/promotions`, { method: "POST", body, auth: true }),
  endPromotion: (promoId) => request(`/merchant/promotions/${promoId}`, { method: "DELETE", auth: true }),
  merchantOrders: () => request("/merchant/orders", { auth: true }),
  setFulfillment: (orderId, status, store_id) =>
    request(`/merchant/orders/${orderId}/status`, { method: "PATCH", body: { status, store_id }, auth: true }),
  storeReport: (storeId) => request(`/merchant/stores/${storeId}/report`, { auth: true }),

  // Administração (RN-021)
  runExpirations: () => request("/admin/expirations/run", { method: "POST", auth: true }),
  scheduler: () => request("/admin/scheduler", { auth: true }),
};

export const brl = (v) =>
  (v ?? 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
