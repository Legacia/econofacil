import { createContext, useContext, useState, useCallback } from "react";
import { api } from "../api/client.js";
import { useAuth } from "./AuthContext.jsx";

const CartCtx = createContext(null);

export function CartProvider({ children }) {
  const { user } = useAuth();
  const [cart, setCart] = useState(null);

  const refresh = useCallback(async () => {
    if (!user) {
      setCart(null);
      return;
    }
    try {
      setCart(await api.cart());
    } catch {
      setCart(null);
    }
  }, [user]);

  const add = useCallback(async (productId, qty = 1) => {
    setCart(await api.addItem(productId, qty));
  }, []);

  const setQty = useCallback(async (productId, qty) => {
    setCart(await api.setQuantity(productId, qty));
  }, []);

  const remove = useCallback(async (productId) => {
    setCart(await api.removeItem(productId));
  }, []);

  const count = cart?.item_count ?? 0;

  return (
    <CartCtx.Provider value={{ cart, count, refresh, add, setQty, remove, setCart }}>
      {children}
    </CartCtx.Provider>
  );
}

export const useCart = () => useContext(CartCtx);
