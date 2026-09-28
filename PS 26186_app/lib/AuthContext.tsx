'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { UserRole, UserOut } from '@/types/api';
import { getCurrentUser, login as authLogin, logout as authLogout, registerJawan, JawanSignupData } from './auth';
import { setStoredToken, getStoredToken, getStoredUser, setStoredUser } from './api';

interface AuthContextType {
  user: UserOut | null;
  role: UserRole;
  token: string | null;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  signup: (data: JawanSignupData) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserOut | null>(null);
  const [role, setRole] = useState<UserRole>('personnel');
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    async function initAuth() {
      const storedToken = getStoredToken();
      const storedUser = getStoredUser();

      if (!storedToken) {
        setIsLoading(false);
        setUser(null);
        setToken(null);
        return;
      }

      setToken(storedToken);
      if (storedUser) {
        setUser(storedUser);
        setRole((storedUser.role as UserRole) || 'personnel');
        setIsLoading(false);
      }

      try {
        const currentUser = await getCurrentUser();
        setUser(currentUser);
        setRole(currentUser.role as UserRole);
        setStoredUser(currentUser);
      } catch (err) {
        console.warn('Mobile session could not be restored:', err);
        setStoredToken(null);
        setStoredUser(null);
        setUser(null);
        setToken(null);
      } finally {
        setIsLoading(false);
      }
    }

    initAuth();
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    setIsLoading(true);
    try {
      const tokenResp = await authLogin(username, password);
      setToken(tokenResp.access_token);
      const currentUser = await getCurrentUser();
      setUser(currentUser);
      setRole(currentUser.role);
      setStoredUser(currentUser);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const signup = useCallback(async (data: JawanSignupData) => {
    setIsLoading(true);
    try {
      const tokenResp = await registerJawan(data);
      setToken(tokenResp.access_token);
      const currentUser = await getCurrentUser();
      setUser(currentUser);
      setRole(currentUser.role);
      setStoredUser(currentUser);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    setToken(null);
    setRole('personnel');
    setStoredUser(null);
    authLogout();
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        role,
        token,
        isLoading,
        login,
        signup,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
