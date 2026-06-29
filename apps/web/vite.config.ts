import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const apiTarget = process.env.VITE_API_TARGET ?? "http://127.0.0.1:8000";
const devPort = Number(process.env.VITE_DEV_PORT ?? 5173);
const webBase = process.env.VITE_BASE_PATH?.trim() || "/";

export default defineConfig({
  base: webBase,
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    port: devPort,
    proxy: {
      "/api": apiTarget
    }
  }
});
