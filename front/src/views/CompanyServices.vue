<template>
  <div class="services-page">
    <header>
      <div class="logo">AutoBooking — Панель компании</div>
      <div class="nav">
        <button type="button" @click="router.push('/company/calendar')">Календарь</button>
        <button type="button" @click="router.push('/company/bookings')">Записи</button>
        <button type="button" @click="handleLogout">Выход</button>
      </div>
    </header>

    <div class="container">
      <div v-if="pageError" class="error-banner">{{ pageError }}</div>

      <div class="form-card">
        <h2>{{ editingId ? 'Редактировать услугу' : 'Создать услугу' }}</h2>

        <form @submit.prevent="editingId ? updateService() : createService()">
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

          <input
            v-model.number="form.price"
            type="number"
            placeholder="Цена (₽), необязательно"
            min="0"
            step="0.01"
          />

          <input
            v-model.number="form.duration"
            type="number"
            placeholder="Длительность (мин)"
            required
            min="5"
            :class="{ error: errors.duration }"
          />
          <span v-if="errors.duration" class="error-text">{{ errors.duration }}</span>

          <label class="checkbox-row">
            <input v-model="form.is_active" type="checkbox" />
            Активна (видна клиентам)
          </label>

          <button type="submit" class="primary" :disabled="creating || !companyId">
            {{
              creating
                ? 'Сохранение...'
                : editingId
                  ? 'Сохранить изменения'
                  : 'Добавить услугу'
            }}
          </button>
          <button
            v-if="editingId"
            type="button"
            class="secondary"
            @click="cancelEdit"
          >
            Отмена
          </button>
        </form>

        <div v-if="createError" class="error-message">{{ createError }}</div>
        <div v-if="createSuccess" class="success-message">Сохранено</div>
      </div>

      <div class="services-list">
        <h2>Мои услуги</h2>

        <div v-if="loading" class="loading">Загрузка...</div>
        <div v-else-if="!companyId" class="empty-state">
          Сначала создайте компанию в разделе «Записи».
        </div>
        <div v-else-if="services.length === 0" class="empty-state">Пока нет услуг</div>

        <div v-else class="services-items">
          <div v-for="svc in services" :key="svc.id" class="service-item">
            <div class="service-info">
              <strong>{{ svc.name }}</strong>
              <span>
                {{ formatPrice(svc.price) }} · {{ svc.duration_minutes }} мин
                <span v-if="!svc.is_active" class="badge">скрыта</span>
              </span>
            </div>
            <div class="service-actions">
              <button
                type="button"
                class="icon-btn edit-btn"
                aria-label="Изменить"
                @click="startEdit(svc)"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path
                    d="M3 17.25V21h3.75L19.81 7.94l-3.75-3.75L3 17.25Z"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                  <path
                    d="M14.06 4.19 17.81 7.94"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                </svg>
              </button>
              <button
                type="button"
                class="icon-btn delete-btn"
                aria-label="Удалить"
                @click="removeService(svc.id)"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path
                    d="M3 6h18"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                  />
                  <path
                    d="M8 6V4h8v2"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                  <path
                    d="M6 6l1 16h10l1-16"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                  <path
                    d="M10 11v6"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                  />
                  <path
                    d="M14 11v6"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                  />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
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

const loading = ref(false);
const creating = ref(false);
const createError = ref('');
const createSuccess = ref(false);
const pageError = ref('');

const companyId = ref(null);
const services = ref([]);
const editingId = ref(null);

const errors = reactive({ name: '', duration: '' });

const form = reactive({
  name: '',
  description: '',
  price: null,
  duration: null,
  is_active: true,
});

onMounted(async () => {
  await loadCompanyAndServices();
});

async function loadCompanyAndServices() {
  loading.value = true;
  pageError.value = '';

  try {
    const token = localStorage.getItem('access_token');
    const response = await fetch(`${API_URL}/owner/company`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (response.status === 404) {
      companyId.value = null;
      services.value = [];
      pageError.value = 'Создайте компанию на странице записей.';
      return;
    }

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(formatApiError(data));
    }

    companyId.value = data.id;
    services.value = Array.isArray(data.services) ? data.services : [];
  } catch (err) {
    pageError.value = err.message;
    services.value = [];
  } finally {
    loading.value = false;
  }
}

function validateForm() {
  errors.name = '';
  errors.duration = '';
  let ok = true;

  if (!form.name.trim()) {
    errors.name = 'Введите название';
    ok = false;
  }

  if (!form.duration || form.duration <= 5 || form.duration >= 180) {
    errors.duration = 'Длительность должна быть больше 5 и меньше 180 минут';
    ok = false;
  }

  return ok;
}

function resetForm() {
  form.name = '';
  form.description = '';
  form.price = null;
  form.duration = 60;
  form.is_active = true;
  editingId.value = null;
}

async function createService() {
  if (!companyId.value || !validateForm()) return;

  creating.value = true;
  createError.value = '';
  createSuccess.value = false;

  try {
    const token = localStorage.getItem('access_token');
    const body = {
      name: form.name.trim(),
      description: form.description.trim() || null,
      price: form.price === '' || form.price === null ? null : Number(form.price),
      duration_minutes: Number(form.duration),
      is_active: form.is_active,
    };

    const response = await fetch(`${API_URL}/owner/company/${companyId.value}/services`, {
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

    createSuccess.value = true;
    setTimeout(() => {
      createSuccess.value = false;
    }, 2000);
    resetForm();
    await loadCompanyAndServices();
  } catch (err) {
    createError.value = err.message;
  } finally {
    creating.value = false;
  }
}

function startEdit(svc) {
  editingId.value = svc.id;
  form.name = svc.name;
  form.description = svc.description || '';
  form.price = svc.price;
  form.duration = svc.duration_minutes;
  form.is_active = svc.is_active;
}

function cancelEdit() {
  resetForm();
}

async function updateService() {
  if (!editingId.value || !validateForm()) return;

  creating.value = true;
  createError.value = '';
  createSuccess.value = false;

  try {
    const token = localStorage.getItem('access_token');
    const body = {
      name: form.name.trim(),
      description: form.description.trim() || null,
      price: form.price === '' || form.price === null ? null : Number(form.price),
      duration_minutes: Number(form.duration),
      is_active: form.is_active,
    };

    const response = await fetch(`${API_URL}/owner/services/${editingId.value}`, {
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

    createSuccess.value = true;
    setTimeout(() => {
      createSuccess.value = false;
    }, 2000);
    resetForm();
    await loadCompanyAndServices();
  } catch (err) {
    createError.value = err.message;
  } finally {
    creating.value = false;
  }
}

async function removeService(serviceId) {
  if (!confirm('Удалить услугу? Связанные записи будут удалены.')) return;

  try {
    const token = localStorage.getItem('access_token');
    const response = await fetch(`${API_URL}/owner/services/${serviceId}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` },
    });

    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(formatApiError(data));
    }

    services.value = services.value.filter((s) => s.id !== serviceId);
    if (editingId.value === serviceId) resetForm();
  } catch (err) {
    alert(err.message);
  }
}

function handleLogout() {
  logout();
}

function formatPrice(price) {
  if (price === null || price === undefined) return 'Цена не указана';
  return `${new Intl.NumberFormat('ru-RU').format(price)} ₽`;
}
</script>

<style scoped>
.services-page {
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
  width: 1000px;
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

.form-card,
.services-list {
  flex: 1;
  min-width: 400px;
  background: white;
  padding: 30px;
  border-radius: 20px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08);
}

.form-card h2,
.services-list h2 {
  margin-bottom: 20px;
  color: #1f2937;
}

input,
textarea {
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
textarea:focus {
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

.checkbox-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  font-size: 14px;
  color: #374151;
}

.checkbox-row input {
  width: auto;
  margin: 0;
}

textarea {
  resize: none;
}

.primary,
.secondary {
  width: 100%;
  padding: 12px;
  border-radius: 10px;
  border: none;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
  margin-bottom: 8px;
}

.primary {
  background: #16a34a;
  color: white;
}

.primary:hover:not(:disabled) {
  background: #15803d;
}

.primary:disabled {
  background: #86efac;
  cursor: not-allowed;
}

.secondary {
  background: #e5e7eb;
  color: #374151;
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

.badge {
  margin-left: 8px;
  color: #92400e;
  font-weight: 600;
}

.service-actions {
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  gap: 8px;
}

.service-actions button {
  padding: 0;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  transition: background 0.2s, opacity 0.2s;
}

.icon-btn {
  width: 36px;
  height: 36px;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-left: 0;
  border: 1px solid transparent;
}

.edit-btn {
  background: transparent;
  color: #2563eb; /* синяя ручка */
}

.delete-btn {
  background: transparent;
  color: #ef4444; /* красная урна */
  border-color: transparent;
}

.edit-btn:hover,
.delete-btn:hover {
  background: #f3f4f6;
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
}
</style>
