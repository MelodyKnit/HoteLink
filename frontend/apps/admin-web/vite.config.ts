import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import path from "node:path";

const usePolling = process.env.CHOKIDAR_USEPOLLING === "true";
const pollingInterval = Number(process.env.CHOKIDAR_INTERVAL ?? "300");

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
    watch: {
      usePolling,
      interval: pollingInterval,
    }
  }
});
