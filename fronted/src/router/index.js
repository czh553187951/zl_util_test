import { createRouter, createWebHistory } from 'vue-router';
import DataManagement from '../components/DataManagement.vue';

const routes = [
    { path: '/datamanagement', component: DataManagement },

  // 其他路由配置...
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;


