import { createRouter, createWebHistory } from 'vue-router';

// Import your components (pages)
import Home from '../views/Home.vue';
import Video from '../views/Video.vue';

const routes = [
  { path: '/', name: 'Home', component: Home },
  { path: '/video/:id', name: 'Video', component: Video },
  // catch-all 404
//   { path: '/:pathMatch(.*)*', name: 'NotFound', component: () => import('../views/NotFound.vue') },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

export default router;