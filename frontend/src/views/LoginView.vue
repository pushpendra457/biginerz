<script setup>
import { ref } from 'vue';
import { useAuthStore } from '../stores/auth';
import { useRouter } from 'vue-router';

const authStore = useAuthStore();
const router = useRouter();

const username = ref('REP_0001');
const password = ref('Syngenta@');
const errorMsg = ref('');

const submitLogin = async () => {
  const result = await authStore.login(username.value, password.value);
  if (result.success) {
    router.push(`/${result.role}`); // Dynamically route to /rep or /retailer
  } else {
    errorMsg.value = result.error;
  }
};
</script>

<template>
  <div class="login-wrapper">
    <div class="card login-card">
      <h2 class="login-title">Syngenta Login</h2>
      <form @submit.prevent="submitLogin">
        
        <div class="form-group">
          <label class="form-label">User ID</label>
          <input v-model="username" type="text" class="form-input" required />
        </div>
        
        <div class="form-group">
          <label class="form-label">Password</label>
          <input v-model="password" type="password" class="form-input" required />
        </div>
        
        <button type="submit" class="submit-btn">Login</button>
      </form>
      
      <div v-if="errorMsg" class="alert-error">
        {{ errorMsg }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-wrapper {
  max-width: 400px;
  margin: 4rem auto;
  font-family: system-ui, sans-serif;
}

.card {
  background: white;
  border-radius: 12px;
  padding: 2.5rem 2rem;
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
  border: 1px solid #f1f5f9;
}

.login-title {
  margin-top: 0;
  font-size: 1.6rem;
  color: #111;
  text-align: center;
  margin-bottom: 2rem;
}

.form-group {
  margin-bottom: 1.25rem;
}

.form-label {
  display: block;
  margin-bottom: 0.5rem;
  color: #475569;
  font-weight: 500;
  font-size: 0.9rem;
}

.form-input {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 1rem;
  color: #334155;
  box-sizing: border-box;
  transition: all 0.2s;
}

.form-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.submit-btn {
  width: 100%;
  background: #3b82f6;
  color: white;
  border: none;
  padding: 0.8rem;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  margin-top: 0.5rem;
  transition: background 0.2s;
}

.submit-btn:hover {
  background: #2563eb;
}

.alert-error {
  background: #fef2f2;
  color: #b91c1c;
  padding: 1rem;
  border-radius: 8px;
  margin-top: 1.5rem;
  text-align: center;
  font-size: 0.9rem;
  font-weight: 500;
}
</style>