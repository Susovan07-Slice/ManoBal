import { apiClient, setStoredToken, getStoredToken } from './api';
import { Token, UserOut, CommanderSignupData } from '@/types/api';

export async function registerCommander(data: CommanderSignupData): Promise<Token> {
  const token = await apiClient<Token>('/auth/register-commander', {
    method: 'POST',
    body: JSON.stringify(data),
    requiresAuth: false,
  });
  setStoredToken(token.access_token);
  return token;
}

export async function login(username: string, password: string): Promise<Token> {
  const token = await apiClient<Token>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
    requiresAuth: false,
  });
  setStoredToken(token.access_token);
  return token;
}

export async function getCurrentUser(): Promise<UserOut> {
  return apiClient<UserOut>('/auth/me', {
    method: 'GET',
    requiresAuth: true,
  });
}

export function logout(): void {
  setStoredToken(null);
  if (typeof window !== 'undefined') {
    window.location.href = '/login';
  }
}

export function isAuthenticated(): boolean {
  return !!getStoredToken();
}
