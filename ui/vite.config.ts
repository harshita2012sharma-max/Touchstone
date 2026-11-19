import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// The build goes straight into the Python package, which serves it from `kasauti ui`.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  build: {
    outDir: "../src/kasauti/server/static",
    emptyOutDir: true,
  },
  server: {
    host: "127.0.0.1",
    proxy: { "/api": "http://127.0.0.1:7860" },
  },
});
