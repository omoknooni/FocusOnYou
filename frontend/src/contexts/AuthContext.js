import React, { createContext, useState, useEffect } from 'react';
import api from '../services/api';

export const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);

  useEffect(() => {
    // 초기 로그인 상태 확인
    api.get('/jobs')
      .then(() => setUser({ username: 'me' }))
      .catch(() => setUser(null));
  }, []);

  const login = async (username, password) => {
    await api.post('/login', { username, password });
    setUser({ username });
  };

  const logout = async () => {
    await api.get('/logout');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}