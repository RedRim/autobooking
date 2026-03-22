<template>
  <div class="booking-page">
    <header>
      <div class="logo">AutoBooking</div>
      <div class="nav">
        <button @click="router.push('/bookings')">Мои записи</button>
        <button @click="router.back()">Назад</button>
      </div>
    </header>

    <div class="container">
      <div class="booking-card">
        <h1>Запись на услугу</h1>
        
        <div class="service-info">
          <strong>Компания:</strong> {{ company?.name || 'Загрузка...' }}<br>
          <strong>Услуга:</strong> {{ service?.name || 'Загрузка...' }}<br>
          <strong>Стоимость:</strong> {{ formatPrice(service?.price) }}<br>
          <strong>Длительность:</strong> {{ service?.duration_minutes }} минут
        </div>

        <!-- Выбор даты -->
        <div class="date-picker">
          <strong>Выберите дату:</strong><br><br>
          <input type="date" v-model="selectedDate" :min="minDate" @change="loadSlots" />
        </div>

        <!-- Слоты времени -->
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
            @click="selectSlot(slot)"
          >
            {{ formatSlotTime(slot.start_at) }}
          </div>
        </div>

        <!-- Заметка -->
        <div class="notes-section">
          <label>Заметка для мастера (необязательно)</label>
          <textarea 
            v-model="notes" 
            placeholder="Например: левша, аллергия на краску..."
            rows="3"
          ></textarea>
        </div>

        <!-- Кнопка записи -->
        <button 
          class="book-btn" 
          @click="createBooking"
          :disabled="!selectedSlot || bookingLoading"
        >
          {{ bookingLoading ? 'Создание записи...' : 'Подтвердить запись' }}
        </button>

        <div v-if="bookingError" class="error-message">{{ bookingError }}</div>
        <div v-if="bookingSuccess" class="success-message">
          ✅ Запись создана! <router-link to="/bookings">Перейти к моим записям</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useAuth } from '@/composables/useAuth';

const router = useRouter();
const route = useRoute();
const auth = useAuth();

const serviceId = ref(parseInt(route.params.serviceId) || route.query.service);
const companyId = ref(parseInt(route.query.company) || 1);

const loading = ref(true);
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

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const minDate = computed(() => {
  const today = new Date();
  return today.toISOString().split('T')[0];
});

onMounted(async () => {
  await loadData();
  selectedDate.value = minDate.value;
  await loadSlots();
});

const loadData = async () => {
  loading.value = true;
  try {
    // Загружаем данные компании и услуги
    const [companyRes, serviceRes] = await Promise.all([
      fetch(`${API_URL}/companies/${companyId.value}`).catch(() => null),
      fetch(`${API_URL}/services/${serviceId.value}`).catch(() => null),
    ]);

    if (companyRes?.ok) company.value = await companyRes.json();
    if (serviceRes?.ok) service.value = await serviceRes.json();
  } catch (err) {
    console.error('Ошибка загрузки данных:', err);
  } finally {
    loading.value = false;
  }
};

const loadSlots = async () => {
  if (!serviceId.value || !selectedDate.value) return;
  
  loadingSlots.value = true;
  slotsError.value = '';
  selectedSlot.value = null;
  
  try {
    const response = await fetch(
      `${API_URL}/services/${serviceId.value}/slots?date=${selectedDate.value}`
    );
    
    if (!response.ok) throw new Error('Не удалось загрузить доступное время');
    availableSlots.value = await response.json();
  } catch (err) {
    slotsError.value = err.message;
  } finally {
    loadingSlots.value = false;
  }
};

const selectSlot = (slot) => {
  selectedSlot.value = slot;
};

const createBooking = async () => {
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
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        service_id: serviceId.value,
        start_at: selectedSlot.value.start_at,
        notes: notes.value || null,
      }),
    });

    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.detail || 'Ошибка создания записи');
    }

    bookingSuccess.value = true;
    // Очищаем форму
    selectedSlot.value = null;
    notes.value = '';
  } catch (err) {
    bookingError.value = err.message;
  } finally {
    bookingLoading.value = false;
  }
};

const formatPrice = (price) => {
  if (!price) return '0 ₽';
  return new Intl.NumberFormat('ru-RU').format(price) + ' ₽';
};

const formatSlotTime = (dateString) => {
  return new Date(dateString).toLocaleTimeString('ru-RU', {
    hour: '2-digit', minute: '2-digit'
  });
};
</script>

<style scoped>
.booking-page { font-family: "Segoe UI", Arial, sans-serif; background: #f5f7fa; min-height: 100vh; }
header { background: linear-gradient(135deg, #1e3a8a, #2563eb); color: white; padding: 20px 50px; display: flex; justify-content: space-between; align-items: center; }
.logo { font-size: 22px; font-weight: bold; }
.nav { display: flex; gap: 10px; }
.nav button { padding: 8px 15px; border-radius: 8px; border: none; cursor: pointer; background: white; color: #1e3a8a; font-weight: 500; }
.nav button:hover { background: #f3f4f6; }
.container { width: 1100px; max-width: 95%; margin: 40px auto; }
.booking-card { background: white; padding: 30px; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.08); }
.booking-card h1 { margin-bottom: 15px; color: #111827; }
.service-info { background: #f9fafb; padding: 15px; border-radius: 12px; margin-bottom: 20px; color: #6b7280; line-height: 1.6; }
.service-info strong { color: #374151; }
.date-picker { margin: 20px 0; }
.date-picker input { padding: 10px; border-radius: 8px; border: 1px solid #d1d5db; font-size: 15px; }
.slots { margin-top: 25px; display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; }
.slot { background: #e0f2fe; padding: 10px; text-align: center; border-radius: 8px; cursor: pointer; transition: 0.3s; }
.slot:hover { background: #2563eb; color: white; }
.slot.active { background: #2563eb; color: white; }
.notes-section { margin: 25px 0; }
.notes-section label { display: block; margin-bottom: 8px; color: #374151; font-weight: 500; }
.notes-section textarea { width: 100%; padding: 12px; border-radius: 10px; border: 1px solid #e5e7eb; font-size: 14px; resize: none; font-family: inherit; }
.notes-section textarea:focus { outline: none; border-color: #2563eb; }
.book-btn { margin-top: 25px; padding: 12px; border-radius: 10px; border: none; background: #2563eb; color: white; font-weight: 500; cursor: pointer; width: 100%; transition: background 0.2s; }
.book-btn:hover:not(:disabled) { background: #1e40af; }
.book-btn:disabled { background: #93c5fd; cursor: not-allowed; }
.loading, .empty-state { text-align: center; padding: 20px; color: #6b7280; }
.error-message { background: #fef2f2; color: #dc2626; padding: 12px; border-radius: 8px; margin: 15px 0; text-align: center; }
.success-message { background: #dcfce7; color: #166534; padding: 12px; border-radius: 8px; margin: 15px 0; text-align: center; }
.success-message a { color: #15803d; font-weight: 500; }
@media (max-width: 768px) { .slots { grid-template-columns: repeat(3, 1fr); } header { padding: 15px 20px; } }
</style>