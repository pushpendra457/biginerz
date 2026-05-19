<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

const router = useRouter();

const searchQuery = ref('');
const sortBy = ref('score_desc');
const loading = ref(false);

const retailers = ref([]);

const fetchRetailerList = async () => {
  loading.value = true;
  try {
    // Calling our brand new batch API!
    const response = await axios.get('http://127.0.0.1:8000/api/v1/rep-tools/my-retailers');
    retailers.value = response.data.data; 
    
    loading.value = false;
  } catch (err) {
    console.error("Failed to load list", err);
    loading.value = false;
  }
};

onMounted(() => fetchRetailerList());

// Computed property to handle searching and sorting instantly on the frontend
const processedRetailers = computed(() => {
  // 1. Filter by search
  let result = retailers.value.filter(r => 
    r.name.toLowerCase().includes(searchQuery.value.toLowerCase()) || 
    r.id.toString() === searchQuery.value
  );

  // 2. Sort
  result.sort((a, b) => {
    if (sortBy.value === 'score_desc') return b.score - a.score;
    if (sortBy.value === 'score_asc') return a.score - b.score;
    if (sortBy.value === 'name_asc') return a.name.localeCompare(b.name);
    return 0;
  });

  return result;
});

const goToDetail = (id) => {
  router.push(`/rep/retailer/${id}`);
};

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
  <div class="list-container">
    <header class="header">
      <h1>Territory Overview</h1>
      <p>Select a retailer to view AI recommendations.</p>
    </header>

    <div class="toolbar">
      <input 
        v-model="searchQuery" 
        type="text" 
        placeholder="Search by ID or Name..." 
        class="search-input"
      />
      <select v-model="sortBy" class="sort-select">
        <option value="score_desc">Highest Priority First</option>
        <option value="score_asc">Lowest Priority First</option>
        <option value="name_asc">Name (A-Z)</option>
      </select>
    </div>

    <div v-if="loading" class="loading">Loading your territory...</div>
    
    <div v-else class="retailer-grid">
      <div 
        v-for="retailer in processedRetailers" 
        :key="retailer.id" 
        class="retailer-card"
        @click="goToDetail(retailer.id)"
      >
        <div class="card-top">
          <div>
            <h3>{{ retailer.name }} <span class="id-tag">#{{ retailer.id }}</span></h3>
            <span class="location">{{ retailer.tehsil }}</span>
          </div>
          <div class="score-box">
            <span class="score">{{ retailer.score }}</span>
            <span :class="['badge', getBadgeClass(retailer.label)]">{{ retailer.label }}</span>
          </div>
        </div>
        <div class="card-bottom">
          <strong>⚡ Action:</strong> {{ retailer.action }}
        </div>
      </div>
      
      <div v-if="processedRetailers.length === 0" class="empty-state">
        No retailers found matching your search.
      </div>
    </div>
  </div>
</template>

<style scoped>
.list-container { max-width: 1000px; margin: 0 auto; padding: 2rem; font-family: system-ui, sans-serif;}
.header h1 { margin: 0; color: #0f172a; }
.header p { color: #64748b; margin-top: 0.5rem; }

.toolbar { display: flex; gap: 1rem; margin: 2rem 0; }
.search-input { flex: 1; padding: 0.75rem; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 1rem; }
.sort-select { padding: 0.75rem; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 1rem; background: white; }

.retailer-grid { display: flex; flex-direction: column; gap: 1rem; }
.retailer-card {
  background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1.5rem;
  cursor: pointer; transition: transform 0.1s, box-shadow 0.1s;
}
.retailer-card:hover { transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); border-color: #93c5fd; }

.card-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem; }
.card-top h3 { margin: 0 0 0.25rem 0; color: #1e293b; display: flex; align-items: center; gap: 0.5rem;}
.id-tag { font-size: 0.8rem; color: #94a3b8; background: #f1f5f9; padding: 2px 6px; border-radius: 4px;}
.location { color: #64748b; font-size: 0.9rem; }

.score-box { text-align: right; display: flex; flex-direction: column; align-items: flex-end; gap: 0.5rem;}
.score { font-size: 1.5rem; font-weight: 800; color: #0f172a; }

.card-bottom { background: #f8fafc; padding: 0.75rem; border-radius: 6px; font-size: 0.9rem; color: #334155; }

/* Badges */
.badge { padding: 4px 10px; border-radius: 99px; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.5px; }
.badge-critical { background: #fee2e2; color: #991b1b; }
.badge-high { background: #ffedd5; color: #c2410c; }
.badge-medium { background: #dbeafe; color: #1e40af; }
.badge-low { background: #dcfce3; color: #166534; }
.empty-state { text-align: center; color: #64748b; padding: 2rem; }
</style>