import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '../stores/auth';

import LoginView from '../views/LoginView.vue';
import RepHomeView from '../views/RepHomeView.vue';
import RetailerHomeView from '../views/RetailerHomeView.vue';

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', component: LoginView },
  { 
    path: '/rep', 
    component: RepHomeView,
    meta: { requiresAuth: true, role: 'rep' }
  },
  { 
    path: '/retailer', 
    component: RetailerHomeView,
    meta: { requiresAuth: true, role: 'retailer' }
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// Navigation Guard: Protect routes
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore();
  
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login');
  } else if (to.meta.requiresAuth && to.meta.role !== authStore.role) {
    // Prevent Reps from seeing Retailer pages, and vice versa
    next(`/${authStore.role}`); 
  } else {
    next();
  }
});

export default router;