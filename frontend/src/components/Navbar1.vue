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
  <nav v-if="authStore.isAuthenticated" class="dashboard-nav">
    <router-link v-if="authStore.isRep" to="/rep" class="nav-link">Rep Dashboard</router-link>
    <router-link v-if="authStore.isRetailer" to="/retailer" class="nav-link">Retailer Dashboard</router-link>
    
    <div class="nav-right">
      <span class="user-info">Logged in as: <strong>{{ authStore.userId }}</strong></span>
      <button @click="handleLogout" class="logout-btn">Logout</button>
    </div>
  </nav>
</template>

<style scoped>
.dashboard-nav {
  padding: 1rem 2rem;
  background: white;
  display: flex;
  align-items: center;
  gap: 1.5rem;
  border-bottom: 2px solid #eef2f6;
  font-family: system-ui, sans-serif;
}

.nav-link {
  text-decoration: none;
  color: #475569;
  font-weight: 600;
  font-size: 1rem;
  transition: color 0.2s;
}

.nav-link:hover, 
.nav-link.router-link-active {
  color: #3b82f6;
}

.nav-right {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.user-info {
  color: #64748b;
  font-size: 0.95rem;
}

.user-info strong {
  color: #0f172a;
}

.logout-btn {
  background: white;
  border: 1px solid #e2e8f0;
  color: #475569;
  font-weight: 600;
  cursor: pointer;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.logout-btn:hover {
  background: #f8fafc;
  border-color: #cbd5e1;
  color: #0f172a;
}
</style>