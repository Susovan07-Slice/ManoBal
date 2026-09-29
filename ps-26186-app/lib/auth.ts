import { apiClient, setStoredToken, getStoredToken } from './api';
import { Token, UserOut } from '@/types/api';

export interface JawanSignupData {
  username: string;
  password: string;
  name: string;
  personnel_code: string;
  age: number;
  gender: string;
  department: string;
  job_role: string;
  battalion: string;
  location: string;
  experience_years: number;
  duty_hours_per_week?: number;
}

export async function registerJawan(data: JawanSignupData): Promise<Token> {
  const token = await apiClient<Token>('/auth/register-jawan', {
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
