import { createRouter, createWebHistory } from 'vue-router'
import RoleSelection from '../views/RoleSelection.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: RoleSelection
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router