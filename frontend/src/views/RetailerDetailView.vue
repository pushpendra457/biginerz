<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { useRoute, useRouter } from 'vue-router';

const route = useRoute();
const router = useRouter();

const retailerId = route.params.id; // Get ID from the URL /rep/retailer/1
const priorityData = ref(null);
const loading = ref(false);
const error = ref(null);

const fetchPriorityData = async () => {
  loading.value = true;
  try {
    const response = await axios.get(`http://127.0.0.1:8000/api/v1/rep-tools/priority/${retailerId}`);
    priorityData.value = response.data.data;
  } catch (err) {
    error.value = err.response?.data?.detail || "Failed to load retailer data.";
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  fetchPriorityData();
});

const goBack = () => router.push('/rep');

const getBadgeClass = (label) => {
  switch (label) {
    case 'CRITICAL': return 'badge-critical';
    case 'HIGH': return 'badge-high';
    case 'MEDIUM': return 'badge-medium';
    default: return 'badge-low';
  }
};
</script>

<template>
  <div class="dashboard-container">
    <button @click="goBack" class="back-btn">← Back to Territory List</button>

    <header class="dashboard-header">
      <div>
        <h1>Retailer Analysis: #{{ retailerId }}</h1>
        <p>Live ML insights and operational context.</p>
      </div>
    </header>

    <div v-if="error" class="alert alert-error"><strong>Error:</strong> {{ error }}</div>
    <div v-if="loading" class="loading-state"><div class="spinner"></div><p>Running ML Pipeline...</p></div>

    <main v-if="priorityData && !loading" class="dashboard-grid">
      
      <section class="card score-card">
        <h2>{{ priorityData.district }} / {{ priorityData.tehsil }}</h2>
        <div class="score-display">
          <div class="main-score">
            <span class="score-value">{{ priorityData.final_priority_score }}</span>
            <span class="score-max">/100</span>
          </div>
          <span :class="['badge', getBadgeClass(priorityData.priority_label)]">
            {{ priorityData.priority_label }} PRIORITY
          </span>
        </div>
      </section>

      <section class="card action-card">
        <h2>⚡ Next Best Action</h2>
        <p class="action-text">{{ priorityData.next_best_action }}</p>
      </section>

      <section class="card breakdown-card">
        <h2>Live Context Boosts</h2>
        <ul class="boost-list">
          <li><span>⛅ Weather Boost</span><span class="boost-value">+{{ priorityData.weather_boost }}</span></li>
          <li><span>🐛 Pest Risk Boost</span><span class="boost-value">+{{ priorityData.pest_boost }}</span></li>
          <li><span>🛰️ NDVI Stress Boost</span><span class="boost-value">+{{ priorityData.ndvi_boost }}</span></li>
          <li><span>📈 Sales Trend Boost</span><span class="boost-value">+{{ priorityData.sales_boost }}</span></li>
          <li><span>📦 Inventory Boost</span><span class="boost-value">+{{ priorityData.inventory_boost }}</span></li>
        </ul>
      </section>

      <section class="card reasons-card">
        <h2>Intelligence Briefing</h2>
        <ul class="reasons-list">
          <li v-for="(reason, index) in priorityData.reasons" :key="index">{{ reason }}</li>
        </ul>
      </section>
    </main>
  </div>
</template>

<style scoped>
/* Keeping the exact same CSS classes from the previous design */
.dashboard-container { max-width: 1200px; margin: 0 auto; padding: 2rem; font-family: system-ui, sans-serif; }
.back-btn { background: none; border: none; color: #3b82f6; font-weight: 600; cursor: pointer; margin-bottom: 1.5rem; padding: 0; font-size: 1rem;}
.back-btn:hover { text-decoration: underline; }
.dashboard-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; padding-bottom: 1rem; border-bottom: 2px solid #eef2f6; }
.dashboard-header h1 { margin: 0 0 0.5rem 0; font-size: 1.8rem; color: #111; }
.dashboard-header p { margin: 0; color: #666; }
.dashboard-grid { display: grid; grid-template-columns: 1fr 1.5fr; gap: 1.5rem; }
.card { background: white; border-radius: 12px; padding: 1.5rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); border: 1px solid #f1f5f9; }
.card h2 { margin-top: 0; font-size: 1.2rem; color: #475569; margin-bottom: 1rem; }
.score-display { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem; }
.main-score { display: flex; align-items: baseline; }
.score-value { font-size: 3.5rem; font-weight: 800; color: #0f172a; line-height: 1; }
.score-max { font-size: 1.5rem; color: #94a3b8; margin-left: 4px; }
.badge { padding: 0.5rem 1rem; border-radius: 9999px; font-weight: 700; font-size: 0.875rem; letter-spacing: 0.05em; }
.badge-critical { background: #fee2e2; color: #991b1b; }
.badge-high { background: #ffedd5; color: #c2410c; }
.badge-medium { background: #dbeafe; color: #1e40af; }
.badge-low { background: #dcfce3; color: #166534; }
.action-card { background: #f0fdf4; border: 1px solid #bbf7d0; }
.action-card h2 { color: #166534; }
.action-text { font-size: 1.25rem; font-weight: 500; color: #15803d; line-height: 1.5; margin: 0; }
.boost-list { list-style: none; padding: 0; margin: 0; }
.boost-list li { display: flex; justify-content: space-between; padding: 0.75rem 0; border-bottom: 1px solid #f1f5f9; font-weight: 500; }
.boost-value { font-weight: 700; color: #0ea5e9; }
.reasons-list { padding-left: 1.2rem; color: #334155; line-height: 1.6; }
.reasons-list li { margin-bottom: 0.5rem; }
.alert-error { background: #fef2f2; color: #b91c1c; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; }
.loading-state { text-align: center; padding: 3rem; color: #64748b; }
.spinner { border: 4px solid #f3f3f3; border-top: 4px solid #3b82f6; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 0 auto 1rem; }
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
@media (max-width: 768px) { .dashboard-grid { grid-template-columns: 1fr; } }
</style>