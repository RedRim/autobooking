import { createRouter, createWebHistory } from 'vue-router'
import RoleSelection from '../views/RoleSelection.vue'
import UserLogin from '../views/UserLogin.vue';
import CompanyLogin from '../views/CompanyLogin.vue';
import UserRegister from '../views/UserRegister.vue';
import CompanyRegisterStep1 from '../views/CompanyRegisterStep1.vue';
import CompanyRegisterStep2 from '../views/CompanyRegisterStep2.vue';
import UserDashboard from '../views/UserDashboard.vue';

const routes = [
  {
    path: '/',
    name: 'Home',
    component: RoleSelection
  },
  { path: '/login/user', name: 'UserLogin', component: UserLogin },
  { path: '/login/company', name: 'CompanyLogin', component: CompanyLogin },
  { path: '/register/user', name: 'UserRegister', component: UserRegister },
  { path: '/register/company/step1', name: 'CompanyRegisterStep1', component: CompanyRegisterStep1 },
  { path: '/register/company/step2', name: 'CompanyRegisterStep2', component: CompanyRegisterStep2 },
  { 
    path: '/dashboard/user', 
    name: 'UserDashboard', 
    component: UserDashboard,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router