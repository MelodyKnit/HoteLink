import { createApp } from "vue";
import { createPinia } from "pinia";
import { configureApi } from "@hotelink/api";
import App from "./App.vue";
import router from "./router";
import "../../../packages/styles/tailwind.css";
import "../../../packages/styles/theme.less";
import "./styles/index.less";

configureApi({ loginRedirect: "/login", tokenNamespace: "user" });

const app = createApp(App);

app.use(createPinia());
app.use(router);
app.mount("#app");
