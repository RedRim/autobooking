<template>
  <div class="login-page">
    <div class="container">
      <h1>Вход для компании</h1>
      <div class="subtitle">Панель владельца AutoBooking</div>

      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <input 
            v-model="form.email" 
            type="email" 
            placeholder="Email компании" 
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

        <button type="submit" :disabled="loading">
          {{ loading ? 'Вход...' : 'Войти в панель' }}
        </button>
      </form>

      <div v-if="serverError" class="server-error">
        {{ serverError }}
      </div>

      <div class="footer-link">
        Нет аккаунта?
        <router-link to="/register/company">Зарегистрировать компанию</router-link>
      </div>

      <div class="footer-link">
        <router-link to="/">← На главную</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuth } from '@/composables/useAuth';

const router = useRouter();
const route = useRoute();
const { login, user } = useAuth();

const loading = ref(false);
const serverError = ref('');
const errors = reactive({ email: '', password: '' });

const form = reactive({
  email: '',
  password: ''
});

const validateForm = () => {
  errors.email = '';
  errors.password = '';
  let isValid = true;

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

  return isValid;
};

const handleLogin = async () => {
  serverError.value = '';
  
  if (!validateForm()) return;

  loading.value = true;

  try {
    await login(form.email, form.password);
    const role = localStorage.getItem('user_role');

    if (role !== 'company') {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user_role');
      user.value = null;
      serverError.value = 'Этот аккаунт не является аккаунтом владельца компании.';
      return;
    }

    const raw = typeof route.query.redirect === 'string' ? route.query.redirect : '';
    const safe = raw.startsWith('/') && !raw.startsWith('//') ? raw : '/dashboard/company';
    router.push(safe);
  } catch (error) {
    serverError.value = error.message || 'Ошибка входа. Проверьте данные.';
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.login-page {
  font-family: "Segoe UI", Arial, sans-serif;
  background: linear-gradient(135deg, #065f46, #16a34a);
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
}

.container {
  width: 420px;
  max-width: 95%;
  background: white;
  padding: 40px;
  border-radius: 20px;
  box-shadow: 0 20px 40px rgba(0,0,0,0.2);
}

h1 {
  text-align: center;
  margin-bottom: 10px;
  color: #1f2937;
}

.subtitle {
  text-align: center;
  color: #6b7280;
  margin-bottom: 30px;
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