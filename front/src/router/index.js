import { createRouter, createWebHistory } from 'vue-router';

// Импорты
import RoleSelection from '@/views/RoleSelection.vue';
import UserLogin from '@/views/UserLogin.vue';
import CompanyLogin from '@/views/CompanyLogin.vue';
import UserRegister from '@/views/UserRegister.vue';
import CompanyRegisterStep1 from '@/views/CompanyRegisterStep1.vue';
import UserDashboard from '@/views/UserDashboard.vue';
import CompanyDashboard from '@/views/CompanyDashboard.vue';
import CompanyCalendar from '@/views/CompanyCalendar.vue';
import CompanyServices from '@/views/CompanyServices.vue';
import UserBookings from '@/views/UserBookings.vue';
import CompanyDetails from '@/views/CompanyDetails.vue';
import SearchResults from '@/views/SearchResults.vue';
import BookingForm from '@/views/BookingForm.vue';

const routes = [
  { path: '/', name: 'Index', component: RoleSelection },
  { path: '/login/user', name: 'UserLogin', component: UserLogin },
  { path: '/login/company', name: 'CompanyLogin', component: CompanyLogin },
  { path: '/register/user', name: 'UserRegister', component: UserRegister },
  { path: '/register/company', name: 'CompanyRegister', component: CompanyRegisterStep1 },
  
  // Клиент
  { path: '/dashboard/user', name: 'UserDashboard', component: UserDashboard, meta: { requiresAuth: true, role: 'user' } },
  { path: '/bookings', name: 'UserBookings', component: UserBookings, meta: { requiresAuth: true, role: 'user' } },
  { path: '/search', name: 'SearchResults', component: SearchResults },
  { path: '/company/:id', name: 'CompanyDetails', component: CompanyDetails },
  { path: '/booking/:serviceId', name: 'BookingForm', component: BookingForm, meta: { requiresAuth: true } },
  
  // Компания
  { path: '/dashboard/company', name: 'CompanyDashboard', component: CompanyDashboard, meta: { requiresAuth: true, role: 'company' } },
  { path: '/company/bookings', name: 'CompanyBookings', component: CompanyDashboard, meta: { requiresAuth: true, role: 'company' } },
  { path: '/company/calendar', name: 'CompanyCalendar', component: CompanyCalendar, meta: { requiresAuth: true, role: 'company' } },
  { path: '/company/services', name: 'CompanyServices', component: CompanyServices, meta: { requiresAuth: true, role: 'company' } },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// Guard
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access_token');
  const role = localStorage.getItem('user_role');

  if (to.meta.requiresAuth && !token) {
    next('/login/user');
    return;
  }

  if (to.meta.role && to.meta.role !== role) {
    next(role === 'company' ? '/dashboard/company' : '/dashboard/user');
    return;
  }

  next();
});

export default router;