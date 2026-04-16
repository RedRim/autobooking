<template>
  <div class="search-page">
    <header>
      <div class="logo">AutoBooking</div>
      <div class="nav">
        <button type="button" @click="goDashboard">Личный кабинет</button>
        <button type="button" @click="handleBack">Назад</button>
      </div>
    </header>

    <div class="container">
      <div class="search-bar">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Название компании"
          @keyup.enter="performSearch"
        />
        <button type="button" @click="performSearch" :disabled="searching">
          {{ searching ? 'Поиск...' : 'Найти' }}
        </button>
      </div>

      <div class="filters">
        <input
          v-model="selectedCategory"
          type="text"
          placeholder="Категория"
          @change="performSearch"
        />
        <input
          v-model="selectedCity"
          type="text"
          placeholder="Город"
          @change="performSearch"
        />
      </div>

      <h2 class="results-title">
        {{ loading ? 'Загрузка...' : `Найдено компаний: ${companies.length}` }}
      </h2>

      <div v-if="error" class="error-message">{{ error }}</div>
      <div v-else-if="!loading && companies.length === 0" class="empty-state">
        Ничего не найдено. Измените запрос или фильтры.
      </div>

      <div v-else class="results-list">
        <div
          v-for="company in companies"
          :key="company.id"
          class="company-card"
          role="button"
          tabindex="0"
          @click="viewCompany(company.id)"
          @keyup.enter="viewCompany(company.id)"
        >
          <div class="company-header">
            <div>
              <h3>{{ company.name }}</h3>
              <div class="muted">{{ company.category || 'Категория не указана' }}</div>
            </div>
          </div>
          <div class="company-meta">
            <div v-if="company.city">📍 {{ company.city }}</div>
            <div v-if="company.address">🏠 {{ company.address }}</div>
            <div v-if="company.phone">📞 {{ company.phone }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { API_URL } from '@/config';
import { formatApiError } from '@/utils/apiError';
import { useAuth } from '@/composables/useAuth';

const router = useRouter();
const route = useRoute();
const { isAuthenticated, getUserRole } = useAuth();

const searchQuery = ref(typeof route.query.search === 'string' ? route.query.search : '');
const selectedCategory = ref(typeof route.query.category === 'string' ? route.query.category : '');
const selectedCity = ref(typeof route.query.city === 'string' ? route.query.city : '');
const searching = ref(false);
const loading = ref(true);
const error = ref('');
const companies = ref([]);

onMounted(() => {
  performSearch();
});

function goDashboard() {
  if (!isAuthenticated()) {
    router.push('/login/user');
    return;
  }
  const role = getUserRole();
  if (role === 'company') {
    router.push('/dashboard/company');
    return;
  }
  if (role === 'manager' || role === 'admin') {
    router.push('/dashboard/manager');
    return;
  }
  router.push('/dashboard/user');
}

function buildQueryParams() {
  const params = new URLSearchParams();
  if (searchQuery.value.trim()) params.set('search', searchQuery.value.trim());
  if (selectedCategory.value.trim()) params.set('category', selectedCategory.value.trim());
  if (selectedCity.value.trim()) params.set('city', selectedCity.value.trim());
  return params;
}

async function performSearch() {
  searching.value = true;
  loading.value = true;
  error.value = '';

  const qs = buildQueryParams().toString();
  const url = qs ? `${API_URL}/companies?${qs}` : `${API_URL}/companies`;

  try {
    const response = await fetch(url);
    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(formatApiError(data));
    }

    companies.value = Array.isArray(data) ? data : [];
    await router.replace({
      path: '/search',
      query: Object.fromEntries(buildQueryParams()),
    });
  } catch (err) {
    error.value = err.message || 'Ошибка поиска';
    companies.value = [];
  } finally {
    searching.value = false;
    loading.value = false;
  }
}

function viewCompany(companyId) {
  router.push(`/company/${companyId}`);
}

function handleBack() {
  router.back();
}
</script>

<style scoped>
.search-page {
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

.search-bar {
  background: white;
  padding: 20px;
  border-radius: 15px;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.05);
  margin-bottom: 20px;
  display: flex;
  gap: 10px;
}

.search-bar input {
  flex: 1;
  padding: 12px;
  border-radius: 8px;
  border: 1px solid #d1d5db;
  font-size: 15px;
}

.search-bar button {
  padding: 12px 20px;
  border-radius: 8px;
  border: none;
  background: #2563eb;
  color: white;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.search-bar button:hover:not(:disabled) {
  background: #1e40af;
}

.search-bar button:disabled {
  background: #93c5fd;
  cursor: not-allowed;
}

.filters {
  display: flex;
  gap: 15px;
  margin-bottom: 30px;
  flex-wrap: wrap;
}

.filters input {
  flex: 1;
  min-width: 200px;
  padding: 10px;
  border-radius: 8px;
  border: 1px solid #d1d5db;
  background: white;
  font-size: 14px;
}

.results-title {
  margin-bottom: 20px;
  color: #1f2937;
}

.error-message {
  background: #fef2f2;
  color: #dc2626;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 20px;
  text-align: center;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #6b7280;
  background: white;
  border-radius: 20px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08);
}

.company-card {
  background: white;
  padding: 25px;
  border-radius: 20px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08);
  margin-bottom: 20px;
  cursor: pointer;
  transition: 0.3s;
  border: 2px solid transparent;
}

.company-card:hover {
  transform: translateY(-5px);
  border-color: #2563eb;
}

.company-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.company-header h3 {
  margin-bottom: 5px;
  color: #111827;
}

.muted {
  color: #6b7280;
  font-size: 14px;
}

.company-meta {
  margin-top: 15px;
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  color: #6b7280;
  font-size: 14px;
}

@media (max-width: 768px) {
  .filters {
    flex-direction: column;
  }

  header {
    padding: 15px 20px;
  }
}
</style>
