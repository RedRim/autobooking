<template>
  <div class="dashboard-page">
    <header>
      <div class="logo">AutoBooking</div>
      <div class="nav">
        <span class="user-info">{{ user?.email }}</span>
        <button @click="router.push('/bookings')">Мои записи</button>
        <button @click="handleLogout">Выйти</button>
      </div>
    </header>

    <div class="container">
      <h1>Найдите услугу и запишитесь онлайн</h1>
      <div class="subtitle">Быстро. Удобно. Без звонков.</div>

      <!-- Поиск -->
      <div class="search-box">
        <input 
          v-model="search.query" 
          type="text" 
          placeholder="Название компании или услуги"
        />
        <select v-model="search.category">
          <option value="">Все категории</option>
          <option value="auto">Автосервис</option>
          <option value="tire">Шиномонтаж</option>
          <option value="detailing">Детейлинг</option>
          <option value="wash">Мойка</option>
          <option value="barber">Барбершоп</option>
          <option value="beauty">Салон красоты</option>
        </select>
        <button @click="handleSearch" :disabled="loading">
          {{ loading ? 'Поиск...' : 'Найти' }}
        </button>
      </div>

      <!-- Категории -->
      <div class="categories">
        <div 
          v-for="category in categories" 
          :key="category.id"
          class="category-card"
          @click="selectCategory(category.id)"
        >
          <h3>{{ category.name }}</h3>
          <p>{{ category.description }}</p>
        </div>
      </div>

      <!-- Последние записи -->
      <div class="section" v-if="bookings.length > 0">
        <h2>Ближайшие записи</h2>
        <div v-for="booking in bookings" :key="booking.id" class="booking-card">
          <div>
            <strong>{{ booking.company_name }}</strong><br>
            {{ formatDate(booking.start_at) }} • {{ formatTime(booking.start_at) }}
          </div>
          <button 
            class="cancel-btn" 
            @click="cancelBooking(booking.id)"
            :disabled="cancellingId === booking.id"
          >
            {{ cancellingId === booking.id ? 'Отмена...' : 'Отменить' }}
          </button>
        </div>
      </div>

      <div v-if="error" class="error-message">{{ error }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuth } from '@/composables/useAuth';

const router = useRouter();
const { user, logout, fetchCurrentUser } = useAuth();

const loading = ref(false);
const error = ref('');
const cancellingId = ref(null);

const search = reactive({
  query: '',
  category: ''
});

const categories = ref([
  { id: 'auto', name: 'Автосервис', description: 'Ремонт и обслуживание авто' },
  { id: 'tire', name: 'Шиномонтаж', description: 'Замена и балансировка шин' },
  { id: 'detailing', name: 'Детейлинг', description: 'Полировка и уход' },
  { id: 'wash', name: 'Мойка', description: 'Комплексная мойка авто' },
  { id: 'barber', name: 'Барбершоп', description: 'Мужские стрижки' },
  { id: 'beauty', name: 'Салон красоты', description: 'Маникюр, педикюр' },
  { id: 'massage', name: 'Массаж', description: 'Расслабляющий массаж' },
  { id: 'medical', name: 'Медицина', description: 'Здоровье и красота' },
]);

const bookings = ref([
  // Заглушка, позже загрузим из API
  { id: 1, company_name: 'AutoFix Service', start_at: '2026-02-25T14:00:00Z' },
  { id: 2, company_name: 'CleanCar', start_at: '2026-02-28T11:30:00Z' },
]);

onMounted(async () => {
  try {
    await fetchCurrentUser();
    // await loadBookings(); // Раскомментировать при наличии API
  } catch (err) {
    error.value = err.message;
  }
});

const handleSearch = async () => {
  loading.value = true;
  error.value = '';
  
  try {
    // API вызов для поиска
    console.log('Поиск:', search);
    // const response = await fetch(...)
  } catch (err) {
    error.value = 'Ошибка поиска';
  } finally {
    loading.value = false;
  }
};

const selectCategory = (categoryId) => {
  search.category = categoryId;
  handleSearch();
};

const cancelBooking = async (bookingId) => {
  cancellingId.value = bookingId;
  
  try {
    // API вызов для отмены
    bookings.value = bookings.value.filter(b => b.id !== bookingId);
  } catch (err) {
    error.value = 'Не удалось отменить запись';
  } finally {
    cancellingId.value = null;
  }
};

const handleLogout = () => {
  logout();
  router.push('/');
};

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long'
  });
};

const formatTime = (dateString) => {
  return new Date(dateString).toLocaleTimeString('ru-RU', {
    hour: '2-digit',
    minute: '2-digit'
  });
};
</script>

<style scoped>
.dashboard-page {
  font-family: "Segoe UI", Arial, sans-serif;
  background: linear-gradient(135deg, #1e3a8a, #2563eb);
  min-height: 100vh;
  color: #111827;
}

header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 60px;
  color: white;
}

.logo {
  font-size: 22px;
  font-weight: bold;
}

.nav {
  display: flex;
  gap: 15px;
  align-items: center;
}

.user-info {
  font-size: 14px;
  opacity: 0.9;
}

.nav button {
  padding: 8px 16px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  background: white;
  color: #1e3a8a;
  font-weight: 500;
  transition: background 0.2s;
}

.nav button:hover {
  background: #f3f4f6;
}

.container {
  width: 1000px;
  max-width: 95%;
  margin: 40px auto;
  background: white;
  padding: 40px;
  border-radius: 20px;
  box-shadow: 0 20px 40px rgba(0,0,0,0.2);
}

h1 {
  margin-bottom: 10px;
}

.subtitle {
  color: #6b7280;
  margin-bottom: 30px;
}

.search-box {
  display: flex;
  gap: 15px;
  margin-bottom: 40px;
}

.search-box input,
.search-box select {
  flex: 1;
  padding: 12px;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  font-size: 14px;
}

.search-box button {
  padding: 12px 20px;
  border-radius: 10px;
  border: none;
  background: #2563eb;
  color: white;
  cursor: pointer;
  font-weight: 500;
  transition: background 0.2s;
}

.search-box button:hover:not(:disabled) {
  background: #1e40af;
}

.search-box button:disabled {
  background: #93c5fd;
  cursor: not-allowed;
}

.categories {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.category-card {
  padding: 25px;
  background: #f9fafb;
  border-radius: 15px;
  text-align: center;
  cursor: pointer;
  transition: 0.3s;
  border: 2px solid transparent;
}

.category-card:hover {
  transform: translateY(-6px);
  border-color: #2563eb;
  box-shadow: 0 10px 20px rgba(0,0,0,0.08);
}

.category-card h3 {
  margin-bottom: 10px;
  font-size: 16px;
}

.category-card p {
  color: #6b7280;
  font-size: 14px;
}

.section {
  margin-top: 50px;
}

.section h2 {
  margin-bottom: 20px;
  font-size: 20px;
}

.booking-card {
  background: #f3f4f6;
  padding: 15px;
  border-radius: 12px;
  margin-top: 15px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.booking-card button {
  padding: 6px 12px;
  border-radius: 8px;
  border: none;
  background: #ef4444;
  color: white;
  cursor: pointer;
  font-size: 13px;
  transition: background 0.2s;
}

.booking-card button:hover:not(:disabled) {
  background: #dc2626;
}

.booking-card button:disabled {
  background: #fca5a5;
  cursor: not-allowed;
}

.error-message {
  background: #fef2f2;
  color: #dc2626;
  padding: 12px;
  border-radius: 8px;
  margin-top: 20px;
  text-align: center;
}

@media (max-width: 768px) {
  .categories {
    grid-template-columns: repeat(2, 1fr);
  }
  
  header {
    padding: 15px 20px;
  }
  
  .search-box {
    flex-direction: column;
  }
}
</style>