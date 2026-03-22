<template>
  <div class="dashboard-page">
    <header>
      <div class="logo">AutoBooking</div>
      <div class="nav">
        <button @click="router.push('/company/services')">Услуги</button>
        <button @click="router.push('/company/calendar')">Календарь</button>
        <button @click="handleLogout">Выйти</button>
      </div>
    </header>

    <div class="container">
      <h2 class="page-title">Записи клиентов</h2>

      <div v-if="loading" class="loading">Загрузка...</div>
      <div v-else-if="error" class="error-message">{{ error }}</div>
      <div v-else-if="!companyId" class="empty-state">
        Компания не найдена. Обновите страницу или создайте компанию в настройках.
        <br>
        <button class="retry-btn" @click="initCompanyData">Повторить</button>
      </div>
      <div v-else-if="bookings.length === 0" class="empty-state">
        Пока нет записей
      </div>

      <div v-else class="bookings-list">
        <div 
          v-for="booking in bookings" 
          :key="booking.id" 
          class="booking-card"
        >
          <div class="booking-header">
            <div>
              <h3>Клиент #{{ booking.user_id }}</h3>
              <div>ID записи: #{{ booking.id }} • Услуга #{{ booking.service_id }}</div>
            </div>
            <div :class="['status', getStatusClass(booking.status)]">
              {{ getStatusText(booking.status) }}
            </div>
          </div>

          <div class="booking-info">
            <div>
              <strong>Дата:</strong><br>
              {{ formatDate(booking.start_at) }}
            </div>
            <div>
              <strong>Время:</strong><br>
              {{ formatTime(booking.start_at) }}
            </div>
            <div>
              <strong>Статус:</strong><br>
              {{ getStatusText(booking.status) }}
            </div>
            <div v-if="booking.notes">
              <strong>Заметка:</strong><br>
              {{ booking.notes }}
            </div>
            <div>
              <strong>Создано:</strong><br>
              {{ formatDate(booking.created_at) }}
            </div>
          </div>

          <div class="booking-actions">
            <button 
              v-if="booking.status === 'pending'" 
              class="confirm-btn" 
              @click="confirmBooking(booking.id)"
              :disabled="processingId === booking.id"
            >
              {{ processingId === booking.id ? 'Обработка...' : 'Подтвердить' }}
            </button>
            <button 
              class="contact-btn" 
              @click="contactClient(booking.user_id)"
            >
              Связаться
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuth } from '@/composables/useAuth';

const router = useRouter();
const auth = useAuth();

const loading = ref(true);
const error = ref('');
const processingId = ref(null);
const bookings = ref([]);
const companyId = ref(null);

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

onMounted(async () => {
  await initCompanyData();
});

// 🔹 Инициализация: получаем данные пользователя и компании
const initCompanyData = async () => {
  loading.value = true;
  error.value = '';

  try {
    // 1. Проверяем авторизацию
    if (!auth.isAuthenticated()) {
      router.push('/login/company');
      return;
    }

    // 2. Загружаем company_id через новый эндпоинт
    await loadCompanyId();

    // 3. Если company_id найден — загружаем записи
    if (companyId.value) {
      await loadBookings();
    }
  } catch (err) {
    console.error('Ошибка инициализации:', err);
    error.value = err.message || 'Ошибка загрузки данных';
  } finally {
    loading.value = false;
  }
};

// 🔹 Получаем ID компании текущего владельца
const loadCompanyId = async () => {
  try {
    const token = localStorage.getItem('access_token');
    
    // Запрашиваем компанию через новый эндпоинт
    const response = await fetch(`${API_URL}/owner/me/company`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (response.ok) {
      const data = await response.json();
      companyId.value = data.id;
      return;
    }

    if (response.status === 404) {
      error.value = 'Компания не найдена. Возможно, она ещё не создана.';
      return;
    }

    throw new Error('Не удалось получить данные компании');
  } catch (err) {
    console.warn('Ошибка получения company_id:', err);
    throw err;
  }
};

// 🔹 Загрузка записей компании
const loadBookings = async () => {
  if (!companyId.value) {
    error.value = 'ID компании не найден';
    return;
  }

  loading.value = true;
  error.value = '';

  try {
    const token = localStorage.getItem('access_token');
    const response = await fetch(
      `${API_URL}/owner/company/${companyId.value}/bookings`,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      }
    );

    if (response.status === 403) {
      throw new Error('Нет доступа к этой компании. Проверьте права владельца.');
    }
    if (response.status === 404) {
      throw new Error('Компания или записи не найдены');
    }
    if (!response.ok) {
      throw new Error('Ошибка загрузки записей');
    }

    bookings.value = await response.json();
  } catch (err) {
    error.value = err.message;
  } finally {
    loading.value = false;
  }
};

// 🔹 Подтверждение записи
const confirmBooking = async (bookingId) => {
  processingId.value = bookingId;

  try {
    const token = localStorage.getItem('access_token');
    const response = await fetch(
      `${API_URL}/owner/bookings/${bookingId}/confirm`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      }
    );

    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.detail || 'Не удалось подтвердить запись');
    }

    // Обновляем статус локально
    const booking = bookings.value.find(b => b.id === bookingId);
    if (booking) {
      booking.status = 'confirmed';
    }
  } catch (err) {
    error.value = err.message;
  } finally {
    processingId.value = null;
  }
};

// 🔹 Связь с клиентом (заглушка)
const contactClient = (userId) => {
  alert(`Связаться с клиентом #${userId}\n(Функция в разработке)`);
};

// 🔹 Выход из системы
const handleLogout = () => {
  auth.logout();
  router.push('/');
};

// 🔹 Утилиты для отображения
const getStatusClass = (status) => {
  const map = {
    pending: 'active',
    confirmed: 'completed',
    cancelled: 'cancelled',
  };
  return map[status] || '';
};

const getStatusText = (status) => {
  const map = {
    pending: 'Активна',
    confirmed: 'Завершена',
    cancelled: 'Отменена',
  };
  return map[status] || status;
};

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
};

const formatTime = (dateString) => {
  return new Date(dateString).toLocaleTimeString('ru-RU', {
    hour: '2-digit',
    minute: '2-digit',
  });
};
</script>

<style scoped>
.dashboard-page {
  font-family: "Segoe UI", Arial, sans-serif;
  background: #f5f7fa;
  min-height: 100vh;
}

header {
  background: linear-gradient(135deg, #065f46, #16a34a);
  color: white;
  padding: 20px 50px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo {
  font-size: 22px;
  font-weight: bold;
}

.nav {
  display: flex;
  gap: 10px;
}

.nav button {
  padding: 8px 15px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  background: white;
  color: #065f46;
  font-weight: 500;
  transition: background 0.2s;
}

.nav button:hover {
  background: #f3f4f6;
}

.container {
  width: 1100px;
  max-width: 95%;
  margin: 40px auto;
}

.page-title {
  margin-bottom: 30px;
  color: #1f2937;
}

.loading,
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #6b7280;
  background: white;
  border-radius: 20px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.08);
}

.retry-btn {
  margin-top: 15px;
  padding: 8px 20px;
  border-radius: 8px;
  border: none;
  background: #16a34a;
  color: white;
  cursor: pointer;
  font-weight: 500;
}

.retry-btn:hover {
  background: #15803d;
}

.error-message {
  background: #fef2f2;
  color: #dc2626;
  padding: 15px;
  border-radius: 12px;
  margin-bottom: 20px;
  text-align: center;
}

.booking-card {
  background: white;
  padding: 25px;
  border-radius: 20px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.08);
  margin-bottom: 20px;
  transition: 0.3s;
}

.booking-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 15px 35px rgba(0,0,0,0.12);
}

.booking-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.booking-header h3 {
  margin-bottom: 5px;
  color: #111827;
}

.booking-header div:last-child {
  color: #6b7280;
  font-size: 14px;
}

.status {
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
}

.status.active {
  background: #dcfce7;
  color: #166534;
}

.status.completed {
  background: #e0f2fe;
  color: #1e40af;
}

.status.cancelled {
  background: #fee2e2;
  color: #991b1b;
}

.booking-info {
  margin-top: 15px;
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 20px;
  font-size: 14px;
  color: #6b7280;
}

.booking-info strong {
  color: #374151;
}

.booking-actions {
  margin-top: 20px;
  display: flex;
  gap: 10px;
}

.booking-actions button {
  padding: 8px 15px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  font-weight: 500;
  transition: background 0.2s;
}

.contact-btn {
  background: #16a34a;
  color: white;
}

.contact-btn:hover {
  background: #15803d;
}

.confirm-btn {
  background: #e0f2fe;
  color: #15803d;
}

.confirm-btn:hover:not(:disabled) {
  background: #bfdbfe;
}

.confirm-btn:disabled {
  background: #d1d5db;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .booking-info {
    grid-template-columns: repeat(2, 1fr);
  }

  header {
    padding: 15px 20px;
  }
}
</style>