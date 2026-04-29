import { createRouter, createWebHistory } from "vue-router";

// Import your components (pages)
import VideoLayout from "../views/video/VideoLayout.vue";

import Home from "../views/home/Home.vue";
import Video from "../views/video/Video.vue";

const routes = [
  { path: "/", name: "Home", component: Home },
  {
    path: "/video/:id",
    component: VideoLayout,
    children: [{ path: "", name: "Video", component: Video }],
  },
  // catch-all 404
  //   { path: '/:pathMatch(.*)*', name: 'NotFound', component: () => import('../views/NotFound.vue') },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

export default router;
