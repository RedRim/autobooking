<template>
  <div class="manager-page">
    <header>
      <div class="logo">AutoBooking · Модерация</div>
      <div class="nav">
        <button type="button" @click="loadRequests">Обновить</button>
        <button type="button" @click="handleLogout">Выйти</button>
      </div>
    </header>

    <div class="container">
      <h2 class="page-title">Заявки на создание компаний</h2>

      <div v-if="loading" class="loading">Загрузка заявок...</div>
      <div v-else-if="error" class="error-message">{{ error }}</div>
      <div v-else-if="requests.length === 0" class="empty-state">Новых заявок пока нет</div>

      <div v-else class="layout">
        <aside class="requests-list">
          <button
            v-for="item in requests"
            :key="item.id"
            type="button"
            class="request-item"
            :class="{ active: selectedRequest?.id === item.id }"
            @click="selectRequest(item)"
          >
            <strong>{{ item.name }}</strong>
            <span>Заявка #{{ item.id }}</span>
            <span>{{ item.city }}</span>
            <span class="muted">{{ item.requested_category }}</span>
          </button>
        </aside>

        <section class="request-details" v-if="selectedRequest">
          <h3>Проверка заявки #{{ selectedRequest.id }}</h3>
          <div class="row">
            <div class="label">Владелец</div>
            <div>#{{ selectedRequest.owner_id }}</div>
          </div>
          <div class="row">
            <div class="label">Название</div>
            <div>{{ selectedRequest.name }}</div>
          </div>

          <form class="edit-form" @submit.prevent="saveRequest">
            <label>
              Категория
              <input
                v-model="editForm.category"
                type="text"
                placeholder="Категория"
                @input="onCategoryInput"
                @blur="closeSuggestions"
                required
              />
            </label>
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

            <label>
              Город
              <input v-model="editForm.city" type="text" placeholder="Город" required />
            </label>

            <div class="actions">
              <button type="submit" class="secondary" :disabled="saving">
                {{ saving ? 'Сохранение...' : 'Сохранить изменения' }}
              </button>
              <button type="button" class="primary" :disabled="approving" @click="approveRequest">
                {{ approving ? 'Подтверждение...' : 'Одобрить заявку' }}
              </button>
            </div>
          </form>

          <div v-if="formMessage" class="success-message">{{ formMessage }}</div>
          <div v-if="formError" class="error-message">{{ formError }}</div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue';

import { API_URL } from '@/config';
import { useAuth } from '@/composables/useAuth';
import { formatApiError } from '@/utils/apiError';

const auth = useAuth();

const loading = ref(true);
const error = ref('');
const requests = ref([]);
const selectedRequest = ref(null);

const saving = ref(false);
const approving = ref(false);
const formError = ref('');
const formMessage = ref('');

const editForm = reactive({
  category: '',
  city: '',
});

const categoryLoading = ref(false);
const categoryOptions = ref([]);
let categoryTimer = null;

onMounted(async () => {
  await loadRequests();
});

function closeSuggestions() {
  window.setTimeout(() => {
    categoryOptions.value = [];
  }, 100);
}

function pickCategory(value) {
  editForm.category = value;
  categoryOptions.value = [];
}

function handleLogout() {
  auth.logout();
}

async function loadRequests() {
  loading.value = true;
  error.value = '';
  formError.value = '';
  formMessage.value = '';

  try {
    const response = await auth.authFetch('/manager/company-requests?status=pending');
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(formatApiError(data));
    }
    requests.value = Array.isArray(data) ? data : [];
    if (requests.value.length === 0) {
      selectedRequest.value = null;
      return;
    }
    if (!selectedRequest.value) {
      selectRequest(requests.value[0]);
      return;
    }
    const freshSelected = requests.value.find((item) => item.id === selectedRequest.value.id);
    if (freshSelected) {
      selectRequest(freshSelected);
    } else {
      selectRequest(requests.value[0]);
    }
  } catch (err) {
    error.value = err.message || 'Не удалось загрузить заявки';
    requests.value = [];
    selectedRequest.value = null;
  } finally {
    loading.value = false;
  }
}

function selectRequest(item) {
  selectedRequest.value = item;
  editForm.category = item.requested_category || '';
  editForm.city = item.city || '';
  formError.value = '';
  formMessage.value = '';
  categoryOptions.value = [];
}

async function saveRequest() {
  if (!selectedRequest.value) return;
  formError.value = '';
  formMessage.value = '';
  saving.value = true;

  try {
    const response = await auth.authFetch(`/manager/company-requests/${selectedRequest.value.id}`, {
      method: 'PUT',
      body: JSON.stringify({
        category: editForm.category.trim(),
        city: editForm.city.trim(),
      }),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(formatApiError(data));
    }
    selectedRequest.value = data;
    formMessage.value = 'Заявка обновлена';
    await loadRequests();
  } catch (err) {
    formError.value = err.message || 'Не удалось сохранить заявку';
  } finally {
    saving.value = false;
  }
}

async function approveRequest() {
  if (!selectedRequest.value) return;
  formError.value = '';
  formMessage.value = '';
  approving.value = true;

  try {
    const response = await auth.authFetch(
      `/manager/company-requests/${selectedRequest.value.id}/approve`,
      {
        method: 'POST',
        body: JSON.stringify({
          category: editForm.category.trim(),
          city: editForm.city.trim(),
        }),
      },
    );
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(formatApiError(data));
    }
    formMessage.value = `Заявка одобрена, компания #${data.company_id} создана`;
    selectedRequest.value = null;
    await loadRequests();
  } catch (err) {
    formError.value = err.message || 'Не удалось одобрить заявку';
  } finally {
    approving.value = false;
  }
}

function onCategoryInput() {
  if (categoryTimer) {
    clearTimeout(categoryTimer);
  }
  const query = editForm.category.trim();
  if (!query) {
    categoryOptions.value = [];
    return;
  }
  categoryTimer = setTimeout(() => {
    loadCategorySuggestions(query);
  }, 250);
}

async function loadCategorySuggestions(query) {
  categoryLoading.value = true;
  try {
    const response = await auth.authFetch(
      `/categories?search=${encodeURIComponent(query)}&limit=8`,
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
</script>

<style scoped>
.manager-page {
  font-family: 'Segoe UI', Arial, sans-serif;
  background: #f5f7fa;
  min-height: 100vh;
}

header {
  background: linear-gradient(135deg, #4c1d95, #7c3aed);
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
  color: #4c1d95;
  font-weight: 500;
}

.container {
  width: 1200px;
  max-width: 95%;
  margin: 40px auto;
}

.page-title {
  margin-bottom: 20px;
}

.layout {
  display: grid;
  grid-template-columns: 330px 1fr;
  gap: 20px;
}

.requests-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.request-item {
  text-align: left;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: white;
  padding: 12px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.request-item.active {
  border-color: #7c3aed;
  box-shadow: 0 0 0 1px #7c3aed;
}

.muted {
  color: #6b7280;
}

.request-details {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.06);
}

.row {
  display: grid;
  grid-template-columns: 120px 1fr;
  margin-bottom: 10px;
}

.label {
  color: #6b7280;
}

.edit-form {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.edit-form label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-weight: 500;
}

.edit-form input {
  padding: 10px;
  border-radius: 8px;
  border: 1px solid #d1d5db;
}

.hint {
  color: #6b7280;
  font-size: 13px;
}

.suggestions {
  margin-top: -6px;
  margin-bottom: 6px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
  background: white;
}

.suggestion-item {
  width: 100%;
  text-align: left;
  padding: 8px 10px;
  border: none;
  background: white;
  cursor: pointer;
}

.suggestion-item:hover {
  background: #f3f4f6;
}

.actions {
  display: flex;
  gap: 10px;
}

.actions button {
  border: none;
  border-radius: 8px;
  padding: 10px 14px;
  cursor: pointer;
  color: white;
}

.primary {
  background: #16a34a;
}

.secondary {
  background: #7c3aed;
}

.loading,
.empty-state {
  text-align: center;
  padding: 50px 20px;
  background: white;
  border-radius: 16px;
}

.error-message {
  margin-top: 12px;
  background: #fef2f2;
  color: #dc2626;
  padding: 10px;
  border-radius: 8px;
}

.success-message {
  margin-top: 12px;
  background: #dcfce7;
  color: #166534;
  padding: 10px;
  border-radius: 8px;
}

@media (max-width: 900px) {
  .layout {
    grid-template-columns: 1fr;
  }

  header {
    padding: 15px 20px;
  }
}
</style>
