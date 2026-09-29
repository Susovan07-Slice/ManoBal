'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { UserRole } from '@/types/rbac';
import { UserOut, CommanderSignupData } from '@/types/api';
import { getCurrentUser, login as authLogin, logout as authLogout, registerCommander, isAuthenticated } from './auth';
import { setStoredToken, getStoredToken, getStoredUser, setStoredUser } from './api';

interface AuthContextType {
  user: UserOut | null;
  role: UserRole;
  token: string | null;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  signupCommander: (data: CommanderSignupData) => Promise<void>;
  logout: () => void;
  setRole: (role: UserRole) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserOut | null>(null);
  const [role, setRole] = useState<UserRole>('officer');
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Initialize auth state on client mount to guarantee SSR-client hydration parity
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
        setRole((storedUser.role as UserRole) || 'officer');
        setIsLoading(false);
      }

      try {
        const currentUser = await getCurrentUser();
        setUser(currentUser);
        setRole(currentUser.role as UserRole);
        setStoredUser(currentUser);
      } catch (err) {
        console.warn('Stored session could not be restored:', err);
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
      setRole(currentUser.role as UserRole);
      setStoredUser(currentUser);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const signupCommander = useCallback(async (data: CommanderSignupData) => {
    setIsLoading(true);
    try {
      const tokenResp = await registerCommander(data);
      setToken(tokenResp.access_token);
      const currentUser = await getCurrentUser();
      setUser(currentUser);
      setRole(currentUser.role as UserRole);
      setStoredUser(currentUser);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    setToken(null);
    setRole('officer');
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
        signupCommander,
        logout,
        setRole,
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

// Backward-compatible hook for existing components using useRole()
export function useRole() {
  const { role, setRole } = useAuth();
  return { role, setRole };
}
