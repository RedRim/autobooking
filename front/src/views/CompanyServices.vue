<template>
  <div class="services-page">
    <header>
      <div class="logo">AutoBooking — Панель компании</div>
      <div class="nav">
        <button @click="router.push('/company/calendar')">Календарь</button>
        <button @click="router.push('/company/bookings')">Записи</button>
        <button @click="handleLogout">Выход</button>
      </div>
    </header>

    <div class="container">
      <!-- Создание услуги -->
      <div class="form-card">
        <h2>Создать услугу</h2>

        <form @submit.prevent="createService">
          <input 
            v-model="form.name" 
            type="text" 
            placeholder="Название услуги" 
            required
            :class="{ error: errors.name }"
          />
          <span v-if="errors.name" class="error-text">{{ errors.name }}</span>

          <textarea 
            v-model="form.description" 
            placeholder="Описание услуги"
            rows="3"
          ></textarea>

          <select v-model="form.category" required>
            <option value="">Категория</option>
            <option value="repair">Ремонт</option>
            <option value="diagnostics">Диагностика</option>
            <option value="wash">Мойка</option>
            <option value="detailing">Детейлинг</option>
            <option value="barber">Барбершоп</option>
            <option value="beauty">Салон красоты</option>
            <option value="massage">Массаж</option>
          </select>

          <input 
            v-model.number="form.price" 
            type="number" 
            placeholder="Цена (₽)" 
            required
            min="0"
            :class="{ error: errors.price }"
          />
          <span v-if="errors.price" class="error-text">{{ errors.price }}</span>

          <input 
            v-model.number="form.duration" 
            type="number" 
            placeholder="Длительность (мин)" 
            required
            min="5"
            :class="{ error: errors.duration }"
          />
          <span v-if="errors.duration" class="error-text">{{ errors.duration }}</span>

          <button type="submit" class="primary" :disabled="creating">
            {{ creating ? 'Создание...' : 'Добавить услугу' }}
          </button>
        </form>

        <div v-if="createError" class="error-message">{{ createError }}</div>
        <div v-if="createSuccess" class="success-message">Услуга добавлена!</div>
      </div>

      <!-- Список услуг -->
      <div class="services-list">
        <h2>Мои услуги</h2>

        <div v-if="loading" class="loading">Загрузка...</div>
        <div v-else-if="services.length === 0" class="empty-state">
          Пока нет услуг
        </div>

        <div v-else class="services-items">
          <div 
            v-for="service in services" 
            :key="service.id" 
            class="service-item"
          >
            <div class="service-info">
              <strong>{{ service.name }}</strong>
              <span>{{ formatPrice(service.price) }} • {{ service.duration_minutes }} мин</span>
            </div>
            <div class="service-actions">
              <button class="edit-btn" @click="editService(service)">
                Редактировать
              </button>
              <button class="delete-btn" @click="deleteService(service.id)">
                Удалить
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuth } from '@/composables/useAuth';

const router = useRouter();
const { logout } = useAuth();

const loading = ref(false);
const creating = ref(false);
const createError = ref('');
const createSuccess = ref(false);

const errors = reactive({ name: '', price: '', duration: '' });

const form = reactive({
  name: '',
  description: '',
  category: '',
  price: 0,
  duration: 0,
});

const services = ref([
  // Заглушка, позже загрузим из API
  { id: 1, name: 'Замена масла', price: 2000, duration_minutes: 40 },
  { id: 2, name: 'Комплексная мойка', price: 1500, duration_minutes: 60 },
]);

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

onMounted(async () => {
  await loadServices();
});

const loadServices = async () => {
  loading.value = true;
  
  try {
    const token = localStorage.getItem('access_token');
    // TODO: Заменить на реальный эндпоинт получения услуг компании
    const response = await fetch(`${API_URL}/owner/company/services`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (response.ok) {
      services.value = await response.json();
    }
  } catch (err) {
    console.error('Ошибка загрузки услуг:', err);
  } finally {
    loading.value = false;
  }
};

const validateForm = () => {
  errors.name = '';
  errors.price = '';
  errors.duration = '';
  let isValid = true;

  if (!form.name) {
    errors.name = 'Введите название услуги';
    isValid = false;
  }

  if (!form.price || form.price <= 0) {
    errors.price = 'Укажите корректную цену';
    isValid = false;
  }

  if (!form.duration || form.duration < 5) {
    errors.duration = 'Длительность должна быть от 5 минут';
    isValid = false;
  }

  return isValid;
};

const createService = async () => {
  if (!validateForm()) return;

  creating.value = true;
  createError.value = '';
  createSuccess.value = false;

  try {
    const token = localStorage.getItem('access_token');
    
    // TODO: Заменить на реальный эндпоинт создания услуги
    const response = await fetch(`${API_URL}/owner/company/services`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        name: form.name,
        description: form.description || null,
        category: form.category || null,
        price: form.price,
        duration_minutes: form.duration,
      }),
    });

    if (!response.ok) {
      throw new Error('Ошибка создания услуги');
    }

    // Очистка формы
    form.name = '';
    form.description = '';
    form.category = '';
    form.price = 0;
    form.duration = 0;

    createSuccess.value = true;
    setTimeout(() => {
      createSuccess.value = false;
    }, 3000);

    // Перезагрузка списка
    await loadServices();
  } catch (err) {
    createError.value = err.message;
  } finally {
    creating.value = false;
  }
};

const editService = (service) => {
  // TODO: Реализовать редактирование (модальное окно или переход на страницу)
  alert(`Редактировать услугу: ${service.name}`);
};

const deleteService = async (serviceId) => {
  if (!confirm('Вы уверены, что хотите удалить эту услугу?')) return;

  try {
    const token = localStorage.getItem('access_token');
    
    // TODO: Заменить на реальный эндпоинт удаления услуги
    const response = await fetch(`${API_URL}/owner/company/services/${serviceId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error('Ошибка удаления');
    }

    services.value = services.value.filter(s => s.id !== serviceId);
  } catch (err) {
    alert(err.message);
  }
};

const handleLogout = () => {
  logout();
  router.push('/');
};

const formatPrice = (price) => {
  return new Intl.NumberFormat('ru-RU').format(price) + ' ₽';
};
</script>

<style scoped>
.services-page {
  font-family: "Segoe UI", Arial, sans-serif;
  background: #f3f4f6;
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
  width: 1000px;
  max-width: 95%;
  margin: 40px auto;
  display: flex;
  gap: 40px;
  flex-wrap: wrap;
}

.form-card,
.services-list {
  flex: 1;
  min-width: 400px;
  background: white;
  padding: 30px;
  border-radius: 20px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.08);
}

.form-card h2,
.services-list h2 {
  margin-bottom: 20px;
  color: #1f2937;
}

input,
textarea,
select {
  width: 100%;
  padding: 12px;
  margin-bottom: 15px;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  font-size: 14px;
  transition: border-color 0.2s;
  font-family: inherit;
}

input:focus,
textarea:focus,
select:focus {
  outline: none;
  border-color: #16a34a;
}

input.error {
  border-color: #ef4444;
}

.error-text {
  color: #ef4444;
  font-size: 12px;
  margin-top: -10px;
  margin-bottom: 10px;
  display: block;
}

textarea {
  resize: none;
}

.primary {
  width: 100%;
  padding: 12px;
  border-radius: 10px;
  border: none;
  background: #16a34a;
  color: white;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.primary:hover:not(:disabled) {
  background: #15803d;
}

.primary:disabled {
  background: #86efac;
  cursor: not-allowed;
}

.error-message {
  background: #fef2f2;
  color: #dc2626;
  padding: 10px;
  border-radius: 8px;
  margin-top: 15px;
  text-align: center;
  font-size: 14px;
}

.success-message {
  background: #dcfce7;
  color: #166534;
  padding: 10px;
  border-radius: 8px;
  margin-top: 15px;
  text-align: center;
  font-size: 14px;
}

.loading,
.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #6b7280;
}

.services-items {
  margin-top: 20px;
}

.service-item {
  background: #f9fafb;
  padding: 15px;
  border-radius: 12px;
  margin-bottom: 15px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: 0.2s;
}

.service-item:hover {
  background: #f3f4f6;
}

.service-info strong {
  display: block;
  color: #111827;
  margin-bottom: 5px;
}

.service-info span {
  color: #6b7280;
  font-size: 14px;
}

.service-actions button {
  padding: 6px 10px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  margin-left: 5px;
  font-size: 13px;
  transition: background 0.2s;
}

.edit-btn {
  background: #facc15;
  color: #1f2937;
}

.edit-btn:hover {
  background: #fbbf24;
}

.delete-btn {
  background: #ef4444;
  color: white;
}

.delete-btn:hover {
  background: #dc2626;
}

@media (max-width: 768px) {
  .container {
    flex-direction: column;
  }

  .form-card,
  .services-list {
    min-width: 100%;
  }

  header {
    padding: 15px 20px;
  }

  .service-item {
    flex-direction: column;
    gap: 15px;
    text-align: center;
  }

  .service-actions {
    display: flex;
    justify-content: center;
  }
}
</style>