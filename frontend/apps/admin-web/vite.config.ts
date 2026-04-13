import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import path from "node:path";

const usePolling = process.env.CHOKIDAR_USEPOLLING === "true";
const pollingInterval = Number(process.env.CHOKIDAR_INTERVAL ?? "300");
const apiTarget = process.env.VITE_API_TARGET ?? "http://localhost:8000";

const backendProxy = {
  target: apiTarget,
  changeOrigin: true,
};

export default defineConfig({
  base: "/admin/",
  plugins: [vue()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src")
    }
  },
  server: {
    host: "0.0.0.0",
    port: 5174,
    allowedHosts: ["classbot.top"],
    proxy: {
      "/api": backendProxy,
      "/media": backendProxy,
      "/static": backendProxy,
      "/docs": backendProxy,
      "/redoc": backendProxy,
      "/schema": backendProxy,
    },
    watch: {
      usePolling,
      interval: pollingInterval,
    }
  }
});
