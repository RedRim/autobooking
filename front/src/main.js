// src/main.js
import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import { useAuth } from './composables/useAuth';

const app = createApp(App);

// Инициализируем авторизацию перед монтированием
const { initAuth } = useAuth();
initAuth().finally(() => {
  app.use(router).mount('#app');
});