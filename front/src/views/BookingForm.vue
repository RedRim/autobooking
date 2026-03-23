<template>
  <div class="booking-page">
    <header>
      <div class="logo">AutoBooking</div>
      <div class="nav">
        <button type="button" @click="router.push('/bookings')">Мои записи</button>
        <button type="button" @click="router.back()">Назад</button>
      </div>
    </header>

    <div class="container">
      <div v-if="pageLoading" class="loading">Загрузка...</div>
      <div v-else-if="pageError" class="error-message">{{ pageError }}</div>

      <div v-else class="booking-card">
        <h1>Запись на услугу</h1>

        <div class="service-info">
          <strong>Компания:</strong>
          {{ company?.name || '—' }}
          <br />
          <strong>Услуга:</strong>
          {{ service?.name || '—' }}
          <br />
          <strong>Стоимость:</strong>
          {{ formatPrice(service?.price) }}
          <br />
          <strong>Длительность:</strong>
          {{ service?.duration_minutes }} минут
          <div v-if="service?.description" class="service-description">
            <strong>Описание:</strong>
            <div class="service-description-text">{{ service.description }}</div>
          </div>
        </div>

        <div class="date-picker">
          <strong>Выберите дату:</strong>
          <br />
          <br />
          <input v-model="selectedDate" type="date" :min="minDate" @change="loadSlots" />
        </div>

        <div v-if="loadingSlots" class="loading">Загрузка доступного времени...</div>
        <div v-else-if="slotsError" class="error-message">{{ slotsError }}</div>
        <div v-else-if="availableSlots.length === 0 && selectedDate" class="empty-state">
          На эту дату нет свободных слотов. Выберите другой день.
        </div>
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

        <div class="notes-section">
          <label>Заметка для мастера (необязательно)</label>
          <textarea
            v-model="notes"
            placeholder="Например: левша, аллергия на краску..."
            rows="3"
          ></textarea>
        </div>

        <button
          type="button"
          class="book-btn"
          :disabled="!selectedSlot || bookingLoading"
          @click="createBooking"
        >
          {{ bookingLoading ? 'Создание записи...' : 'Подтвердить запись' }}
        </button>

        <div v-if="bookingError" class="error-message">{{ bookingError }}</div>
        <div v-if="bookingSuccess" class="success-message">
          Запись создана!
          <router-link to="/bookings">Мои записи</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { API_URL } from '@/config';
import { formatApiError } from '@/utils/apiError';

const router = useRouter();
const route = useRoute();

const serviceId = computed(() => {
  const fromParam = route.params.serviceId;
  const n = Number.parseInt(String(fromParam), 10);
  if (Number.isFinite(n)) return n;
  const q = route.query.service;
  const m = Number.parseInt(String(q), 10);
  return Number.isFinite(m) ? m : null;
});

const companyId = computed(() => {
  const q = route.query.company;
  if (q === undefined || q === null || q === '') return null;
  const n = Number.parseInt(String(q), 10);
  return Number.isFinite(n) ? n : null;
});

const pageLoading = ref(true);
const pageError = ref('');
const loadingSlots = ref(false);
const bookingLoading = ref(false);
const slotsError = ref('');
const bookingError = ref('');
const bookingSuccess = ref(false);

const company = ref(null);
const service = ref(null);
const selectedDate = ref('');
const availableSlots = ref([]);
const selectedSlot = ref(null);
const notes = ref('');

const minDate = computed(() => {
  const today = new Date();
  return today.toISOString().split('T')[0];
});

onMounted(async () => {
  await loadData();
  selectedDate.value = minDate.value;
  await loadSlots();
});

async function loadData() {
  pageLoading.value = true;
  pageError.value = '';

  if (!serviceId.value) {
    pageError.value = 'Не указана услуга';
    pageLoading.value = false;
    return;
  }

  try {
    let cid = companyId.value;

    if (!cid) {
      pageError.value = 'Укажите компанию в ссылке (параметр company).';
      pageLoading.value = false;
      return;
    }

    const companyRes = await fetch(`${API_URL}/companies/${cid}`);
    const data = await companyRes.json().catch(() => ({}));

    if (!companyRes.ok) {
      throw new Error(formatApiError(data));
    }

    company.value = data;
    const found = (data.services || []).find((s) => s.id === serviceId.value && s.is_active);
    service.value = found || null;

    if (!service.value) {
      pageError.value = 'Услуга не найдена или недоступна.';
    }
  } catch (err) {
    pageError.value = err.message || 'Ошибка загрузки';
  } finally {
    pageLoading.value = false;
  }
}

async function loadSlots() {
  if (!serviceId.value || !selectedDate.value) return;

  loadingSlots.value = true;
  slotsError.value = '';
  selectedSlot.value = null;

  try {
    const response = await fetch(
      `${API_URL}/services/${serviceId.value}/slots?date=${selectedDate.value}`,
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
  selectedSlot.value = slot;
}

async function createBooking() {
  if (!selectedSlot.value) return;

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
        service_id: serviceId.value,
        start_at: selectedSlot.value.start_at,
        notes: notes.value.trim() ? notes.value.trim() : null,
      }),
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(formatApiError(data));
    }

    bookingSuccess.value = true;
    selectedSlot.value = null;
    notes.value = '';
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
.booking-page {
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

.booking-card {
  background: white;
  padding: 30px;
  border-radius: 20px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08);
}

.booking-card h1 {
  margin-bottom: 15px;
  color: #111827;
}

.service-info {
  background: #f9fafb;
  padding: 15px;
  border-radius: 12px;
  margin-bottom: 20px;
  color: #6b7280;
  line-height: 1.6;
}

.service-info strong {
  color: #374151;
}

.service-description {
  margin-top: 10px;
}

.service-description-text {
  margin-top: 6px;
  color: #6b7280;
  line-height: 1.4;
}

.date-picker {
  margin: 20px 0;
}

.date-picker input {
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

.notes-section {
  margin: 25px 0;
}

.notes-section label {
  display: block;
  margin-bottom: 8px;
  color: #374151;
  font-weight: 500;
}

.notes-section textarea {
  width: 100%;
  padding: 12px;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  font-size: 14px;
  resize: none;
  font-family: inherit;
}

.notes-section textarea:focus {
  outline: none;
  border-color: #2563eb;
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

.loading,
.empty-state {
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
  .slots {
    grid-template-columns: repeat(3, 1fr);
  }

  header {
    padding: 15px 20px;
  }
}
</style>
