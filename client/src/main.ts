import { createApp } from 'vue';
import { createPinia } from 'pinia';
import './main.css';
import App from './App.vue';
import router from './router';
import { clickOutside } from './directives/uiDirectives';

const app = createApp(App);
const pinia = createPinia();

app.directive('click-outside', clickOutside);
app.use(router);
app.use(pinia);
app.mount('#app');
