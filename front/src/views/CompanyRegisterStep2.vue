<template>
  <div class="register-page">
    <div class="container">
      <div class="progress">
        <div class="progress-bar" :style="{ width: '100%' }"></div>
      </div>
      
      <h1>Данные компании</h1>
      <div class="subtitle">Шаг 2 из 2 — Юридическая информация</div>

      <form @submit.prevent="handleStep2">
        <div class="form-group">
          <select 
            v-model="form.legalForm" 
            required
            :class="{ error: errors.legalForm }"
          >
            <option value="">Выберите форму собственности</option>
            <option value="ip">ИП</option>
            <option value="ooo">ООО</option>
            <option value="selfemployed">Самозанятый</option>
          </select>
          <span v-if="errors.legalForm" class="error-message">{{ errors.legalForm }}</span>
        </div>

        <div class="form-group">
          <input 
            v-model="form.inn" 
            type="text" 
            placeholder="ИНН" 
            required
            :class="{ error: errors.inn }"
          />
          <span v-if="errors.inn" class="error-message">{{ errors.inn }}</span>
        </div>

        <div class="form-group">
          <input 
            v-model="form.ogrn" 
            type="text" 
            placeholder="ОГРН / ОГРНИП" 
            required
            :class="{ error: errors.ogrn }"
          />
          <span v-if="errors.ogrn" class="error-message">{{ errors.ogrn }}</span>
        </div>

        <div class="form-group">
          <input 
            v-model="form.legalAddress" 
            type="text" 
            placeholder="Юридический адрес" 
            required
            :class="{ error: errors.legalAddress }"
          />
          <span v-if="errors.legalAddress" class="error-message">{{ errors.legalAddress }}</span>
        </div>

        <div class="form-group">
          <input 
            v-model="form.actualAddress" 
            type="text" 
            placeholder="Фактический адрес" 
            required
            :class="{ error: errors.actualAddress }"
          />
          <span v-if="errors.actualAddress" class="error-message">{{ errors.actualAddress }}</span>
        </div>

        <div class="form-group">
          <input 
            v-model="form.phone" 
            type="tel" 
            placeholder="Телефон компании" 
            required
            :class="{ error: errors.phone }"
          />
          <span v-if="errors.phone" class="error-message">{{ errors.phone }}</span>
        </div>

        <button type="submit" :disabled="loading">
          {{ loading ? 'Регистрация...' : 'Завершить регистрацию' }}
        </button>
      </form>

      <div v-if="serverError" class="server-error">
        {{ serverError }}
      </div>

      <div class="footer-link">
        <router-link to="/register/company/step1">← Назад</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuth } from '@/composables/useAuth';

const router = useRouter();
const { register } = useAuth();

const loading = ref(false);
const serverError = ref('');
const errors = reactive({
  legalForm: '', inn: '', ogrn: '', legalAddress: '', actualAddress: '', phone: ''
});

const form = reactive({
  legalForm: '',
  inn: '',
  ogrn: '',
  legalAddress: '',
  actualAddress: '',
  phone: ''
});

const step1Data = ref({
  companyName: '',
  email: '',
  password: ''
});

onMounted(() => {
  // Загружаем данные из шага 1
  const saved = sessionStorage.getItem('companyRegisterData');
  if (saved) {
    step1Data.value = JSON.parse(saved);
  } else {
    // Если нет данных шага 1, возвращаем назад
    router.push('/register/company/step1');
  }
});

const validateForm = () => {
  errors.legalForm = '';
  errors.inn = '';
  errors.ogrn = '';
  errors.legalAddress = '';
  errors.actualAddress = '';
  errors.phone = '';
  let isValid = true;

  if (!form.legalForm) {
    errors.legalForm = 'Выберите форму собственности';
    isValid = false;
  }

  if (!form.inn) {
    errors.inn = 'Введите ИНН';
    isValid = false;
  }

  if (!form.ogrn) {
    errors.ogrn = 'Введите ОГРН';
    isValid = false;
  }

  if (!form.legalAddress) {
    errors.legalAddress = 'Введите юридический адрес';
    isValid = false;
  }

  if (!form.actualAddress) {
    errors.actualAddress = 'Введите фактический адрес';
    isValid = false;
  }

  if (!form.phone) {
    errors.phone = 'Введите телефон';
    isValid = false;
  }

  return isValid;
};

const handleStep2 = async () => {
  serverError.value = '';
  
  if (!validateForm()) return;

  loading.value = true;

  try {
    // Объединяем данные шага 1 и шага 2
    const registerData = {
      email: step1Data.value.email,
      password: step1Data.value.password,
      company_name: step1Data.value.companyName,
      // Дополнительные данные компании можно отправить отдельно
      // или сохранить в профиль после регистрации
    };

    const response = await register(
      registerData.email,
      registerData.password,
      registerData.company_name
    );

    // Очищаем sessionStorage
    sessionStorage.removeItem('companyRegisterData');

    localStorage.setItem('access_token', response.access_token);
    localStorage.setItem('user_role', 'company');

    router.push('/dashboard/company');
  } catch (error) {
    serverError.value = error.message || 'Ошибка регистрации. Попробуйте другой email.';
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.register-page {
  font-family: "Segoe UI", Arial, sans-serif;
  background: linear-gradient(135deg, #065f46, #16a34a);
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 30px 20px;
}

.container {
  width: 600px;
  max-width: 95%;
  background: white;
  padding: 40px;
  border-radius: 20px;
  box-shadow: 0 20px 40px rgba(0,0,0,0.2);
}

.progress {
  height: 8px;
  background: #e5e7eb;
  border-radius: 10px;
  margin-bottom: 25px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background: #16a34a;
  transition: width 0.3s ease;
}

h1 {
  text-align: center;
  margin-bottom: 10px;
  color: #1f2937;
}

.subtitle {
  text-align: center;
  color: #6b7280;
  margin-bottom: 25px;
}

.form-group {
  margin-bottom: 15px;
}

input,
select {
  width: 100%;
  padding: 12px;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  font-size: 14px;
  transition: border-color 0.2s;
  background: white;
}

input:focus,
select:focus {
  outline: none;
  border-color: #16a34a;
}

input.error,
select.error {
  border-color: #ef4444;
}

.error-message {
  color: #ef4444;
  font-size: 12px;
  margin-top: 5px;
  display: block;
}

button {
  width: 100%;
  padding: 12px;
  border-radius: 10px;
  border: none;
  background: #16a34a;
  color: white;
  font-weight: 500;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;
}

button:hover:not(:disabled) {
  background: #15803d;
}

button:disabled {
  background: #86efac;
  cursor: not-allowed;
}

.server-error {
  background: #fef2f2;
  color: #dc2626;
  padding: 10px;
  border-radius: 8px;
  margin-bottom: 15px;
  font-size: 14px;
  text-align: center;
}

.footer-link {
  text-align: center;
  margin-top: 20px;
  font-size: 14px;
}

.footer-link a {
  color: #16a34a;
  text-decoration: none;
}

.footer-link a:hover {
  text-decoration: underline;
}
</style>