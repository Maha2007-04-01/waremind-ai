// AuthProvider.jsx — ONLY exports React components.
// This allows Vite Fast Refresh to work correctly.
import React, { useState, useEffect, useContext } from 'react';
import { AuthContext } from './AuthContext.js';
import { loginUser, registerUser, fetchCurrentUser } from '../services/api';

const DEFAULT_USER = {
  id: 'USR-MANAGER',
  username: 'manager',
  name: 'Sarah Chen',
  email: 'manager@waremind.ai',
  role: 'Fulfillment Center Manager',
  badge: 'MANAGER'
};

// Safe wrappers — never throw even if localStorage is blocked
function safeGetItem(key) {
  try { return localStorage.getItem(key); } catch { return null; }
}
function safeSetItem(key, value) {
  try { localStorage.setItem(key, value); } catch { /* noop */ }
}
function safeRemoveItem(key) {
  try { localStorage.removeItem(key); } catch { /* noop */ }
}
function safeParse(str) {
  try { return str ? JSON.parse(str) : null; } catch { return null; }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const stored = safeParse(safeGetItem('waremind_user'));
    return stored || DEFAULT_USER;
  });

  const [token, setToken] = useState(() => {
    return safeGetItem('waremind_token') || '';
  });

  const [loading, setLoading] = useState(false);

  // On mount: verify stored token against backend
  useEffect(() => {
    const savedToken = safeGetItem('waremind_token');
    if (!savedToken) {
      setUser(DEFAULT_USER);
      setLoading(false);
      return;
    }

    setLoading(true);
    fetchCurrentUser()
      .then((res) => {
        if (res && res.data) {
          setUser(res.data);
          safeSetItem('waremind_user', JSON.stringify(res.data));
        }
      })
      .catch(() => {
        // Token invalid or backend offline — keep existing stored user
        const stored = safeParse(safeGetItem('waremind_user'));
        setUser(stored || DEFAULT_USER);
      })
      .finally(() => setLoading(false));
  }, []);

  const login = async (usernameOrEmail, password) => {
    try {
      const res = await loginUser({ usernameOrEmail, password });
      if (res?.data?.token) {
        safeSetItem('waremind_token', res.data.token);
        safeSetItem('waremind_user', JSON.stringify(res.data.user));
        setToken(res.data.token);
        setUser(res.data.user);
        return res.data.user;
      }
    } catch (err) {
      // Backend offline — create offline session
      const query = (usernameOrEmail || '').toLowerCase().trim();
      const isAdmin = query.includes('admin');
      const isCustomer = query.includes('customer');
      const offlineUser = {
        id: `USR-${Date.now().toString().slice(-4)}`,
        username: query || 'manager',
        name: query.charAt(0).toUpperCase() + query.slice(1),
        email: query.includes('@') ? query : `${query}@waremind.ai`,
        role: isAdmin
          ? 'System Administrator'
          : isCustomer
          ? 'Enterprise Client'
          : 'Fulfillment Center Manager',
        badge: (query || 'MANAGER').toUpperCase()
      };
      safeSetItem('waremind_token', 'offline');
      safeSetItem('waremind_user', JSON.stringify(offlineUser));
      setToken('offline');
      setUser(offlineUser);
      return offlineUser;
    }
    throw new Error('Authentication failed');
  };

  const register = async ({ name, email, username, password, role }) => {
    const res = await registerUser({ name, email, username, password, role });
    if (res?.data?.token) {
      safeSetItem('waremind_token', res.data.token);
      safeSetItem('waremind_user', JSON.stringify(res.data.user));
      setToken(res.data.token);
      setUser(res.data.user);
      return res.data.user;
    }
    throw new Error(res?.error?.message || 'Registration failed');
  };

  const logout = () => {
    safeRemoveItem('waremind_token');
    safeRemoveItem('waremind_user');
    setToken('');
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{ user, token, login, register, logout, isAuthenticated: !!user, loading }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within an AuthProvider');
  return context;
}
