<template>
  <div class="calendar-page">
    <header>
      <div class="logo">AutoBooking — Календарь</div>
      <div class="nav">
        <button @click="router.push('/company/services')">Услуги</button>
        <button @click="router.push('/company/bookings')">Записи</button>
        <button @click="handleLogout">Выход</button>
      </div>
    </header>

    <div class="container">
      <!-- Настройка -->
      <div class="settings-card">
        <h2>Настройка рабочего времени</h2>

        <label>Рабочие дни</label>
        <div class="days">
          <div 
            v-for="(day, index) in weekDays" 
            :key="index"
            :class="['day', { active: workingDays.includes(index) }]"
            @click="toggleDay(index)"
          >
            {{ day }}
          </div>
        </div>

        <label>Начало рабочего дня</label>
        <input 
          v-model="settings.startTime" 
          type="time" 
          @change="updatePreview"
        />

        <label>Конец рабочего дня</label>
        <input 
          v-model="settings.endTime" 
          type="time" 
          @change="updatePreview"
        />

        <label>Интервал записи (мин)</label>
        <select v-model="settings.interval" @change="updatePreview">
          <option value="15">15</option>
          <option value="30">30</option>
          <option value="45">45</option>
          <option value="60">60</option>
        </select>

        <label>Перерыв (необязательно)</label>
        <div class="break-time">
          <input v-model="settings.breakStart" type="time" placeholder="Начало" />
          <input v-model="settings.breakEnd" type="time" placeholder="Конец" />
        </div>

        <button 
          class="primary" 
          @click="saveSettings" 
          :disabled="saving"
        >
          {{ saving ? 'Сохранение...' : 'Сохранить настройки' }}
        </button>

        <div v-if="saveError" class="error-message">{{ saveError }}</div>
        <div v-if="saveSuccess" class="success-message">Настройки сохранены!</div>
      </div>

      <!-- Предпросмотр -->
      <div class="preview-card">
        <h2>Предпросмотр слотов</h2>
        <p style="color:#6b7280;">Пример доступных слотов на день</p>

        <div v-if="previewSlots.length === 0" class="no-slots">
          Выберите рабочие дни и время
        </div>

        <div v-else class="slots">
          <div 
            v-for="(slot, index) in previewSlots" 
            :key="index"
            class="slot"
          >
            {{ slot }}
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

const weekDays = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];

const workingDays = ref([0, 1, 2, 3, 4]); // Пн-Пт по умолчанию

const settings = reactive({
  startTime: '09:00',
  endTime: '18:00',
  interval: '30',
  breakStart: '',
  breakEnd: '',
});

const previewSlots = ref([]);
const saving = ref(false);
const saveError = ref('');
const saveSuccess = ref(false);

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

onMounted(() => {
  updatePreview();
});

const toggleDay = (index) => {
  const pos = workingDays.value.indexOf(index);
  if (pos === -1) {
    workingDays.value.push(index);
  } else {
    workingDays.value.splice(pos, 1);
  }
  updatePreview();
};

const updatePreview = () => {
  previewSlots.value = [];

  if (workingDays.value.length === 0) return;

  const start = settings.startTime;
  const end = settings.endTime;
  const interval = parseInt(settings.interval);

  const [startHour, startMin] = start.split(':').map(Number);
  const [endHour, endMin] = end.split(':').map(Number);

  const startMinutes = startHour * 60 + startMin;
  const endMinutes = endHour * 60 + endMin;

  let current = startMinutes;
  while (current + interval <= endMinutes) {
    const hours = Math.floor(current / 60);
    const mins = current % 60;
    const timeStr = `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}`;
    
    // Проверка перерыва
    const isBreak = settings.breakStart && settings.breakEnd &&
      timeStr >= settings.breakStart && timeStr < settings.breakEnd;

    if (!isBreak) {
      previewSlots.value.push(timeStr);
    }

    current += interval;
  }
};

const saveSettings = async () => {
  saving.value = true;
  saveError.value = '';
  saveSuccess.value = false;

  try {
    const token = localStorage.getItem('access_token');
    
    // TODO: Заменить на реальный эндпоинт сохранения расписания
    const response = await fetch(`${API_URL}/owner/company/working-hours`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        working_days: workingDays.value,
        start_time: settings.startTime,
        end_time: settings.endTime,
        interval_minutes: parseInt(settings.interval),
        break_start: settings.breakStart || null,
        break_end: settings.breakEnd || null,
      }),
    });

    if (!response.ok) {
      throw new Error('Ошибка сохранения');
    }

    saveSuccess.value = true;
    setTimeout(() => {
      saveSuccess.value = false;
    }, 3000);
  } catch (err) {
    saveError.value = err.message;
  } finally {
    saving.value = false;
  }
};

const handleLogout = () => {
  logout();
  router.push('/');
};
</script>

<style scoped>
.calendar-page {
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
  width: 1100px;
  max-width: 95%;
  margin: 40px auto;
  display: flex;
  gap: 40px;
  flex-wrap: wrap;
}

.settings-card,
.preview-card {
  flex: 1;
  min-width: 400px;
  background: white;
  padding: 30px;
  border-radius: 20px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.08);
}

.settings-card h2,
.preview-card h2 {
  margin-bottom: 20px;
  color: #1f2937;
}

label {
  display: block;
  margin-bottom: 8px;
  color: #374151;
  font-weight: 500;
}

.days {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 10px;
  margin-bottom: 20px;
}

.day {
  padding: 12px;
  background: #f9fafb;
  border-radius: 8px;
  text-align: center;
  cursor: pointer;
  border: 2px solid transparent;
  transition: 0.2s;
  font-weight: 500;
}

.day:hover {
  background: #f3f4f6;
}

.day.active {
  border-color: #16a34a;
  background: #dcfce7;
  color: #166534;
}

input,
select {
  width: 100%;
  padding: 12px;
  margin-bottom: 15px;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  font-size: 14px;
  transition: border-color 0.2s;
}

input:focus,
select:focus {
  outline: none;
  border-color: #16a34a;
}

.break-time {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
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

.slots {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  margin-top: 20px;
}

.slot {
  background: #dcfce7;
  padding: 10px;
  text-align: center;
  border-radius: 8px;
  font-size: 14px;
  color: #166534;
  font-weight: 500;
}

.no-slots {
  text-align: center;
  padding: 40px 20px;
  color: #6b7280;
  background: #f9fafb;
  border-radius: 12px;
  margin-top: 20px;
}

@media (max-width: 768px) {
  .container {
    flex-direction: column;
  }

  .settings-card,
  .preview-card {
    min-width: 100%;
  }

  .slots {
    grid-template-columns: repeat(3, 1fr);
  }

  header {
    padding: 15px 20px;
  }
}
</style>