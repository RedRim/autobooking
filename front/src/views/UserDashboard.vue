<template>
  <div class="dashboard-page">
    <header>
      <div class="logo">AutoBooking</div>
      <div class="nav">
        <span class="user-info">{{ user?.email }}</span>
        <button type="button" @click="router.push('/search')">Поиск компаний</button>
        <button type="button" @click="router.push('/bookings')">Мои записи</button>
        <button type="button" @click="handleLogout">Выйти</button>
      </div>
    </header>

    <div class="container">
      <h1>Найдите услугу и запишитесь онлайн</h1>
      <div class="subtitle">Быстро. Удобно. Без звонков.</div>

      <div class="search-box">
        <input
          v-model="search.query"
          type="text"
          placeholder="Название компании"
        />
        <div class="category-input-wrapper">
          <input
            v-model="search.category"
            type="text"
            placeholder="Категория (необязательно)"
            @input="onCategoryInput"
            @focus="onCategoryFocus"
            @blur="handleCategoryBlur"
          />
          <ul
            v-if="showCategoryDropdown && categorySuggestions.length > 0"
            class="suggestions-dropdown"
          >
            <li
              v-for="category in categorySuggestions"
              :key="category.id"
              @mousedown="selectCategorySuggestion(category)"
            >
              <strong>{{ category.name }}</strong>
            </li>
          </ul>
        </div>
        <div class="city-input-wrapper">
          <input
            v-model="search.city"
            type="text"
            placeholder="Город (необязательно)"
            @input="onCityInput"
            @focus="onCityFocus"
            @blur="handleCityBlur"
          />
          <ul v-if="showCityDropdown && citySuggestions.length > 0" class="suggestions-dropdown">
            <li
              v-for="city in citySuggestions"
              :key="city.name"
              @mousedown="selectCitySuggestion(city)"
            >
              <strong>{{ city.name }}</strong>
            </li>
          </ul>
        </div>
        <button type="button" @click="goSearch" :disabled="searchLoading">
          {{ searchLoading ? '...' : 'Найти' }}
        </button>
      </div>

      <div class="section" v-if="bookingsLoading">
        <h2>Ближайшие записи</h2>
        <p class="muted">Загрузка...</p>
      </div>

      <div class="section" v-else-if="upcomingBookings.length > 0">
        <h2>Ближайшие записи</h2>
        <div class="sort-controls">
          <label for="upcomingSort">Сортировка:</label>
          <select id="upcomingSort" v-model="upcomingSortKey">
            <option value="startAsc">Дата записи ↑</option>
            <option value="startDesc">Дата записи ↓</option>
          </select>
        </div>
        <div
          v-for="booking in upcomingBookings"
          :key="booking.id"
          class="booking-card"
        >
          <div>
            <strong>{{ metaLabel(booking.company_id, 'company') }}</strong>
            <br />
            {{ metaLabel(booking.service_id, 'service', booking.company_id) }}
            <br />
            {{ formatDate(booking.start_at) }} • {{ formatTime(booking.start_at) }}
          </div>
          <button
            v-if="booking.status === 'pending' || booking.status === 'confirmed'"
            type="button"
            class="cancel-btn"
            :disabled="cancellingId === booking.id"
            @click="cancelBooking(booking.id)"
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
import { computed, onMounted, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';

import { API_URL } from '@/config';
import { formatApiError } from '@/utils/apiError';
import { useAuth } from '@/composables/useAuth';

const router = useRouter();
const { user, logout, fetchCurrentUser } = useAuth();

const searchLoading = ref(false);
const bookingsLoading = ref(false);
const error = ref('');
const cancellingId = ref(null);
const bookings = ref([]);
const companyNames = ref({});
const serviceNames = ref({});
const upcomingSortKey = ref('startAsc');
const categorySuggestions = ref([]);
const showCategoryDropdown = ref(false);
let categoryDebounceTimer = null;
const citySuggestions = ref([]);
const showCityDropdown = ref(false);
let cityDebounceTimer = null;

const search = reactive({
  query: '',
  category: '',
  city: '',
});

function toMs(dateString) {
  const t = new Date(dateString).getTime();
  return Number.isFinite(t) ? t : 0;
}

const upcomingBookings = computed(() => {
  const now = Date.now();
  const list = bookings.value.filter((b) => b.status !== 'cancelled' && toMs(b.start_at) >= now);

  switch (upcomingSortKey.value) {
    case 'startDesc':
      return list
        .sort((a, b) => {
          const as = toMs(a.start_at);
          const bs = toMs(b.start_at);
          if (as !== bs) return bs - as;
          return toMs(b.created_at) - toMs(a.created_at);
        })
        .slice(0, 5);
    case 'startAsc':
    default:
      return list
        .sort((a, b) => {
          const as = toMs(a.start_at);
          const bs = toMs(b.start_at);
          if (as !== bs) return as - bs;
          return toMs(b.created_at) - toMs(a.created_at);
        })
        .slice(0, 5);
  }
});

onMounted(async () => {
  try {
    await fetchCurrentUser();
  } catch (err) {
    error.value = err.message;
  }
  await loadBookings();
});

function goSearch() {
  searchLoading.value = true;
  router
    .push({
      path: '/search',
      query: {
        ...(search.query.trim() ? { search: search.query.trim() } : {}),
        ...(search.category.trim() ? { category: search.category.trim() } : {}),
        ...(search.city.trim() ? { city: search.city.trim() } : {}),
      },
    })
    .finally(() => {
      searchLoading.value = false;
    });
}

function onCategoryInput() {
  showCategoryDropdown.value = true;
  clearTimeout(categoryDebounceTimer);
  categoryDebounceTimer = setTimeout(() => {
    fetchCategorySuggestions(search.category.trim());
  }, 300);
}

async function fetchCategorySuggestions(query = '') {
  const params = new URLSearchParams({ limit: '50' });
  if (query) {
    params.set('search', query);
  }

  try {
    const response = await fetch(`${API_URL}/categories?${params.toString()}`);
    if (response.ok) {
      const data = await response.json().catch(() => []);
      categorySuggestions.value = Array.isArray(data) ? data : [];
    } else {
      categorySuggestions.value = [];
    }
  } catch {
    categorySuggestions.value = [];
  }
}

async function onCategoryFocus() {
  showCategoryDropdown.value = true;
  if (categorySuggestions.value.length > 0) {
    return;
  }
  await fetchCategorySuggestions(search.category.trim());
}

function selectCategorySuggestion(category) {
  search.category = category.name;
  showCategoryDropdown.value = false;
  categorySuggestions.value = [];
}

function handleCategoryBlur() {
  setTimeout(() => {
    showCategoryDropdown.value = false;
  }, 150);
}

function onCityInput() {
  showCityDropdown.value = true;
  clearTimeout(cityDebounceTimer);
  cityDebounceTimer = setTimeout(() => {
    fetchCitySuggestions(search.city.trim());
  }, 300);
}

async function fetchCitySuggestions(query = '') {
  const params = new URLSearchParams();
  if (query) {
    params.set('search', query);
  }
  try {
    const response = await fetch(`${API_URL}/cities?${params.toString()}`);
    if (response.ok) {
      const data = await response.json().catch(() => []);
      citySuggestions.value = Array.isArray(data) ? data : [];
    } else {
      citySuggestions.value = [];
    }
  } catch {
    citySuggestions.value = [];
  }
}

async function onCityFocus() {
  showCityDropdown.value = true;
  if (citySuggestions.value.length > 0) {
    return;
  }
  await fetchCitySuggestions(search.city.trim());
}

function selectCitySuggestion(city) {
  search.city = city.name;
  showCityDropdown.value = false;
  citySuggestions.value = [];
}

function handleCityBlur() {
  setTimeout(() => {
    showCityDropdown.value = false;
  }, 150);
}

async function loadBookings() {
  bookingsLoading.value = true;
  error.value = '';

  const token = localStorage.getItem('access_token');
  if (!token) {
    bookingsLoading.value = false;
    return;
  }

  try {
    const response = await fetch(`${API_URL}/bookings/my`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(formatApiError(data));
    }

    bookings.value = Array.isArray(data) ? data : [];
    await enrichBookingMeta(bookings.value);
  } catch (err) {
    error.value = err.message;
    bookings.value = [];
  } finally {
    bookingsLoading.value = false;
  }
}

async function enrichBookingMeta(list) {
  const companyIds = [...new Set(list.map((b) => b.company_id))];

  await Promise.all(
    companyIds.map(async (id) => {
      try {
        const res = await fetch(`${API_URL}/companies/${id}`);
        if (!res.ok) return;
        const company = await res.json();
        companyNames.value[id] = company.name;
        (company.services || []).forEach((s) => {
          const key = `${id}:${s.id}`;
          serviceNames.value[key] = s.name;
        });
      } catch {
        /* ignore */
      }
    }),
  );
}

function metaLabel(serviceOrCompanyId, kind, companyIdForService = null) {
  if (kind === 'company') {
    return companyNames.value[serviceOrCompanyId] || `Компания #${serviceOrCompanyId}`;
  }
  const key = `${companyIdForService}:${serviceOrCompanyId}`;
  return serviceNames.value[key] || `Услуга #${serviceOrCompanyId}`;
}

async function cancelBooking(bookingId) {
  if (!confirm('Отменить запись?')) return;

  cancellingId.value = bookingId;

  try {
    const token = localStorage.getItem('access_token');
    const response = await fetch(`${API_URL}/bookings/${bookingId}/cancel`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(formatApiError(data));
    }

    const booking = bookings.value.find((b) => b.id === bookingId);
    if (booking) booking.status = 'cancelled';
  } catch (err) {
    error.value = err.message;
  } finally {
    cancellingId.value = null;
  }
}

function handleLogout() {
  logout();
}

function formatDate(dateString) {
  return new Date(dateString).toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
  });
}

function formatTime(dateString) {
  return new Date(dateString).toLocaleTimeString('ru-RU', {
    hour: '2-digit',
    minute: '2-digit',
  });
}
</script>

<style scoped>
.dashboard-page {
  font-family: 'Segoe UI', Arial, sans-serif;
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
  flex-wrap: wrap;
}

.user-info {
  font-size: 19px;
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
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
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
  flex-wrap: wrap;
}

.search-box input {
  flex: 1;
  min-width: 160px;
  padding: 12px;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  font-size: 14px;
}

.category-input-wrapper,
.city-input-wrapper {
  flex: 1;
  min-width: 160px;
  position: relative;
}

.category-input-wrapper input,
.city-input-wrapper input {
  width: 100%;
  box-sizing: border-box;
}

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

.section {
  margin-top: 50px;
}

.section h2 {
  margin-bottom: 20px;
  font-size: 20px;
}

.muted {
  color: #6b7280;
}

.sort-controls {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 18px;
}

.sort-controls label {
  color: #374151;
  font-weight: 500;
  font-size: 14px;
}

.sort-controls select {
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  font-size: 14px;
  background: white;
}

.booking-card {
  background: #f3f4f6;
  padding: 15px;
  border-radius: 12px;
  margin-top: 15px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.cancel-btn {
  padding: 6px 12px;
  border-radius: 8px;
  border: none;
  background: #ef4444;
  color: white;
  cursor: pointer;
  font-size: 13px;
  transition: background 0.2s;
}

.cancel-btn:hover:not(:disabled) {
  background: #dc2626;
}

.cancel-btn:disabled {
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
  header {
    padding: 15px 20px;
  }

  .search-box {
    flex-direction: column;
  }
}
</style>
