import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

// En dev (npm run dev) el navegador corre en el host y Vite en el contenedor
// "frontend-dev", por eso /api se manda al contenedor "gateway" dentro de la
// red interna de Docker en vez de a localhost.
export default defineConfig({
  plugins: [vue()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      "/api": {
        target: "http://gateway:80",
        changeOrigin: true,
      },
    },
  },
});
