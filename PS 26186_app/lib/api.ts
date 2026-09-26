export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export class ApiError extends Error {
  status: number;
  data: any;

  constructor(status: number, message: string, data?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

export function getStoredToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('manobal_jawan_token');
}

export function setStoredToken(token: string | null): void {
  if (typeof window === 'undefined') return;
  if (token) {
    localStorage.setItem('manobal_jawan_token', token);
  } else {
    localStorage.removeItem('manobal_jawan_token');
  }
}

interface RequestOptions extends RequestInit {
  requiresAuth?: boolean;
}

export async function apiClient<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { requiresAuth = true, headers = {}, ...rest } = options;

  const url = endpoint.startsWith('http')
    ? endpoint
    : `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  const requestHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(headers as Record<string, string>),
  };

  if (requiresAuth) {
    const token = getStoredToken();
    if (token) {
      requestHeaders['Authorization'] = `Bearer ${token}`;
    }
  }

  let response: Response;
  try {
    response = await fetch(url, {
      ...rest,
      headers: requestHeaders,
    });
  } catch (err: any) {
    throw new ApiError(
      0,
      'Unable to connect to ManoBal backend. Please verify that the API server is online.',
      err
    );
  }

  let data: any = null;
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    try {
      data = await response.json();
    } catch {
      data = null;
    }
  }

  // Handle 401 Unauthorized
  if (response.status === 401) {
    if (requiresAuth) {
      if (typeof window !== 'undefined') {
        setStoredToken(null);
        if (!window.location.pathname.includes('/login') && !window.location.pathname.includes('/signup')) {
          window.location.href = '/login?expired=1';
        }
      }
      throw new ApiError(401, 'Session expired. Please sign in again.');
    } else {
      const msg = data?.detail || 'Incorrect service username or password.';
      throw new ApiError(401, typeof msg === 'string' ? msg : JSON.stringify(msg), data);
    }
  }

  if (!response.ok) {
    let errorMsg = `API Error ${response.status}`;
    if (data?.detail) {
      if (Array.isArray(data.detail)) {
        errorMsg = data.detail.map((d: any) => d.msg || d.message).join('; ');
      } else if (typeof data.detail === 'string') {
        errorMsg = data.detail;
      }
    } else if (data?.message) {
      errorMsg = data.message;
    }
    throw new ApiError(response.status, errorMsg, data);
  }

  return data as T;
}
