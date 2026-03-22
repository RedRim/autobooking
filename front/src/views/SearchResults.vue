<template>
  <div class="search-page">
    <header>
      <div class="logo">AutoBooking</div>
      <div class="nav">
        <button @click="router.push('/dashboard/user')">Мои записи</button>
        <button @click="handleBack">Назад</button>
      </div>
    </header>

    <div class="container">
      <!-- Поиск -->
      <div class="search-bar">
        <input 
          v-model="searchQuery" 
          type="text" 
          placeholder="Название компании или услуги"
          @keyup.enter="performSearch"
        />
        <button @click="performSearch" :disabled="searching">
          {{ searching ? 'Поиск...' : 'Найти' }}
        </button>
      </div>

      <!-- Фильтры -->
      <div class="filters">
        <select v-model="selectedCategory" @change="performSearch">
          <option value="">Все категории</option>
          <option value="auto">Автосервис</option>
          <option value="tire">Шиномонтаж</option>
          <option value="detailing">Детейлинг</option>
          <option value="wash">Мойка</option>
          <option value="barber">Барбершоп</option>
          <option value="beauty">Салон красоты</option>
        </select>
        <select v-model="selectedCity" @change="performSearch">
          <option value="">Все города</option>
          <option value="moscow">Москва</option>
          <option value="spb">Санкт-Петербург</option>
        </select>
      </div>

      <!-- Результаты -->
      <h2 class="results-title">
        {{ loading ? 'Поиск...' : `Найдено ${companies.length} компаний` }}
      </h2>

      <div v-if="error" class="error-message">{{ error }}</div>
      <div v-else-if="!loading && companies.length === 0" class="empty-state">
        Ничего не найдено. Попробуйте изменить параметры поиска.
      </div>

      <div v-else class="results-list">
        <div 
          v-for="company in companies" 
          :key="company.id" 
          class="company-card"
          @click="viewCompany(company.id)"
        >
          <div class="company-header">
            <div>
              <h3>{{ company.name }}</h3>
              <div>{{ company.category }}</div>
            </div>
            <div class="rating">⭐ 4.8</div>
          </div>
          <div class="company-description">{{ company.description }}</div>
          <div class="company-meta">
            <div>📍 {{ company.city || 'г. Москва' }}</div>
            <div>🕒 Открыто до 18:00</div>
            <div>💰 от {{ formatMinPrice(company.services) }} ₽</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';

const router = useRouter();
const route = useRoute();

const searchQuery = ref(route.query.q || '');
const selectedCategory = ref(route.query.category || '');
const selectedCity = ref(route.query.city || '');
const searching = ref(false);
const loading = ref(true);
const error = ref('');
const companies = ref([]);

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

onMounted(() => {
  performSearch();
});

const performSearch = async () => {
  searching.value = true;
  loading.value = true;
  error.value = '';

  try {
    // Формируем параметры запроса
    const params = new URLSearchParams();
    if (searchQuery.value) params.append('q', searchQuery.value);
    if (selectedCategory.value) params.append('category', selectedCategory.value);
    if (selectedCity.value) params.append('city', selectedCity.value);

    const response = await fetch(`${API_URL}/companies/search?${params}`);
    
    if (!response.ok) throw new Error('Ошибка поиска');
    companies.value = await response.json();
  } catch (err) {
    error.value = err.message;
    // Заглушка для демо
    companies.value = [
      { id: 1, name: 'AutoFix Service', category: 'Автосервис', description: 'Профессиональный ремонт автомобилей любой сложности.', city: 'Москва', services: [{ price: 1500 }] },
      { id: 2, name: 'ProCar Service', category: 'Диагностика и ремонт', description: 'Быстрая диагностика и гарантия на все виды работ.', city: 'Москва', services: [{ price: 1200 }] },
      { id: 3, name: 'CarMaster', category: 'Комплексный автосервис', description: 'Более 15 лет опыта. Современное оборудование.', city: 'Москва', services: [{ price: 1800 }] },
    ];
  } finally {
    searching.value = false;
    loading.value = false;
  }
};

const viewCompany = (companyId) => {
  router.push(`/company/${companyId}`);
};

const handleBack = () => {
  router.back();
};

const formatMinPrice = (services) => {
  if (!services || services.length === 0) return '0';
  const min = Math.min(...services.map(s => s.price || 0));
  return new Intl.NumberFormat('ru-RU').format(min);
};
</script>

<style scoped>
.search-page { font-family: "Segoe UI", Arial, sans-serif; background: #f5f7fa; min-height: 100vh; }
header { background: linear-gradient(135deg, #1e3a8a, #2563eb); color: white; padding: 20px 50px; display: flex; justify-content: space-between; align-items: center; }
.logo { font-size: 22px; font-weight: bold; }
.nav { display: flex; gap: 10px; }
.nav button { padding: 8px 15px; border-radius: 8px; border: none; cursor: pointer; background: white; color: #1e3a8a; font-weight: 500; }
.nav button:hover { background: #f3f4f6; }
.container { width: 1100px; max-width: 95%; margin: 40px auto; }
.search-bar { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 5px 15px rgba(0,0,0,0.05); margin-bottom: 20px; display: flex; gap: 10px; }
.search-bar input { flex: 1; padding: 12px; border-radius: 8px; border: 1px solid #d1d5db; font-size: 15px; }
.search-bar button { padding: 12px 20px; border-radius: 8px; border: none; background: #2563eb; color: white; font-weight: 500; cursor: pointer; transition: background 0.2s; }
.search-bar button:hover:not(:disabled) { background: #1e40af; }
.search-bar button:disabled { background: #93c5fd; cursor: not-allowed; }
.filters { display: flex; gap: 15px; margin-bottom: 30px; }
.filters select { padding: 10px; border-radius: 8px; border: 1px solid #d1d5db; background: white; font-size: 14px; }
.results-title { margin-bottom: 20px; color: #1f2937; }
.error-message { background: #fef2f2; color: #dc2626; padding: 12px; border-radius: 8px; margin-bottom: 20px; text-align: center; }
.empty-state { text-align: center; padding: 40px; color: #6b7280; background: white; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.08); }
.company-card { background: white; padding: 25px; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.08); margin-bottom: 20px; cursor: pointer; transition: 0.3s; }
.company-card:hover { transform: translateY(-5px); border: 2px solid #2563eb; }
.company-header { display: flex; justify-content: space-between; align-items: center; }
.company-header h3 { margin-bottom: 5px; color: #111827; }
.company-header div:last-child { color: #6b7280; font-size: 14px; }
.rating { background: #2563eb; color: white; padding: 6px 10px; border-radius: 8px; font-size: 14px; }
.company-description { margin-top: 10px; color: #6b7280; }
.company-meta { margin-top: 15px; display: flex; gap: 30px; color: #6b7280; font-size: 14px; }
@media (max-width: 768px) { .filters { flex-direction: column; } .company-meta { flex-wrap: wrap; gap: 10px; } header { padding: 15px 20px; } }
</style>