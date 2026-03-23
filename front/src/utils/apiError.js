/**
 * Текст ошибки из ответа FastAPI (detail: string | { msg }[] | object).
 */
export function formatApiError(data) {
  if (!data || data.detail === undefined || data.detail === null) {
    return 'Ошибка запроса';
  }
  const { detail } = data;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => (typeof item === 'object' && item?.msg ? item.msg : String(item)))
      .join('; ');
  }
  if (typeof detail === 'object') {
    try {
      return JSON.stringify(detail);
    } catch {
      return 'Ошибка запроса';
    }
  }
  return String(detail);
}
