<template>
  <div class="dashboard-page">
    <header>
      <div class="logo">AutoBooking</div>
      <div class="nav">
        <button type="button" @click="router.push('/company/services')">Услуги</button>
        <button type="button" @click="router.push('/company/calendar')">Календарь</button>
        <button type="button" @click="handleLogout">Выйти</button>
      </div>
    </header>

    <div class="container">
      <h2 class="page-title">Записи клиентов</h2>

      <div v-if="needsCompany" class="create-company-card">
        <h3>Создайте карточку компании</h3>
        <p class="muted">
          После регистрации владельца нужно заполнить данные компании — так вы появитесь в поиске.
        </p>
        <form class="company-form" @submit.prevent="createCompany">
          <input v-model="createForm.name" type="text" placeholder="Название *" required />
          <textarea
            v-model="createForm.description"
            rows="2"
            placeholder="Описание"
          ></textarea>
          <input v-model="createForm.category" type="text" placeholder="Категория" />
          <input v-model="createForm.city" type="text" placeholder="Город" />
          <input v-model="createForm.address" type="text" placeholder="Адрес" />
          <input v-model="createForm.phone" type="text" placeholder="Телефон" />
          <button type="submit" class="primary" :disabled="creatingCompany">
            {{ creatingCompany ? 'Создание...' : 'Создать компанию' }}
          </button>
        </form>
        <div v-if="createError" class="error-message">{{ createError }}</div>
      </div>

      <template v-else>
        <div v-if="loading" class="loading">Загрузка...</div>
        <div v-else-if="error" class="error-message">{{ error }}</div>
        <div v-else-if="bookings.length === 0" class="empty-state">Пока нет записей</div>

        <div v-else class="bookings-list">
          <div v-for="booking in bookings" :key="booking.id" class="booking-card">
            <div class="booking-header">
              <div>
                <h3>Клиент #{{ booking.user_id }}</h3>
                <div>Запись #{{ booking.id }} · Услуга #{{ booking.service_id }}</div>
              </div>
              <div :class="['status', statusClass(booking.status)]">
                {{ statusText(booking.status) }}
              </div>
            </div>

            <div class="booking-info">
              <div>
                <strong>Дата:</strong>
                <br />
                {{ formatDate(booking.start_at) }}
              </div>
              <div>
                <strong>Время:</strong>
                <br />
                {{ formatTime(booking.start_at) }}
              </div>
              <div v-if="booking.notes">
                <strong>Заметка:</strong>
                <br />
                {{ booking.notes }}
              </div>
              <div>
                <strong>Создано:</strong>
                <br />
                {{ formatDate(booking.created_at) }}
              </div>
            </div>

            <div class="booking-actions">
              <button
                v-if="booking.status === 'pending'"
                type="button"
                class="confirm-btn"
                :disabled="processingId === booking.id"
                @click="confirmBooking(booking.id)"
              >
                {{ processingId === booking.id ? 'Обработка...' : 'Подтвердить' }}
              </button>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';

import { API_URL } from '@/config';
import { formatApiError } from '@/utils/apiError';
import { useAuth } from '@/composables/useAuth';

const router = useRouter();
const auth = useAuth();

const loading = ref(true);
const error = ref('');
const processingId = ref(null);
const bookings = ref([]);
const companyId = ref(null);
const needsCompany = ref(false);

const creatingCompany = ref(false);
const createError = ref('');
const createForm = reactive({
  name: '',
  description: '',
  category: '',
  city: '',
  address: '',
  phone: '',
});

onMounted(async () => {
  await initCompanyData();
});

async function initCompanyData() {
  loading.value = true;
  error.value = '';
  needsCompany.value = false;

  try {
    if (!auth.isAuthenticated()) {
      router.push('/login/company');
      return;
    }

    await loadMyCompany();

    if (needsCompany.value) {
      loading.value = false;
      return;
    }

    if (companyId.value) {
      await loadBookings();
    }
  } catch (err) {
    error.value = err.message || 'Ошибка загрузки данных';
  } finally {
    loading.value = false;
  }
}

async function loadMyCompany() {
  const token = localStorage.getItem('access_token');
  const response = await fetch(`${API_URL}/owner/company`, {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (response.status === 404) {
    needsCompany.value = true;
    companyId.value = null;
    return;
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(formatApiError(data));
  }

  companyId.value = data.id;
  needsCompany.value = false;
}

async function createCompany() {
  creatingCompany.value = true;
  createError.value = '';

  try {
    const token = localStorage.getItem('access_token');
    const body = {
      name: createForm.name.trim(),
      description: createForm.description.trim() || null,
      category: createForm.category.trim() || null,
      city: createForm.city.trim() || null,
      address: createForm.address.trim() || null,
      phone: createForm.phone.trim() || null,
    };

    const response = await fetch(`${API_URL}/owner/company`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(body),
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(formatApiError(data));
    }

    companyId.value = data.id;
    needsCompany.value = false;
    createForm.name = '';
    createForm.description = '';
    createForm.category = '';
    createForm.city = '';
    createForm.address = '';
    createForm.phone = '';
    await loadBookings();
  } catch (err) {
    createError.value = err.message;
  } finally {
    creatingCompany.value = false;
  }
}

async function loadBookings() {
  if (!companyId.value) {
    error.value = 'Компания не найдена';
    return;
  }

  loading.value = true;
  error.value = '';

  try {
    const token = localStorage.getItem('access_token');
    const response = await fetch(`${API_URL}/owner/company/${companyId.value}/bookings`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(formatApiError(data));
    }

    bookings.value = Array.isArray(data) ? data : [];
  } catch (err) {
    error.value = err.message;
    bookings.value = [];
  } finally {
    loading.value = false;
  }
}

async function confirmBooking(bookingId) {
  processingId.value = bookingId;

  try {
    const token = localStorage.getItem('access_token');
    const response = await fetch(`${API_URL}/owner/bookings/${bookingId}/confirm`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(formatApiError(data));
    }

    const booking = bookings.value.find((b) => b.id === bookingId);
    if (booking) booking.status = 'confirmed';
  } catch (err) {
    error.value = err.message;
  } finally {
    processingId.value = null;
  }
}

function handleLogout() {
  auth.logout();
}

function statusClass(status) {
  const map = { pending: 'active', confirmed: 'completed', cancelled: 'cancelled' };
  return map[status] || '';
}

function statusText(status) {
  const map = {
    pending: 'Ожидает подтверждения',
    confirmed: 'Подтверждена',
    cancelled: 'Отменена',
  };
  return map[status] || status;
}

function formatDate(dateString) {
  return new Date(dateString).toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
}

function formatTime(dateString) {
  return new Date(dateString).toLocaleTimeString('ru-RU', {
    hour: '2-digit',
    minute: '2-digit',
  });
}
</script>

<style scoped>
.dashboard-page {
  font-family: 'Segoe UI', Arial, sans-serif;
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

.create-company-card {
  background: white;
  padding: 30px;
  border-radius: 20px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08);
}

.create-company-card h3 {
  margin-bottom: 10px;
  color: #111827;
}

.muted {
  color: #6b7280;
  margin-bottom: 20px;
}

.company-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.company-form input,
.company-form textarea {
  padding: 12px;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  font-size: 14px;
  font-family: inherit;
}

.primary {
  padding: 12px;
  border-radius: 10px;
  border: none;
  background: #16a34a;
  color: white;
  font-weight: 500;
  cursor: pointer;
}

.primary:hover:not(:disabled) {
  background: #15803d;
}

.primary:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.loading,
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #6b7280;
  background: white;
  border-radius: 20px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08);
}

.error-message {
  background: #fef2f2;
  color: #dc2626;
  padding: 15px;
  border-radius: 12px;
  margin-top: 16px;
  text-align: center;
}

.booking-card {
  background: white;
  padding: 25px;
  border-radius: 20px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08);
  margin-bottom: 20px;
  transition: 0.3s;
}

.booking-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.12);
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
  background: #fef3c7;
  color: #92400e;
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
  grid-template-columns: repeat(4, 1fr);
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

.confirm-btn {
  padding: 8px 15px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  font-weight: 500;
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
