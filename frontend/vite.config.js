import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      '/documents': 'http://localhost:8000',
      '/investigate': 'http://localhost:8000',
      '/investigations': 'http://localhost:8000',
      '/dashboard': 'http://localhost:8000',
      '/evaluation': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
})

