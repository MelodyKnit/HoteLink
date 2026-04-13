import { createApp } from "vue";
import { createPinia } from "pinia";
import { configureApi } from "@hotelink/api";
import App from "./App.vue";
import router from "./router";
import { useAuthStore } from "@hotelink/store";
import "../../../packages/styles/tailwind.css";
import "../../../packages/styles/theme.less";
import "./styles/index.less";

configureApi({ loginRedirect: "/admin/login", tokenNamespace: "admin" });

const app = createApp(App);
const pinia = createPinia();

app.use(pinia);
app.use(router);

const auth = useAuthStore();
if (auth.isLoggedIn) {
  auth.fetchMe().finally(() => app.mount("#app"));
} else {
  app.mount("#app");
}
