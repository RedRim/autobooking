<template>
  <div class="company-page">
    <header>
      <div class="logo">AutoBooking</div>
      <div class="nav">
        <button type="button" @click="goDashboard">Личный кабинет</button>
        <button type="button" @click="router.back()">Назад</button>
      </div>
    </header>

    <div class="container">
      <div v-if="loading" class="loading">Загрузка...</div>
      <div v-else-if="pageError" class="error-message">{{ pageError }}</div>

      <template v-else>
        <div class="company-card">
          <div class="company-header">
            <div>
              <h1>{{ company?.name }}</h1>
              <div class="muted">{{ company?.category || 'Категория не указана' }}</div>
            </div>
          </div>
          <div class="company-description">
            {{ company?.description || 'Описание не указано.' }}
          </div>
          <div class="info-grid">
            <div class="info-box">
              <strong>Адрес</strong>
              <br />
              {{ company?.address || '—' }}
            </div>
            <div class="info-box">
  <strong>График</strong>
  <div class="schedule-list">
    <div v-for="(day, idx) in scheduleList" :key="idx" class="schedule-item">
      {{ day }}
    </div>
  </div>
</div>
            <div class="info-box">
              <strong>Телефон</strong>
              <br />
              {{ company?.phone || '—' }}
            </div>
          </div>
        </div>

        <div class="section">
          <h2>Доступные услуги</h2>
          <div v-if="loadingServices" class="loading">Загрузка услуг...</div>
          <div v-else-if="services.length === 0" class="muted">Нет активных услуг.</div>
          <div v-else class="services">
            <div
              v-for="svc in services"
              :key="svc.id"
              class="service-card"
              :class="{ selected: selectedService?.id === svc.id }"
              role="button"
              tabindex="0"
              @click="selectService(svc)"
              @keyup.enter="selectService(svc)"
            >
              <strong>{{ svc.name }}</strong>
              <span>{{ formatPrice(svc.price) }} · {{ svc.duration_minutes }} мин</span>
              <!-- <div v-if="svc.description" class="service-description">
                {{ svc.description }}
              </div> -->
            </div>
          </div>
        </div>

        <div v-if="selectedService" class="section">

          <div v-if="selectedService.description" class="selected-service-description">
            <strong>Описание:</strong>
            <div class="service-description">{{ selectedService.description }}</div>
          </div>

          <h2>Выберите время</h2>

          <p v-if="!isLoggedIn" class="hint">
            Чтобы записаться,
            <router-link :to="loginLink">войдите как клиент</router-link>
            .
          </p>

          <div class="date-picker">
            <strong>Дата:</strong>
            <input
              v-model="selectedDate"
              type="date"
              :min="minDate"
              :disabled="!isLoggedIn"
              @change="loadSlots"
            />
          </div>

          <div v-if="loadingSlots" class="loading">Загрузка слотов...</div>
          <div v-else-if="slotsError" class="error-message">{{ slotsError }}</div>
          <div v-else class="slots">
            <div
              v-for="slot in availableSlots"
              :key="slot.start_at"
              class="slot"
              :class="{ active: selectedSlot?.start_at === slot.start_at }"
              role="button"
              tabindex="0"
              @click="selectSlot(slot)"
              @keyup.enter="selectSlot(slot)"
            >
              {{ formatSlotTime(slot.start_at) }}
            </div>
          </div>

          <button
            v-if="selectedSlot && isLoggedIn"
            type="button"
            class="book-btn"
            :disabled="bookingLoading"
            @click="createBooking"
          >
            {{ bookingLoading ? 'Запись...' : 'Записаться' }}
          </button>
        </div>

        <div v-if="bookingError" class="error-message">{{ bookingError }}</div>
        <div v-if="bookingSuccess" class="success-message">
          Запись создана!
          <router-link to="/bookings">Мои записи</router-link>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { API_URL } from '@/config';
import { formatApiError } from '@/utils/apiError';
import { useAuth } from '@/composables/useAuth';

const router = useRouter();
const route = useRoute();
const { isAuthenticated, getUserRole } = useAuth();

const companyId = computed(() => {
  const raw = route.params.id;
  const n = Number.parseInt(String(raw), 10);
  return Number.isFinite(n) ? n : null;
});

const serviceIdFromQuery = computed(() => {
  const raw = route.query.service;
  if (raw === undefined || raw === null || raw === '') return null;
  const n = Number.parseInt(String(raw), 10);
  return Number.isFinite(n) ? n : null;
});

const loading = ref(true);
const loadingServices = ref(true);
const loadingSlots = ref(false);
const bookingLoading = ref(false);
const pageError = ref('');
const slotsError = ref('');
const bookingError = ref('');
const bookingSuccess = ref(false);

const company = ref(null);
const services = ref([]);
const selectedService = ref(null);
const selectedDate = ref('');
const availableSlots = ref([]);
const selectedSlot = ref(null);

const minDate = computed(() => {
  const today = new Date();
  return today.toISOString().split('T')[0];
});

const isLoggedIn = computed(
  () => isAuthenticated() && getUserRole() !== 'company',
);

const loginLink = computed(() => ({
  path: '/login/user',
  query: { redirect: route.fullPath },
}));

const scheduleList = computed(() => {
  const wh = company.value?.working_hours;
  if (!wh || wh.length === 0) return ['Расписание не задано'];

  const dayNames = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];
  return [...wh]
    .sort((a, b) => a.day_of_week - b.day_of_week)
    .map((d) => {
      const label = dayNames[d.day_of_week] ?? d.day_of_week;
      if (!d.is_working) return `${label}: выходной`;
      const start = formatTimeOnly(d.start_time);
      const end = formatTimeOnly(d.end_time);
      return `${label}: ${start}–${end}`;
    });
});

onMounted(async () => {
  if (!companyId.value) {
    pageError.value = 'Некорректный адрес компании';
    loading.value = false;
    return;
  }
  await loadCompany();
  await loadServices();

  if (serviceIdFromQuery.value) {
    const found = services.value.find((s) => s.id === serviceIdFromQuery.value);
    if (found) selectService(found);
  }
});

function formatTimeOnly(t) {
  if (!t) return '';
  const s = String(t);
  return s.length >= 5 ? s.slice(0, 5) : s;
}

function goDashboard() {
  if (!isAuthenticated()) {
    router.push('/login/user');
    return;
  }
  router.push(getUserRole() === 'company' ? '/dashboard/company' : '/dashboard/user');
}

async function loadCompany() {
  pageError.value = '';
  try {
    const response = await fetch(`${API_URL}/companies/${companyId.value}`);
    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(formatApiError(data));
    }

    company.value = data;
  } catch (err) {
    pageError.value = err.message || 'Компания не найдена';
  } finally {
    loading.value = false;
  }
}

async function loadServices() {
  loadingServices.value = true;
  try {
    const response = await fetch(`${API_URL}/companies/${companyId.value}/services`);
    if (response.ok) {
      services.value = await response.json();
    }
  } catch {
    services.value = [];
  } finally {
    loadingServices.value = false;
  }
}

function selectService(svc) {
  selectedService.value = svc;
  selectedSlot.value = null;
  selectedDate.value = minDate.value;
  if (isLoggedIn.value) {
    loadSlots();
  }
}

async function loadSlots() {
  if (!selectedService.value || !selectedDate.value) return;

  loadingSlots.value = true;
  slotsError.value = '';

  try {
    const response = await fetch(
      `${API_URL}/services/${selectedService.value.id}/slots?date=${selectedDate.value}`,
    );
    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(formatApiError(data));
    }

    availableSlots.value = Array.isArray(data) ? data : [];
  } catch (err) {
    slotsError.value = err.message;
    availableSlots.value = [];
  } finally {
    loadingSlots.value = false;
  }
}

function selectSlot(slot) {
  if (!isLoggedIn.value) {
    router.push(loginLink.value);
    return;
  }
  selectedSlot.value = slot;
}

async function createBooking() {
  if (!selectedService.value || !selectedSlot.value) return;

  if (!isLoggedIn.value) {
    router.push(loginLink.value);
    return;
  }

  bookingLoading.value = true;
  bookingError.value = '';
  bookingSuccess.value = false;

  try {
    const token = localStorage.getItem('access_token');
    const response = await fetch(`${API_URL}/bookings`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        service_id: selectedService.value.id,
        start_at: selectedSlot.value.start_at,
        notes: null,
      }),
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(formatApiError(data));
    }

    bookingSuccess.value = true;
    selectedSlot.value = null;
    await loadSlots();
  } catch (err) {
    bookingError.value = err.message;
  } finally {
    bookingLoading.value = false;
  }
}

function formatPrice(price) {
  if (price === null || price === undefined) return 'Цена по запросу';
  return `${new Intl.NumberFormat('ru-RU').format(price)} ₽`;
}

function formatSlotTime(dateString) {
  return new Date(dateString).toLocaleTimeString('ru-RU', {
    hour: '2-digit',
    minute: '2-digit',
  });
}
</script>

<style scoped>
.company-page {
  font-family: 'Segoe UI', Arial, sans-serif;
  background: #f5f7fa;
  min-height: 100vh;
}

header {
  background: linear-gradient(135deg, #1e3a8a, #2563eb);
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
  color: #1e3a8a;
  font-weight: 500;
}

.nav button:hover {
  background: #f3f4f6;
}

.container {
  width: 1100px;
  max-width: 95%;
  margin: 40px auto;
}

.company-card {
  background: white;
  padding: 30px;
  border-radius: 20px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08);
  margin-bottom: 30px;
}

.company-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.company-header h1 {
  margin-bottom: 10px;
  color: #111827;
}

.muted {
  color: #6b7280;
}

.company-description {
  margin-top: 15px;
  color: #6b7280;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-top: 20px;
}

.info-box {
  background: #f9fafb;
  padding: 15px;
  border-radius: 12px;
}

.section {
  margin-top: 40px;
}

.section h2 {
  margin-bottom: 20px;
  color: #1f2937;
}

.services {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.service-card {
  background: white;
  padding: 20px;
  border-radius: 15px;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.05);
  cursor: pointer;
  transition: 0.3s;
  border: 2px solid transparent;
}

.service-card:hover {
  transform: translateY(-5px);
  border-color: #2563eb;
}

.service-card.selected {
  border-color: #2563eb;
  background: #eff6ff;
}

.service-card strong {
  display: block;
  margin-bottom: 8px;
  color: #111827;
}

.service-card span {
  color: #6b7280;
  font-size: 14px;
}

.service-description {
  margin-top: 10px;
  color: #374151;
  font-size: 13px;
  line-height: 1.4;
}

.selected-service-description {
  margin-bottom: 20px;
  padding: 15px;
  border-radius: 12px;
  background: #f9fafb;
  color: #6b7280;
}

.selected-service-description strong {
  color: #374151;
  display: block;
  margin-bottom: 8px;
}

.hint {
  margin-bottom: 12px;
  color: #6b7280;
}

.hint a {
  color: #2563eb;
  font-weight: 500;
}

.date-picker {
  margin: 20px 0;
}

.date-picker input {
  margin-left: 8px;
  padding: 10px;
  border-radius: 8px;
  border: 1px solid #d1d5db;
  font-size: 15px;
}

.slots {
  margin-top: 25px;
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 10px;
}

.slot {
  background: #e0f2fe;
  padding: 10px;
  text-align: center;
  border-radius: 8px;
  cursor: pointer;
  transition: 0.3s;
}

.slot:hover {
  background: #2563eb;
  color: white;
}

.slot.active {
  background: #2563eb;
  color: white;
}

.book-btn {
  margin-top: 25px;
  padding: 12px;
  border-radius: 10px;
  border: none;
  background: #2563eb;
  color: white;
  font-weight: 500;
  cursor: pointer;
  width: 100%;
  transition: background 0.2s;
}

.book-btn:hover:not(:disabled) {
  background: #1e40af;
}

.book-btn:disabled {
  background: #93c5fd;
  cursor: not-allowed;
}

.loading {
  text-align: center;
  padding: 20px;
  color: #6b7280;
}

.error-message {
  background: #fef2f2;
  color: #dc2626;
  padding: 12px;
  border-radius: 8px;
  margin: 15px 0;
  text-align: center;
}

.success-message {
  background: #dcfce7;
  color: #166534;
  padding: 12px;
  border-radius: 8px;
  margin: 15px 0;
  text-align: center;
}

.success-message a {
  color: #15803d;
  font-weight: 500;
}

@media (max-width: 768px) {
  .info-grid {
    grid-template-columns: 1fr;
  }

  .services {
    grid-template-columns: 1fr;
  }

  .slots {
    grid-template-columns: repeat(3, 1fr);
  }

  header {
    padding: 15px 20px;
  }

  .schedule-list {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.schedule-item {
  font-size: 14px;
  color: #374151;
  line-height: 1.4;
}
}
</style>
