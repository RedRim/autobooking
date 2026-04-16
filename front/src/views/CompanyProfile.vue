<template>
  <div class="profile-page">
    <header>
      <div class="logo">AutoBooking — Профиль компании</div>
      <div class="nav">
        <button type="button" @click="router.push('/company/bookings')">Записи</button>
        <button type="button" @click="router.push('/company/services')">Услуги</button>
        <button type="button" @click="router.push('/company/calendar')">Календарь</button>
        <button type="button" @click="handleLogout">Выход</button>
      </div>
    </header>

    <div class="container">
      <div v-if="loading" class="state-card">Загрузка...</div>
      <div v-else-if="pageError" class="state-card error">{{ pageError }}</div>

      <div v-else class="card">
        <h2>Редактирование информации о компании</h2>
        <br>
        <!-- <p class="muted">
          Категория определяется при модерации: <strong>{{ categoryLabel }}</strong>
        </p> -->

        <form class="form" @submit.prevent="saveCompany">
          <label>
            Название
            <input v-model="form.name" type="text" required />
          </label>

          <label>
            Описание
            <textarea v-model="form.description" rows="3" placeholder="Описание компании"></textarea>
          </label>

          <label>
            Город
            <input v-model="form.city" type="text" placeholder="Город" />
          </label>

          <label>
            Адрес
            <input v-model="form.address" type="text" placeholder="Адрес" />
          </label>

          <label>
            Телефон
            <input v-model="form.phone" type="text" placeholder="Телефон" />
          </label>

          <button class="primary" type="submit" :disabled="saving">
            {{ saving ? 'Сохранение...' : 'Сохранить изменения' }}
          </button>
        </form>

        <div v-if="saveError" class="message error">{{ saveError }}</div>
        <div v-if="saveSuccess" class="message success">Изменения сохранены</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';

import { useAuth } from '@/composables/useAuth';
import { formatApiError } from '@/utils/apiError';

const router = useRouter();
const auth = useAuth();

const loading = ref(true);
const saving = ref(false);
const pageError = ref('');
const saveError = ref('');
const saveSuccess = ref(false);
const companyId = ref(null);
const companyCategory = ref('');

const form = reactive({
  name: '',
  description: '',
  city: '',
  address: '',
  phone: '',
  is_active: true,
});

const categoryLabel = computed(() => companyCategory.value || 'Не указана');

onMounted(async () => {
  await loadCompany();
});

function handleLogout() {
  auth.logout();
}

async function loadCompany() {
  loading.value = true;
  pageError.value = '';
  try {
    const response = await auth.authFetch('/owner/company');
    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(formatApiError(data));
    }

    companyId.value = data.id;
    companyCategory.value = data.category || '';
    form.name = data.name || '';
    form.description = data.description || '';
    form.city = data.city || '';
    form.address = data.address || '';
    form.phone = data.phone || '';
    form.is_active = Boolean(data.is_active);
  } catch (err) {
    pageError.value = err.message || 'Не удалось загрузить данные компании';
  } finally {
    loading.value = false;
  }
}

async function saveCompany() {
  if (!companyId.value) return;

  saving.value = true;
  saveError.value = '';
  saveSuccess.value = false;

  try {
    const response = await auth.authFetch(`/owner/company/${companyId.value}`, {
      method: 'PUT',
      body: JSON.stringify({
        name: form.name.trim() || null,
        description: form.description.trim() || null,
        city: form.city.trim() || null,
        address: form.address.trim() || null,
        phone: form.phone.trim() || null,
        is_active: form.is_active,
      }),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(formatApiError(data));
    }

    companyCategory.value = data.category || companyCategory.value;
    saveSuccess.value = true;
  } catch (err) {
    saveError.value = err.message || 'Не удалось сохранить изменения';
  } finally {
    saving.value = false;
  }
}
</script>

<style scoped>
.profile-page {
  font-family: 'Segoe UI', Arial, sans-serif;
  background: #f5f7fa;
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
}

.container {
  width: 900px;
  max-width: 95%;
  margin: 40px auto;
}

.state-card,
.card {
  background: white;
  border-radius: 16px;
  padding: 24px;
}

.state-card.error {
  color: #dc2626;
}

.muted {
  color: #6b7280;
  margin-bottom: 18px;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form label {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form input,
.form textarea {
  width: 100%;
  box-sizing: border-box;
  padding: 12px;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  font-size: 14px;
  font-family: inherit;
}

.toggle {
  flex-direction: row !important;
  align-items: center;
  gap: 10px !important;
}

.primary {
  width: 100%;
  box-sizing: border-box;
  padding: 12px;
  border-radius: 10px;
  border: none;
  background: #16a34a;
  color: white;
  font-weight: 500;
  cursor: pointer;
}

.primary:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.message {
  margin-top: 12px;
  padding: 12px;
  border-radius: 8px;
  text-align: center;
}

.message.error {
  background: #fef2f2;
  color: #dc2626;
}

.message.success {
  background: #dcfce7;
  color: #166534;
}

@media (max-width: 768px) {
  header {
    padding: 15px 20px;
  }
}
</style>
