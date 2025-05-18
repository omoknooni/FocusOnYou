import React, { createContext, useState, useEffect } from 'react';
import { signIn, signOut, getCurrentUser, fetchAuthSession } from 'aws-amplify/auth';
import api from '../services/api';

export const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 세션 유지 확인
    const checkAuth = async () => {
      try {
        const currentUser = await getCurrentUser();
        setUser(currentUser);
        const session = await fetchAuthSession();
        const token = session.tokens.idToken.toString();
        api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      } catch (error) {
        setUser(null);
      } finally {
        setLoading(false);
      }
    };
    
    checkAuth();
  }, []);

  const login = async (email, password) => {
    const { isSignedIn, nextStep } = await signIn({ username: email, password });
    if (isSignedIn) {
      const currentUser = await getCurrentUser();
      const session = await fetchAuthSession();
      const token = session.tokens.idToken.toString();
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      setUser(currentUser);
    }
  };

  const logout = async () => {
    await signOut();
    delete api.defaults.headers.common['Authorization'];
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}