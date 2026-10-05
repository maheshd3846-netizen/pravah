/**
 * Base HTTP API Client for PRAVAH backend.
 */

const API_BASE = '/api';

export class ApiError extends Error {
  status: number;
  body?: any;

  constructor(status: number, message: string, body?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.body = body;
  }
}

export async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((options.headers as Record<string, string>) || {}),
  };

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      let errorBody: any = null;
      try {
        errorBody = await response.json();
      } catch {
        errorBody = await response.text();
      }

      let message = `API error (${response.status}): ${response.statusText}`;
      if (typeof errorBody === 'string' && errorBody.trim().length > 0) {
        message = errorBody;
      } else if (errorBody?.detail) {
        if (typeof errorBody.detail === 'string') {
          message = errorBody.detail;
        } else if (Array.isArray(errorBody.detail)) {
          message = errorBody.detail
            .map((item: any) => {
              if (typeof item === 'string') return item;
              const field = Array.isArray(item?.loc) ? item.loc.slice(1).join('.') : '';
              const msg = item?.msg || item?.message || JSON.stringify(item);
              return field ? `${field}: ${msg}` : msg;
            })
            .join('; ');
        } else if (typeof errorBody.detail === 'object') {
          message = JSON.stringify(errorBody.detail);
        }
      } else if (errorBody?.message) {
        message = typeof errorBody.message === 'string' ? errorBody.message : JSON.stringify(errorBody.message);
      }

      throw new ApiError(response.status, message, errorBody);
    }

    return (await response.json()) as T;
  } catch (err: any) {
    if (err instanceof ApiError) {
      throw err;
    }
    const fallback = typeof err?.message === 'string' ? err.message : 'Network communication failure. Please verify PRAVAH backend server is running.';
    throw new ApiError(0, fallback);
  }
}
