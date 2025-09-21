import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'
import { fileURLToPath } from 'url'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
    },
  },
  resolve: {
    alias: {
      '@': resolve(fileURLToPath(import.meta.url), '../src'),
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
})