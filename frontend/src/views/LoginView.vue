<script setup>
import { ref } from 'vue';
import { useAuthStore } from '../stores/auth';
import { useRouter } from 'vue-router';

const authStore = useAuthStore();
const router = useRouter();

const username = ref('RTL_00001');
const password = ref('Syngenta@RTL_00001');
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
  <div style="max-width: 300px; margin: 50px auto; padding: 20px; border: 1px solid #ccc;">
    <h2>Syngenta Login</h2>
    <form @submit.prevent="submitLogin">
      <div style="margin-bottom: 10px;">
        <label>User ID</label><br>
        <input v-model="username" type="text" required />
      </div>
      <div style="margin-bottom: 10px;">
        <label>Password</label><br>
        <input v-model="password" type="password" required />
      </div>
      <button type="submit">Login</button>
    </form>
    <p v-if="errorMsg" style="color: red;">{{ errorMsg }}</p>
  </div>
</template>