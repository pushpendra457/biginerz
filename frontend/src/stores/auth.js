import { defineStore } from 'pinia';
import axios from 'axios';
import { jwtDecode } from 'jwt-decode';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || null,
    role: localStorage.getItem('role') || null,
    userId: localStorage.getItem('userId') || null,
  }),
  
  getters: {
    isAuthenticated: (state) => !!state.token,
    isRep: (state) => state.role === 'rep',
    isRetailer: (state) => state.role === 'retailer',
  },
  
  actions: {
    async login(username, password) {
      try {
        // Call your FastAPI backend
        const response = await axios.post('http://127.0.0.1:8000/api/v1/auth/login', {
          username,
          password
        });
        
        const { access_token, role, user_id } = response.data;
        
        // Save to Pinia state
        this.token = access_token;
        this.role = role;
        this.userId = user_id;
        
        // Save to browser LocalStorage so they stay logged in on refresh
        localStorage.setItem('token', access_token);
        localStorage.setItem('role', role);
        localStorage.setItem('userId', user_id);
        
        // Set Axios default header for future requests
        axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
        
        return { success: true, role };
      } catch (error) {
        console.error("Login failed:", error);
        return { success: false, error: error.response?.data?.detail || "Login failed" };
      }
    },
    
    logout() {
      this.token = null;
      this.role = null;
      this.userId = null;
      localStorage.clear();
      delete axios.defaults.headers.common['Authorization'];
    }
  }
});