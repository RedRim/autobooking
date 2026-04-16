<template>
  <div class="calendar-page">
    <header>
      <div class="logo">AutoBooking — Календарь</div>
      <div class="nav">
        <button type="button" @click="router.push('/company/services')">Услуги</button>
        <button type="button" @click="router.push('/company/bookings')">Записи</button>
        <button type="button" @click="handleLogout">Выход</button>
      </div>
    </header>

    <div class="container">
      <div v-if="pageError" class="error-banner">{{ pageError }}</div>

      <div v-else-if="!companyId" class="empty-state">
        Сначала создайте компанию в разделе «Записи».
      </div>

      <template v-else>
        <div class="settings-card">
          <h2>Рабочие дни и часы</h2>
          <p class="hint">
            Одинаковые часы для всех выбранных дней. Сохранение отправляет расписание на сервер (7 дней).
          </p>

          <label>Рабочие дни</label>
          <div class="days">
            <div
              v-for="(day, index) in weekDays"
              :key="day"
              :class="['day', { active: workingDays.includes(index) }]"
              role="button"
              tabindex="0"
              @click="toggleDay(index)"
              @keyup.enter="toggleDay(index)"
            >
              {{ day }}
            </div>
          </div>

          <label>Начало</label>
          <input v-model="settings.startTime" type="time" @change="updatePreview" />

          <label>Конец</label>
<input v-model="settings.endTime" type="time" @change="updatePreview" />

<label>Длительность записи (мин)</label>
<input
  v-model.number="settings.duration"
  type="number"
  min="5"
  step="5"
  placeholder="30"
  @input="updatePreview"
/>

          <button type="button" class="primary" :disabled="saving" @click="saveSchedule">
            {{ saving ? 'Сохранение...' : 'Сохранить расписание' }}
          </button>

          <div v-if="saveError" class="error-message">{{ saveError }}</div>
          <div v-if="saveSuccess" class="success-message">Расписание сохранено</div>
        </div>

        <div class="preview-card">
          <h2>Предпросмотр слотов</h2>
          <p class="muted">Пример интервалов для одного дня (как визуальная подсказка)</p>

          <div v-if="previewSlots.length === 0" class="no-slots">
            Выберите рабочие дни и время
          </div>
          <div v-else class="slots">
            <div v-for="(slot, index) in previewSlots" :key="index" class="slot">
              {{ slot }}
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
const { logout } = useAuth();

const weekDays = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];

const workingDays = ref([0, 1, 2, 3, 4]);

const previewSlots = ref([]);
const saving = ref(false);
const saveError = ref('');
const saveSuccess = ref(false);

const companyId = ref(null);
const pageError = ref('');

const settings = reactive({
  startTime: '09:00',
  endTime: '18:00',
  duration: 30, // ← значение по умолчанию
});

function updatePreview() {
  previewSlots.value = [];
  if (workingDays.value.length === 0) return;

  const interval = Math.max(5, Number(settings.duration) || 30);
  const [startHour, startMin] = settings.startTime.split(':').map(Number);
  const [endHour, endMin] = settings.endTime.split(':').map(Number);

  const startMinutes = startHour * 60 + startMin;
  const endMinutes = endHour * 60 + endMin;

  if (startMinutes >= endMinutes) return;

  let current = startMinutes;
  while (current + interval <= endMinutes) {
    const hours = Math.floor(current / 60);
    const mins = current % 60;
    const timeStr = `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}`;
    previewSlots.value.push(timeStr);
    current += interval;
  }
}

onMounted(async () => {
  await loadCompanySchedule();
  updatePreview();
});

function toHHMMSS(time) {
  if (!time) return '09:00:00';
  const s = String(time);
  if (s.length >= 8) return s;
  if (s.length === 5) return `${s}:00`;
  return `${s}:00`;
}

function fromTimeInput(isoTime) {
  const s = toHHMMSS(isoTime);
  return s.slice(0, 5);
}

async function loadCompanySchedule() {
  pageError.value = '';

  try {
    const token = localStorage.getItem('access_token');
    const response = await fetch(`${API_URL}/owner/company`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (response.status === 404) {
      companyId.value = null;
      return;
    }

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(formatApiError(data));
    }

    companyId.value = data.id;
    const wh = data.working_hours || [];

    if (wh.length > 0) {
      workingDays.value = wh.filter((d) => d.is_working).map((d) => d.day_of_week);
      const first = wh.find((d) => d.is_working);
      if (first) {
        settings.startTime = fromTimeInput(first.start_time);
        settings.endTime = fromTimeInput(first.end_time);
      }
    }
  } catch (err) {
    pageError.value = err.message;
  }
}

function toggleDay(index) {
  const pos = workingDays.value.indexOf(index);
  if (pos === -1) {
    workingDays.value.push(index);
    workingDays.value.sort((a, b) => a - b);
  } else {
    workingDays.value.splice(pos, 1);
  }
  updatePreview();
}

async function saveSchedule() {
  if (!companyId.value) return;

  saving.value = true;
  saveError.value = '';
  saveSuccess.value = false;

  const token = localStorage.getItem('access_token');
  const start = `${settings.startTime}:00`;
  const end = `${settings.endTime}:00`;

  try {
    for (let day = 0; day < 7; day += 1) {
      const isWorking = workingDays.value.includes(day);
      const body = isWorking
        ? { day_of_week: day, start_time: start, end_time: end, is_working: true }
        : { day_of_week: day, start_time: '00:00:00', end_time: '00:00:00', is_working: false };

      const response = await fetch(`${API_URL}/owner/company/${companyId.value}/schedule`, {
        method: 'PUT',
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
    }

    saveSuccess.value = true;
    setTimeout(() => {
      saveSuccess.value = false;
    }, 2500);
  } catch (err) {
    saveError.value = err.message;
  } finally {
    saving.value = false;
  }
}

function handleLogout() {
  logout();
}
</script>

<style scoped>
.calendar-page {
  font-family: 'Segoe UI', Arial, sans-serif;
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

.error-banner {
  width: 100%;
  background: #fef2f2;
  color: #b91c1c;
  padding: 12px 16px;
  border-radius: 12px;
}

.empty-state {
  width: 100%;
  text-align: center;
  padding: 48px 20px;
  background: white;
  border-radius: 20px;
  color: #6b7280;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08);
}

.settings-card,
.preview-card {
  flex: 1;
  min-width: 400px;
  background: white;
  padding: 30px;
  border-radius: 20px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08);
}

.settings-card h2,
.preview-card h2 {
  margin-bottom: 12px;
  color: #1f2937;
}

.hint {
  color: #6b7280;
  font-size: 14px;
  margin-bottom: 20px;
}

.muted {
  color: #6b7280;
  font-size: 14px;
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

input {
  width: 100%;
  padding: 12px;
  margin-bottom: 15px;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  font-size: 14px;
  transition: border-color 0.2s;
}

input:focus {
  outline: none;
  border-color: #16a34a;
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
