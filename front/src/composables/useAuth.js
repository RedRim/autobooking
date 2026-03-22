import { ref } from 'vue';
import { useRouter } from 'vue-router';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Composable для работы с авторизацией
 * @returns {Object} Методы и состояния для аутентификации
 */
export function useAuth() {
  const router = useRouter();
  
  // Реактивные состояния
  const loading = ref(false);
  const error = ref(null);
  const user = ref(null);

  /**
   * Вспомогательная функция для авторизованных запросов
   * Автоматически добавляет токен и обрабатывает 401 ошибки
   */
  const authFetch = async (url, options = {}) => {
    const token = localStorage.getItem('access_token');
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(url, { ...options, headers });

    // Если токен истёк или невалиден — разлогиниваем пользователя
    if (response.status === 401) {
      logout();
      if (router.currentRoute.value.meta.requiresAuth) {
        router.push('/login/user');
      }
      throw new Error('Сессия истекла. Пожалуйста, войдите снова.');
    }

    return response;
  };

  /**
   * Вход пользователя
   * @param {string} email 
   * @param {string} password 
   * @returns {Promise<Object>} Данные токена
   */
  const login = async (email, password) => {
    loading.value = true;
    error.value = null;

    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Ошибка входа');
      }

      // Сохраняем токен
      localStorage.setItem('access_token', data.access_token);
      
      // Загружаем данные пользователя
      await fetchCurrentUser();

      return data;
    } catch (err) {
      error.value = err.message;
      throw err;
    } finally {
      loading.value = false;
    }
  };

  /**
   * Регистрация нового пользователя
   * @param {string} email 
   * @param {string} password 
   * @param {string|null} companyName 
   * @returns {Promise<Object>} Данные токена
   */
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

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Ошибка регистрации');
      }

      // Сохраняем токен
      localStorage.setItem('access_token', data.access_token);
      
      // Загружаем данные пользователя
      await fetchCurrentUser();

      return data;
    } catch (err) {
      error.value = err.message;
      throw err;
    } finally {
      loading.value = false;
    }
  };

  /**
   * Получение данных текущего пользователя
   * @returns {Promise<Object>} Данные пользователя
   */
  const fetchCurrentUser = async () => {
    const token = localStorage.getItem('access_token');
    
    if (!token) {
      throw new Error('Токен не найден');
    }

    try {
      const response = await authFetch(`${API_URL}/auth/me`);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Ошибка получения данных');
      }

      user.value = data;
      return data;
    } catch (err) {
      error.value = err.message;
      throw err;
    }
  };

  /**
   * Инициализация сессии при загрузке приложения
   * Проверяет токен и загружает пользователя, если он есть
   */
  const initAuth = async () => {
    const token = localStorage.getItem('access_token');
    
    if (token) {
      try {
        await fetchCurrentUser();
      } catch (err) {
        // Токен невалиден, очищаем
        logout();
      }
    }
  };

  /**
   * Выход из системы
   */
  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_role');
    user.value = null;
    error.value = null;
    
    // Перенаправляем на главную или страницу входа
    if (router) {
      router.push('/');
    }
  };

  /**
   * Проверка, авторизован ли пользователь
   * @returns {boolean}
   */
  const isAuthenticated = () => {
    return !!localStorage.getItem('access_token');
  };

  /**
   * Получение роли пользователя
   * @returns {string|null} 'user' | 'company' | 'admin' | null
   */
  const getUserRole = () => {
    if (user.value?.role) {
      return user.value.role;
    }
    return localStorage.getItem('user_role');
  };

  /**
   * Проверка наличия конкретной роли
   * @param {string} role 
   * @returns {boolean}
   */
  const hasRole = (role) => {
    return getUserRole() === role;
  };

  /**
   * Очистка ошибки
   */
  const clearError = () => {
    error.value = null;
  };

  return {
    // Состояния
    loading,
    error,
    user,

    // Методы аутентификации
    login,
    register,
    logout,
    initAuth,
    fetchCurrentUser,

    // Утилиты
    isAuthenticated,
    getUserRole,
    hasRole,
    clearError,
  };
}