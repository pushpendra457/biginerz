import Dexie from 'dexie';

export const db = new Dexie('AntiFarmDB');

// Define your offline tables here. 
// ++id means auto-incrementing primary key
db.version(1).stores({
  visits: '++id, grower_id, visit_date, status',
  growers: 'grower_id, name, village'
});