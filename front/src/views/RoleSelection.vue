<template>
  <div class="role-page">
    <div class="container">
      <h1>Добро пожаловать в AutoBooking</h1>
      <div class="subtitle">
        Выберите, как вы хотите использовать платформу
      </div>

      <div class="role-selection">
        <!-- Карточка Клиента -->
        <div class="role-card" @click="selectRole('client')">
          <h2>Я клиент</h2>
          <p>Хочу записаться на услугу: салон, барбершоп, массаж, авто-сервис и многое другое</p>
          <button class="buy-btn" @click.stop="navigateTo('/login/user')">Найти услуги</button>
        </div>

        <!-- Карточка Владельца -->
        <div class="role-card" @click="selectRole('business')">
          <h2>Я владелец бизнеса</h2>
          <p>Хочу добавить свою компанию и принимать онлайн-записи клиентов</p>
          <button class="sell-btn" @click.stop="navigateTo('/login/company')">Добавить компанию</button>
        </div>
      </div>

      <div class="footer">
        © 2026 AutoBooking. Онлайн запись на услуги.
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';

const router = useRouter();

const selectRole = (role) => {
  console.log(`Выбрана роль: ${role}`);
};

const navigateTo = (path) => {
  router.push(path);
};
</script>

<style scoped>
.role-page {
  font-family: "Segoe UI", Arial, sans-serif;
  background: linear-gradient(135deg, #1e3a8a, #2563eb);
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  color: #111827;
}

.container {
  background: white;
  width: 900px;
  max-width: 95%;
  padding: 50px;
  border-radius: 20px;
  box-shadow: 0 20px 40px rgba(0,0,0,0.2);
  text-align: center;
}

h1 {
  margin-bottom: 15px;
  font-size: 32px;
  color: #1f2937;
}

.subtitle {
  margin-bottom: 40px;
  color: #6b7280;
  font-size: 16px;
}

.role-selection {
  display: flex;
  gap: 30px;
  justify-content: center;
  flex-wrap: wrap;
}

.role-card {
  flex: 1;
  min-width: 280px;
  padding: 40px 30px;
  border-radius: 15px;
  border: 2px solid #e5e7eb;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.role-card:hover {
  transform: translateY(-8px);
  border-color: #2563eb;
  box-shadow: 0 15px 30px rgba(0,0,0,0.1);
}

.role-card h2 {
  margin-bottom: 15px;
  color: #111827;
}

.role-card p {
  color: #6b7280;
  margin-bottom: 25px;
  flex-grow: 1;
}

button {
  padding: 12px 20px;
  border-radius: 10px;
  border: none;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
  width: 100%;
}

.buy-btn {
  background: #2563eb;
  color: white;
}

.buy-btn:hover {
  background: #1e40af;
}

.sell-btn {
  background: #16a34a;
  color: white;
}

.sell-btn:hover {
  background: #15803d;
}

.footer {
  margin-top: 40px;
  font-size: 14px;
  color: #9ca3af;
}
</style>