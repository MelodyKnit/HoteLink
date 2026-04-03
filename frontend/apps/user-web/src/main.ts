import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import router from "./router";
import "../../../packages/styles/tailwind.css";
import "../../../packages/styles/theme.less";
import "./styles/index.less";

const app = createApp(App);

app.use(createPinia());
app.use(router);
app.mount("#app");
