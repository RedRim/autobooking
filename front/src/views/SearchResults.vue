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
  <div class="search-input-wrapper">
    <input
      v-model="searchQuery"
      type="text"
      placeholder="Название компании"
      @input="onSearchInput"
      @focus="showDropdown = true"
      @blur="handleBlur"
      @keyup.enter="performSearch"
    />
    <ul v-if="showDropdown && suggestions.length > 0" class="suggestions-dropdown">
      <li
        v-for="comp in suggestions"
        :key="comp.id"
        @mousedown="selectSuggestion(comp)"
      >
        <strong>{{ comp.name }}</strong>
        <span v-if="comp.category" class="muted-suggestion"> · {{ comp.category }}</span>
      </li>
    </ul>
  </div>
  <button type="button" @click="performSearch" :disabled="searching">
    {{ searching ? 'Поиск...' : 'Найти' }}
  </button>
</div>

      <div class="filters">
        <input
          v-model="selectedCategory"
          type="text"
          placeholder="Категория (точное совпадение, например Барбершоп)"
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

// Добавьте рядом с другими ref
const suggestions = ref([]);
const showDropdown = ref(false);
let debounceTimer = null;

function onSearchInput() {
  showDropdown.value = true;
  clearTimeout(debounceTimer);
  
  if (!searchQuery.value.trim()) {
    suggestions.value = [];
    return;
  }
  debounceTimer = setTimeout(fetchSuggestions, 300);
}

async function fetchSuggestions() {
  if (!searchQuery.value.trim()) return;
  try {
    const response = await fetch(`${API_URL}/companies?search=${encodeURIComponent(searchQuery.value.trim())}`);
    if (response.ok) {
      const data = await response.json();
      suggestions.value = (Array.isArray(data) ? data : []).slice(0, 5);
    } else {
      suggestions.value = [];
    }
  } catch {
    suggestions.value = [];
  }
}

function selectSuggestion(comp) {
  searchQuery.value = comp.name;
  showDropdown.value = false;
  suggestions.value = [];
  viewCompany(comp.id); // Сразу переходим на страницу компании
}

function handleBlur() {
  // Задержка, чтобы клик по списку успел сработать до закрытия
  setTimeout(() => {
    showDropdown.value = false;
  }, 150);
}

onMounted(() => {
  performSearch();
});

function goDashboard() {
  if (!isAuthenticated()) {
    router.push('/login/user');
    return;
  }
  router.push(getUserRole() === 'company' ? '/dashboard/company' : '/dashboard/user');
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

/* Замените оригинальный .search-bar input на этот */
.search-input-wrapper {
  flex: 1;
  position: relative;
}

.search-input-wrapper input {
  width: 100%;
  box-sizing: border-box;
  padding: 12px;
  border-radius: 8px;
  border: 1px solid #d1d5db;
  font-size: 15px;
}

/* Стили выпадающего списка */
.suggestions-dropdown {
  position: absolute;
  top: calc(100% + 5px);
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  list-style: none;
  margin: 0;
  padding: 5px 0;
  max-height: 200px;
  overflow-y: auto;
  z-index: 100;
}

.suggestions-dropdown li {
  padding: 10px 15px;
  cursor: pointer;
  font-size: 14px;
  color: #1f2937;
  transition: background 0.15s;
}

.suggestions-dropdown li:hover {
  background: #f3f4f6;
}

.muted-suggestion {
  color: #6b7280;
  font-size: 13px;
  margin-left: 6px;
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
