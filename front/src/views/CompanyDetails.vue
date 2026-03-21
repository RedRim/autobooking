<template>
  <div class="company-page">
    <header>
      <div class="logo">AutoBooking</div>
      <div class="nav">
        <button @click="router.push('/dashboard/user')">Мои записи</button>
        <button @click="router.back()">Назад</button>
      </div>
    </header>

    <div class="container">
      <!-- Информация о компании -->
      <div class="company-card">
        <div class="company-header">
          <div>
            <h1>{{ company?.name || 'Загрузка...' }}</h1>
            <div>{{ company?.category || 'Категория' }}</div>
          </div>
          <div class="rating">⭐ 4.8</div>
        </div>
        <div class="company-description">{{ company?.description || 'Описание компании' }}</div>
        <div class="info-grid">
          <div class="info-box"><strong>Адрес</strong><br>{{ company?.address || 'г. Москва' }}</div>
          <div class="info-box"><strong>График работы</strong><br>Пн–Пт: 09:00–18:00</div>
          <div class="info-box"><strong>Телефон</strong><br>{{ company?.phone || '+7 (999) 123-45-67' }}</div>
        </div>
      </div>

      <!-- Услуги -->
      <div class="section">
        <h2>Доступные услуги</h2>
        <div v-if="loadingServices" class="loading">Загрузка услуг...</div>
        <div v-else class="services">
          <div 
            v-for="service in services" 
            :key="service.id"
            class="service-card"
            :class="{ selected: selectedService?.id === service.id }"
            @click="selectService(service)"
          >
            <strong>{{ service.name }}</strong>
            <span>{{ formatPrice(service.price) }} • {{ service.duration_minutes }} мин</span>
          </div>
        </div>
      </div>

      <!-- Выбор времени -->
      <div class="section" v-if="selectedService">
        <h2>Выберите время</h2>
        
        <div class="date-picker">
          <strong>Дата:</strong>
          <input type="date" v-model="selectedDate" @change="loadSlots" :min="minDate" />
        </div>

        <div v-if="loadingSlots" class="loading">Загрузка слотов...</div>
        <div v-else-if="slotsError" class="error-message">{{ slotsError }}</div>
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

        <button 
          v-if="selectedSlot" 
          class="book-btn" 
          @click="createBooking"
          :disabled="bookingLoading"
        >
          {{ bookingLoading ? 'Запись...' : 'Записаться' }}
        </button>
      </div>

      <div v-if="bookingError" class="error-message">{{ bookingError }}</div>
      <div v-if="bookingSuccess" class="success-message">✅ Запись создана! <router-link to="/bookings">Мои записи</router-link></div>
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

const companyId = ref(parseInt(route.params.id) || 1);
const serviceIdFromQuery = ref(parseInt(route.query.service) || null);

const loading = ref(true);
const loadingServices = ref(true);
const loadingSlots = ref(false);
const bookingLoading = ref(false);
const error = ref('');
const slotsError = ref('');
const bookingError = ref('');
const bookingSuccess = ref(false);

const company = ref(null);
const services = ref([]);
const selectedService = ref(null);
const selectedDate = ref('');
const availableSlots = ref([]);
const selectedSlot = ref(null);

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const minDate = computed(() => {
  const today = new Date();
  return today.toISOString().split('T')[0];
});

onMounted(async () => {
  await loadCompany();
  await loadServices();
  
  if (serviceIdFromQuery.value) {
    const service = services.value.find(s => s.id === serviceIdFromQuery.value);
    if (service) selectService(service);
  }
});

const loadCompany = async () => {
  try {
    const response = await fetch(`${API_URL}/companies/${companyId.value}`);
    if (!response.ok) throw new Error('Компания не найдена');
    company.value = await response.json();
  } catch (err) {
    error.value = err.message;
  } finally {
    loading.value = false;
  }
};

const loadServices = async () => {
  loadingServices.value = true;
  try {
    const response = await fetch(`${API_URL}/companies/${companyId.value}/services`);
    if (response.ok) {
      services.value = await response.json();
    }
  } catch (err) {
    console.error('Ошибка загрузки услуг:', err);
  } finally {
    loadingServices.value = false;
  }
};

const selectService = (service) => {
  selectedService.value = service;
  selectedSlot.value = null;
  selectedDate.value = minDate.value;
  loadSlots();
};

const loadSlots = async () => {
  if (!selectedService.value || !selectedDate.value) return;
  
  loadingSlots.value = true;
  slotsError.value = '';
  
  try {
    const response = await fetch(
      `${API_URL}/services/${selectedService.value.id}/slots?date=${selectedDate.value}`
    );
    
    if (!response.ok) throw new Error('Не удалось загрузить слоты');
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
  if (!selectedService.value || !selectedSlot.value) return;
  
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
        service_id: selectedService.value.id,
        start_at: selectedSlot.value.start_at,
        notes: '',
      }),
    });

    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.detail || 'Ошибка создания записи');
    }

    bookingSuccess.value = true;
    selectedSlot.value = null;
  } catch (err) {
    bookingError.value = err.message;
  } finally {
    bookingLoading.value = false;
  }
};

const formatPrice = (price) => {
  return new Intl.NumberFormat('ru-RU').format(price) + ' ₽';
};

const formatSlotTime = (dateString) => {
  return new Date(dateString).toLocaleTimeString('ru-RU', {
    hour: '2-digit', minute: '2-digit'
  });
};
</script>

<style scoped>
.company-page { font-family: "Segoe UI", Arial, sans-serif; background: #f5f7fa; min-height: 100vh; }
header { background: linear-gradient(135deg, #1e3a8a, #2563eb); color: white; padding: 20px 50px; display: flex; justify-content: space-between; align-items: center; }
.logo { font-size: 22px; font-weight: bold; }
.nav { display: flex; gap: 10px; }
.nav button { padding: 8px 15px; border-radius: 8px; border: none; cursor: pointer; background: white; color: #1e3a8a; font-weight: 500; }
.nav button:hover { background: #f3f4f6; }
.container { width: 1100px; max-width: 95%; margin: 40px auto; }
.company-card { background: white; padding: 30px; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.08); margin-bottom: 30px; }
.company-header { display: flex; justify-content: space-between; align-items: center; }
.company-header h1 { margin-bottom: 10px; color: #111827; }
.rating { background: #2563eb; color: white; padding: 6px 10px; border-radius: 8px; font-size: 14px; }
.company-description { margin-top: 15px; color: #6b7280; }
.info-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-top: 20px; }
.info-box { background: #f9fafb; padding: 15px; border-radius: 12px; }
.section { margin-top: 40px; }
.section h2 { margin-bottom: 20px; color: #1f2937; }
.services { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }
.service-card { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 5px 15px rgba(0,0,0,0.05); cursor: pointer; transition: 0.3s; border: 2px solid transparent; }
.service-card:hover { transform: translateY(-5px); border-color: #2563eb; }
.service-card.selected { border-color: #2563eb; background: #eff6ff; }
.service-card strong { display: block; margin-bottom: 8px; color: #111827; }
.service-card span { color: #6b7280; font-size: 14px; }
.date-picker { margin: 20px 0; }
.date-picker input { padding: 10px; border-radius: 8px; border: 1px solid #d1d5db; font-size: 15px; }
.slots { margin-top: 25px; display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; }
.slot { background: #e0f2fe; padding: 10px; text-align: center; border-radius: 8px; cursor: pointer; transition: 0.3s; }
.slot:hover { background: #2563eb; color: white; }
.slot.active { background: #2563eb; color: white; }
.book-btn { margin-top: 25px; padding: 12px; border-radius: 10px; border: none; background: #2563eb; color: white; font-weight: 500; cursor: pointer; width: 100%; transition: background 0.2s; }
.book-btn:hover:not(:disabled) { background: #1e40af; }
.book-btn:disabled { background: #93c5fd; cursor: not-allowed; }
.loading { text-align: center; padding: 20px; color: #6b7280; }
.error-message { background: #fef2f2; color: #dc2626; padding: 12px; border-radius: 8px; margin: 15px 0; text-align: center; }
.success-message { background: #dcfce7; color: #166534; padding: 12px; border-radius: 8px; margin: 15px 0; text-align: center; }
.success-message a { color: #15803d; font-weight: 500; }
@media (max-width: 768px) { .info-grid { grid-template-columns: 1fr; } .services { grid-template-columns: 1fr; } .slots { grid-template-columns: repeat(3, 1fr); } header { padding: 15px 20px; } }
</style>