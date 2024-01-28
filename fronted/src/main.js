// main.js

import { createApp } from 'vue';
import { createRouter, createWebHistory } from 'vue-router';
import App from './components/DataManagement.vue';  // 将根组件设置为 DataManagement.vue
import DataManagement from './components/DataManagement.vue';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/datamanagement', component: DataManagement },
  ]
});

const app = createApp(App);
app.use(router);
app.mount('#app');