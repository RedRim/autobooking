<template>
  <div class="dashboard-page">
    <header>
      <div class="logo">AutoBooking</div>
      <div class="nav">
        <button type="button" @click="router.push('/company/profile')" :disabled="!companyId">
          Профиль
        </button>
        <button type="button" @click="router.push('/company/services')" :disabled="!companyId">
          Услуги
        </button>
        <button type="button" @click="router.push('/company/calendar')" :disabled="!companyId">
          Календарь
        </button>
        <button type="button" @click="handleLogout">Выйти</button>
      </div>
    </header>

    <div class="container">
      <h2 class="page-title">Панель владельца</h2>

      <div v-if="needsCompany" class="create-company-card">
        <template v-if="companyRequest">
          <h3>Заявка отправлена</h3>
          <p class="muted">
            Статус:
            <strong>{{ requestStatusText(companyRequest.status) }}</strong>
          </p>
          <div class="request-summary">
            <div><strong>Название:</strong> {{ companyRequest.name }}</div>
            <div><strong>Категория:</strong> {{ companyRequest.requested_category }}</div>
            <div><strong>Город:</strong> {{ companyRequest.city }}</div>
            <div><strong>Телефон:</strong> {{ companyRequest.phone }}</div>
          </div>
          <p class="muted" v-if="companyRequest.status === 'pending'">
            Менеджер проверит заявку и создаст карточку компании после одобрения.
          </p>
          <button class="primary" type="button" @click="initCompanyData">Обновить статус</button>
        </template>

        <template v-else>
          <h3>Подайте заявку на создание компании</h3>
          <p class="muted">
            После одобрения менеджером компания появится в системе, и вы сможете настроить услуги и
            расписание.
          </p>
          <form class="company-form" @submit.prevent="createCompanyRequest">
            <input v-model="createForm.name" type="text" placeholder="Название компании *" required />

            <div class="category-field">
              <input
                v-model="createForm.category"
                type="text"
                placeholder="Категория *"
                required
                @input="onCategoryInput"
                @focus="onCategoryFocus"
                @blur="closeSuggestions"
              />
              <div v-if="categoryLoading" class="hint">Поиск категорий...</div>
              <div v-else-if="categoryOptions.length > 0" class="suggestions">
                <button
                  v-for="option in categoryOptions"
                  :key="option.id"
                  type="button"
                  class="suggestion-item"
                  @mousedown.prevent="pickCategory(option.name)"
                >
                  {{ option.name }}
                </button>
              </div>
            </div>

            <div class="city-field">
              <input
                v-model="createForm.city"
                type="text"
                placeholder="Город *"
                required
                @input="onCityInput"
                @focus="onCityFocus"
                @blur="closeCitySuggestions"
              />
              <div v-if="cityLoading" class="hint">Поиск городов...</div>
              <div v-else-if="cityOptions.length > 0" class="suggestions">
                <button
                  v-for="option in cityOptions"
                  :key="option.name"
                  type="button"
                  class="suggestion-item"
                  @mousedown.prevent="pickCity(option.name)"
                >
                  {{ option.name }}
                </button>
              </div>
            </div>
            <input
              v-model="createForm.phone"
              type="tel"
              placeholder="Телефон компании *"
              required
            />
            <button type="submit" class="primary" :disabled="creatingRequest">
              {{ creatingRequest ? 'Отправка...' : 'Отправить заявку' }}
            </button>
          </form>
          <div v-if="createError" class="error-message">{{ createError }}</div>
        </template>
      </div>

      <template v-else>
        <h2 class="section-title">Записи клиентов</h2>
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

import { useAuth } from '@/composables/useAuth';
import { formatApiError } from '@/utils/apiError';

const router = useRouter();
const auth = useAuth();

const loading = ref(true);
const error = ref('');
const processingId = ref(null);
const bookings = ref([]);
const companyId = ref(null);
const needsCompany = ref(false);

const creatingRequest = ref(false);
const createError = ref('');
const createForm = reactive({
  name: '',
  category: '',
  city: '',
  phone: '',
});
const companyRequest = ref(null);

const categoryLoading = ref(false);
const categoryOptions = ref([]);
let categoryTimer = null;
const cityLoading = ref(false);
const cityOptions = ref([]);
let cityTimer = null;

onMounted(async () => {
  await initCompanyData();
});

async function initCompanyData() {
  loading.value = true;
  error.value = '';
  needsCompany.value = false;
  companyRequest.value = null;

  try {
    if (!auth.isAuthenticated()) {
      router.push('/login/company');
      return;
    }

    await loadMyCompany();
    if (needsCompany.value) {
      await loadMyCompanyRequest();
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
  const response = await auth.authFetch('/owner/company');
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

async function loadMyCompanyRequest() {
  const response = await auth.authFetch('/owner/company-request');
  if (response.status === 404) {
    companyRequest.value = null;
    return;
  }

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(formatApiError(data));
  }
  companyRequest.value = data;
}

async function createCompanyRequest() {
  creatingRequest.value = true;
  createError.value = '';

  try {
    const response = await auth.authFetch('/owner/company-request', {
      method: 'POST',
      body: JSON.stringify({
        name: createForm.name.trim(),
        category: createForm.category.trim(),
        city: createForm.city.trim(),
        phone: createForm.phone.trim(),
      }),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(formatApiError(data));
    }
    companyRequest.value = data;
    createForm.name = '';
    createForm.category = '';
    createForm.city = '';
    createForm.phone = '';
    categoryOptions.value = [];
  } catch (err) {
    createError.value = err.message || 'Не удалось отправить заявку';
  } finally {
    creatingRequest.value = false;
  }
}

function pickCategory(value) {
  createForm.category = value;
  categoryOptions.value = [];
}

function closeSuggestions() {
  window.setTimeout(() => {
    categoryOptions.value = [];
  }, 100);
}

function pickCity(value) {
  createForm.city = value;
  cityOptions.value = [];
}

function closeCitySuggestions() {
  window.setTimeout(() => {
    cityOptions.value = [];
  }, 100);
}

function onCategoryInput() {
  if (categoryTimer) {
    clearTimeout(categoryTimer);
  }
  categoryTimer = setTimeout(() => {
    loadCategorySuggestions(createForm.category.trim());
  }, 250);
}

async function onCategoryFocus() {
  if (categoryOptions.value.length > 0) {
    return;
  }
  await loadCategorySuggestions(createForm.category.trim());
}

async function loadCategorySuggestions(query = '') {
  categoryLoading.value = true;
  try {
    const params = new URLSearchParams({ limit: '50' });
    if (query) {
      params.set('search', query);
    }
    const response = await auth.authFetch(
      `/categories?${params.toString()}`,
      {},
      { redirectOn401: false },
    );
    if (!response.ok) {
      categoryOptions.value = [];
      return;
    }
    const data = await response.json().catch(() => []);
    categoryOptions.value = Array.isArray(data) ? data : [];
  } finally {
    categoryLoading.value = false;
  }
}

function onCityInput() {
  if (cityTimer) {
    clearTimeout(cityTimer);
  }
  cityTimer = setTimeout(() => {
    loadCitySuggestions(createForm.city.trim());
  }, 250);
}

async function onCityFocus() {
  if (cityOptions.value.length > 0) {
    return;
  }
  await loadCitySuggestions(createForm.city.trim());
}

async function loadCitySuggestions(query = '') {
  cityLoading.value = true;
  try {
    const params = new URLSearchParams();
    if (query) {
      params.set('search', query);
    }
    const response = await auth.authFetch(
      `/cities?${params.toString()}`,
      {},
      { redirectOn401: false },
    );
    if (!response.ok) {
      cityOptions.value = [];
      return;
    }
    const data = await response.json().catch(() => []);
    cityOptions.value = Array.isArray(data) ? data : [];
  } finally {
    cityLoading.value = false;
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
    const response = await auth.authFetch(`/owner/company/${companyId.value}/bookings`);
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
    const response = await auth.authFetch(`/owner/bookings/${bookingId}/confirm`, {
      method: 'POST',
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(formatApiError(data));
    }
    const booking = bookings.value.find((item) => item.id === bookingId);
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

function requestStatusText(requestStatus) {
  const map = {
    pending: 'На модерации',
    approved: 'Одобрена',
    rejected: 'Отклонена',
  };
  return map[requestStatus] || requestStatus;
}

function statusClass(statusValue) {
  const map = { pending: 'active', confirmed: 'completed', cancelled: 'cancelled' };
  return map[statusValue] || '';
}

function statusText(statusValue) {
  const map = {
    pending: 'Ожидает подтверждения',
    confirmed: 'Подтверждена',
    cancelled: 'Отменена',
  };
  return map[statusValue] || statusValue;
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
}

.nav button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.container {
  width: 1100px;
  max-width: 95%;
  margin: 40px auto;
}

.page-title,
.section-title {
  margin-bottom: 24px;
  color: #1f2937;
}

.create-company-card {
  background: white;
  padding: 30px;
  border-radius: 20px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08);
}

.muted {
  color: #6b7280;
  margin-bottom: 12px;
}

.request-summary {
  background: #f9fafb;
  border-radius: 12px;
  padding: 12px;
  display: grid;
  gap: 6px;
  margin-bottom: 12px;
}

.company-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.company-form input {
  width: 100%;
  box-sizing: border-box;
  padding: 12px;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  font-size: 14px;
}

.category-field {
  position: relative;
}

.city-field {
  position: relative;
}

.hint {
  margin-top: 6px;
  font-size: 13px;
  color: #6b7280;
}

.suggestions {
  margin-top: 6px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  overflow: hidden;
  background: white;
  max-height: 220px;
  overflow-y: auto;
}

.suggestion-item {
  width: 100%;
  text-align: left;
  border: none;
  padding: 9px 12px;
  background: white;
  cursor: pointer;
}

.suggestion-item:hover {
  background: #f3f4f6;
}

.primary {
  width: 100%;
  box-sizing: border-box;
  padding: 12px;
  border-radius: 10px;
  border: none;
  background: #16a34a;
  color: white;
  font-weight: 500;
  cursor: pointer;
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
}

.booking-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.booking-info {
  margin-top: 15px;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  font-size: 14px;
  color: #6b7280;
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

.booking-actions {
  margin-top: 20px;
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

@media (max-width: 768px) {
  header {
    padding: 15px 20px;
  }

  .booking-info {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
