import { defineConfig } from "astro/config";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  site: "https://genai-gurus.com",
  output: "static",
  vite: {
    plugins: [tailwindcss()],
  },
});
