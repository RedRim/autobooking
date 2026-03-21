<template>
  <div class="bookings-page">
    <header>
      <div class="logo">AutoBooking</div>
      <div class="nav">
        <button @click="router.push('/dashboard/user')">Поиск</button>
        <button @click="handleLogout">Выйти</button>
      </div>
    </header>

    <div class="container">
      <h2 class="page-title">Мои записи</h2>

      <div v-if="loading" class="loading">Загрузка...</div>
      <div v-else-if="error" class="error-message">{{ error }}</div>
      <div v-else-if="bookings.length === 0" class="empty-state">
        У вас пока нет записей. <router-link to="/dashboard/user">Найти услугу</router-link>
      </div>

      <div v-else class="bookings-list">
        <div 
          v-for="booking in bookings" 
          :key="booking.id" 
          class="booking-card"
        >
          <div class="booking-header">
            <div>
              <h3>{{ getCompanyName(booking.company_id) }}</h3>
              <div>{{ getServiceName(booking.service_id) }}</div>
            </div>
            <div :class="['status', getStatusClass(booking.status)]">
              {{ getStatusText(booking.status) }}
            </div>
          </div>

          <div class="booking-info">
            <div><strong>Дата:</strong><br> {{ formatDate(booking.start_at) }}</div>
            <div><strong>Время:</strong><br> {{ formatTime(booking.start_at) }}</div>
            <div><strong>Адрес:</strong><br> г. Москва</div>
            <div><strong>Цена:</strong><br> {{ formatPrice(getServicePrice(booking.service_id)) }}</div>
          </div>

          <div class="booking-actions">
            <button class="details-btn" @click="viewDetails(booking)">Подробнее</button>
            <button 
              v-if="booking.status === 'pending'" 
              class="cancel-btn" 
              @click="cancelBooking(booking.id)"
              :disabled="cancellingId === booking.id"
            >
              {{ cancellingId === booking.id ? 'Отмена...' : 'Отменить' }}
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
const cancellingId = ref(null);
const bookings = ref([]);

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

onMounted(async () => {
  await loadBookings();
});

const loadBookings = async () => {
  loading.value = true;
  error.value = '';

  try {
    const token = localStorage.getItem('access_token');
    const response = await fetch(`${API_URL}/bookings/my`, {
      headers: { 'Authorization': `Bearer ${token}` },
    });

    if (!response.ok) throw new Error('Ошибка загрузки записей');
    bookings.value = await response.json();
  } catch (err) {
    error.value = err.message;
  } finally {
    loading.value = false;
  }
};

const cancelBooking = async (bookingId) => {
  if (!confirm('Отменить запись?')) return;
  
  cancellingId.value = bookingId;

  try {
    const token = localStorage.getItem('access_token');
    const response = await fetch(`${API_URL}/bookings/${bookingId}/cancel`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
    });

    if (!response.ok) throw new Error('Не удалось отменить запись');
    
    // Обновляем статус локально
    const booking = bookings.value.find(b => b.id === bookingId);
    if (booking) booking.status = 'cancelled';
  } catch (err) {
    error.value = err.message;
  } finally {
    cancellingId.value = null;
  }
};

const viewDetails = (booking) => {
  router.push(`/company/${booking.company_id}?service=${booking.service_id}`);
};

const handleLogout = () => {
  auth.logout();
  router.push('/');
};

// Заглушки для отображения (в реальности загружать из API)
const getCompanyName = (companyId) => {
  const names = { 1: 'AutoFix Service', 2: 'ProCar Service', 3: 'CarMaster' };
  return names[companyId] || `Компания #${companyId}`;
};

const getServiceName = (serviceId) => {
  const names = { 1: 'Замена масла', 2: 'Диагностика', 3: 'Комплексная проверка' };
  return names[serviceId] || `Услуга #${serviceId}`;
};

const getServicePrice = (serviceId) => {
  const prices = { 1: 2000, 2: 1500, 3: 1800 };
  return prices[serviceId] || 0;
};

const getStatusClass = (status) => {
  const map = { pending: 'active', confirmed: 'completed', cancelled: 'cancelled' };
  return map[status] || '';
};

const getStatusText = (status) => {
  const map = { pending: 'Активна', confirmed: 'Завершена', cancelled: 'Отменена' };
  return map[status] || status;
};

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('ru-RU', {
    day: 'numeric', month: 'long', year: 'numeric'
  });
};

const formatTime = (dateString) => {
  return new Date(dateString).toLocaleTimeString('ru-RU', {
    hour: '2-digit', minute: '2-digit'
  });
};

const formatPrice = (price) => {
  return new Intl.NumberFormat('ru-RU').format(price) + ' ₽';
};
</script>

<style scoped>
.bookings-page { font-family: "Segoe UI", Arial, sans-serif; background: #f5f7fa; min-height: 100vh; }
header { background: linear-gradient(135deg, #1e3a8a, #2563eb); color: white; padding: 20px 50px; display: flex; justify-content: space-between; align-items: center; }
.logo { font-size: 22px; font-weight: bold; }
.nav { display: flex; gap: 10px; }
.nav button { padding: 8px 15px; border-radius: 8px; border: none; cursor: pointer; background: white; color: #1e3a8a; font-weight: 500; }
.nav button:hover { background: #f3f4f6; }
.container { width: 1100px; max-width: 95%; margin: 40px auto; }
.page-title { margin-bottom: 30px; color: #1f2937; }
.loading, .empty-state { text-align: center; padding: 60px 20px; color: #6b7280; background: white; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.08); }
.error-message { background: #fef2f2; color: #dc2626; padding: 15px; border-radius: 12px; margin-bottom: 20px; text-align: center; }
.booking-card { background: white; padding: 25px; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.08); margin-bottom: 20px; transition: 0.3s; }
.booking-card:hover { transform: translateY(-5px); border: 2px solid #2563eb; }
.booking-header { display: flex; justify-content: space-between; align-items: center; }
.booking-header h3 { margin-bottom: 5px; color: #111827; }
.booking-header div:last-child { color: #6b7280; font-size: 14px; }
.status { padding: 6px 12px; border-radius: 8px; font-size: 13px; font-weight: 500; }
.status.active { background: #dcfce7; color: #166534; }
.status.completed { background: #e0f2fe; color: #1e40af; }
.status.cancelled { background: #fee2e2; color: #991b1b; }
.booking-info { margin-top: 15px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; font-size: 14px; color: #6b7280; }
.booking-info strong { color: #374151; }
.booking-actions { margin-top: 20px; display: flex; gap: 10px; }
.booking-actions button { padding: 8px 15px; border-radius: 8px; border: none; cursor: pointer; font-weight: 500; transition: background 0.2s; }
.details-btn { background: #2563eb; color: white; }
.details-btn:hover { background: #1e40af; }
.cancel-btn { background: #fee2e2; color: #991b1b; }
.cancel-btn:hover:not(:disabled) { background: #fecaca; }
.cancel-btn:disabled { background: #fca5a5; cursor: not-allowed; }
@media (max-width: 768px) { .booking-info { grid-template-columns: repeat(2, 1fr); } header { padding: 15px 20px; } }
</style>