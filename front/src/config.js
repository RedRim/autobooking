/**
 * Базовый URL FastAPI (без завершающего слэша).
 *
 * Приоритет:
 * 1) VITE_API_URL на этапе сборки: "/api" (nginx прокси на тот же хост) или полный URL.
 * 2) В браузере без VITE_API_URL — тот же хост, порт 8000 (локально без прокси).
 * 3) Fallback для SSR/тестов: http://localhost:8000
 */
function resolveApiUrl() {
  const fromEnv = import.meta.env.VITE_API_URL;
  if (fromEnv != null && String(fromEnv).trim() !== '') {
    return String(fromEnv).trim().replace(/\/$/, '');
  }
  if (typeof window !== 'undefined' && window.location) {
    const { protocol, hostname } = window.location;
    return `${protocol}//${hostname}:8000`;
  }
  return 'http://localhost:8000';
}

export const API_URL = resolveApiUrl();
