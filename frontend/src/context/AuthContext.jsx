import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { api, tokens } from "../api/client.js";

const AuthCtx = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadMe = useCallback(async () => {
    if (!tokens.access) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      setUser(await api.me());
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadMe();
  }, [loadMe]);

  const login = useCallback(async (email, password, otp_code) => {
    const pair = await api.login({ email, password, otp_code: otp_code || undefined });
    tokens.set(pair);
    const me = await api.me();
    setUser(me);
    return me;
  }, []);

  const register = useCallback(
    async (full_name, email, password) => {
      await api.register({ full_name, email, password });
      return login(email, password);
    },
    [login]
  );

  const logout = useCallback(async () => {
    try {
      if (tokens.refresh) await api.logout(tokens.refresh);
    } catch {
      /* ignore */
    }
    tokens.clear();
    setUser(null);
  }, []);

  return (
    <AuthCtx.Provider value={{ user, setUser, loading, login, register, logout }}>
      {children}
    </AuthCtx.Provider>
  );
}

export const useAuth = () => useContext(AuthCtx);
