import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => ({
  base: loadEnv(mode, "..", "VITE_").VITE_BASE_PATH || "/",
  plugins: [react()],
  server: {
    proxy: {
      "/api": process.env.VITE_DEV_API_TARGET || "http://localhost:8000",
    },
  },
}));
