<script setup>
import { useAuthStore } from '../stores/auth';
import { useRouter } from 'vue-router';

const authStore = useAuthStore();
const router = useRouter();

const handleLogout = () => {
  authStore.logout();
  router.push('/login');
};
</script>

<template>
  <nav v-if="authStore.isAuthenticated" style="padding: 1rem; background: #eee; display: flex; gap: 1rem;">
    <router-link v-if="authStore.isRep" to="/rep">Rep Dashboard</router-link>
    <router-link v-if="authStore.isRetailer" to="/retailer">Retailer Dashboard</router-link>
    
    <span style="margin-left: auto;">Logged in as: {{ authStore.userId }}</span>
    <button @click="handleLogout">Logout</button>
  </nav>
</template>