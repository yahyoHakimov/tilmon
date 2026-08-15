/// <reference types="vitest" />
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Portlar dev.sh dan uzatiladi — ikkala tomonda qo'lda o'zgartirish
// kerak bo'lmasligi uchun.
const BACKEND_URL = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";
const FRONTEND_PORT = Number(process.env.FRONTEND_PORT ?? 5173);

export default defineConfig({
  plugins: [react()],
  server: {
    port: FRONTEND_PORT,
    strictPort: true,
    proxy: {
      // Backend alohida ishlaydi — API chegarasi aniq saqlanadi.
      "/api": BACKEND_URL,
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/setupTests.ts"],
  },
});
