<template>
  <div class="register-page">
    <div class="container">
      <div class="progress">
        <div class="progress-bar" :style="{ width: '100%' }"></div>
      </div>
      
      <h1>Регистрация компании</h1>
      <div class="subtitle">Создайте аккаунт владельца бизнеса</div>

      <form @submit.prevent="handleRegister">
        <div class="form-group">
          <input 
            v-model="form.companyName" 
            type="text" 
            placeholder="Название компании" 
            required
            :class="{ error: errors.companyName }"
          />
          <span v-if="errors.companyName" class="error-message">{{ errors.companyName }}</span>
        </div>

        <div class="form-group">
          <input 
            v-model="form.email" 
            type="email" 
            placeholder="Email (логин)" 
            required
            :class="{ error: errors.email }"
          />
          <span v-if="errors.email" class="error-message">{{ errors.email }}</span>
        </div>

        <div class="form-group">
          <input 
            v-model="form.password" 
            type="password" 
            placeholder="Пароль" 
            required
            :class="{ error: errors.password }"
          />
          <span v-if="errors.password" class="error-message">{{ errors.password }}</span>
        </div>

        <div class="form-group">
          <input 
            v-model="form.confirmPassword" 
            type="password" 
            placeholder="Повторите пароль" 
            required
            :class="{ error: errors.confirmPassword }"
          />
          <span v-if="errors.confirmPassword" class="error-message">{{ errors.confirmPassword }}</span>
        </div>

        <button type="submit" :disabled="loading">
          {{ loading ? 'Регистрация...' : 'Зарегистрировать компанию' }}
        </button>
      </form>

      <div v-if="serverError" class="server-error">
        {{ serverError }}
      </div>

      <div v-if="serverSuccess" class="success-message">
        Регистрация успешна! Перенаправляем...
      </div>

      <div class="footer-link">
        Уже есть аккаунт? <router-link to="/login/company">Войти</router-link>
      </div>

      <div class="footer-link">
        <router-link to="/">← На главную</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { useAuth } from '@/composables/useAuth';

const router = useRouter();
const { register } = useAuth();

const loading = ref(false);
const serverError = ref('');
const serverSuccess = ref(false);
const errors = reactive({ companyName: '', email: '', password: '', confirmPassword: '' });

const form = reactive({
  companyName: '',
  email: '',
  password: '',
  confirmPassword: ''
});

const validateForm = () => {
  errors.companyName = '';
  errors.email = '';
  errors.password = '';
  errors.confirmPassword = '';
  let isValid = true;

  if (!form.companyName) {
    errors.companyName = 'Введите название компании';
    isValid = false;
  }

  if (!form.email) {
    errors.email = 'Введите email';
    isValid = false;
  } else if (!/\S+@\S+\.\S+/.test(form.email)) {
    errors.email = 'Некорректный email';
    isValid = false;
  }

  if (!form.password) {
    errors.password = 'Введите пароль';
    isValid = false;
  } else if (form.password.length < 4) {
    errors.password = 'Пароль должен быть не менее 4 символов';
    isValid = false;
  }

  if (form.password !== form.confirmPassword) {
    errors.confirmPassword = 'Пароли не совпадают';
    isValid = false;
  }

  return isValid;
};

const handleRegister = async () => {
  serverError.value = '';
  serverSuccess.value = false;
  
  if (!validateForm()) return;

  loading.value = true;

  try {
    // Вызываем API регистрации с company_name
    await register(form.email, form.password, form.companyName);

    serverSuccess.value = true;
    
    // Перенаправляем в панель компании после небольшой задержки
    setTimeout(() => {
      router.push('/dashboard/company');
    }, 1500);
    
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
  padding: 20px;
}

.container {
  width: 480px;
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

input {
  width: 100%;
  padding: 12px;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  font-size: 14px;
  transition: border-color 0.2s;
}

input:focus {
  outline: none;
  border-color: #16a34a;
}

input.error {
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

.success-message {
  background: #dcfce7;
  color: #166534;
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