import { ref } from 'vue';

import { API_URL } from '@/config';
import { formatApiError } from '@/utils/apiError';

/** Общее состояние авторизации для всего приложения (один экземпляр). */
const loading = ref(false);
const error = ref(null);
const user = ref(null);

function clearSession() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('user_role');
  user.value = null;
}

/**
 * Composable для работы с авторизацией.
 */
export function useAuth() {
  /**
   * @param {RequestInit} options
   * @param {{ redirectOn401?: boolean }} fetchOpts
   */
  const authFetch = async (path, options = {}, fetchOpts = {}) => {
    const { redirectOn401 = true } = fetchOpts;
    const token = localStorage.getItem('access_token');
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    const response = await fetch(`${API_URL}${path}`, { ...options, headers });

    if (response.status === 401) {
      clearSession();
      if (redirectOn401 && typeof window !== 'undefined') {
        window.location.assign('/login/user');
      }
      throw new Error('Сессия истекла. Пожалуйста, войдите снова.');
    }

    return response;
  };

  const login = async (email, password) => {
    loading.value = true;
    error.value = null;

    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(formatApiError(data));
      }

      localStorage.setItem('access_token', data.access_token);
      await fetchCurrentUser();
      return data;
    } catch (err) {
      error.value = err.message;
      throw err;
    } finally {
      loading.value = false;
    }
  };

  const register = async (email, password, companyName = null) => {
    loading.value = true;
    error.value = null;

    try {
      const payload = { email, password };
      if (companyName) {
        payload.company_name = companyName;
      }

      const response = await fetch(`${API_URL}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(formatApiError(data));
      }

      localStorage.setItem('access_token', data.access_token);
      await fetchCurrentUser();
      return data;
    } catch (err) {
      error.value = err.message;
      throw err;
    } finally {
      loading.value = false;
    }
  };

  const fetchCurrentUser = async () => {
    const token = localStorage.getItem('access_token');

    if (!token) {
      throw new Error('Токен не найден');
    }

    try {
      const response = await authFetch('/auth/me', {}, { redirectOn401: false });
      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(formatApiError(data));
      }

      user.value = data;
      if (data?.role) {
        localStorage.setItem('user_role', data.role);
      }
      return data;
    } catch (err) {
      error.value = err.message;
      throw err;
    }
  };

  const initAuth = async () => {
    const token = localStorage.getItem('access_token');

    if (!token) {
      return;
    }

    try {
      await fetchCurrentUser();
    } catch {
      clearSession();
    }
  };

  const logout = () => {
    clearSession();
    error.value = null;
    if (typeof window !== 'undefined') {
      window.location.assign('/');
    }
  };

  const isAuthenticated = () => !!localStorage.getItem('access_token');

  const getUserRole = () => {
    if (user.value?.role) {
      return user.value.role;
    }
    return localStorage.getItem('user_role');
  };

  const hasRole = (role) => getUserRole() === role;

  const clearError = () => {
    error.value = null;
  };

  return {
    loading,
    error,
    user,
    login,
    register,
    logout,
    initAuth,
    fetchCurrentUser,
    authFetch,
    isAuthenticated,
    getUserRole,
    hasRole,
    clearError,
  };
}
