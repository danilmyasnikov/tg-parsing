import { defineConfig } from 'vite'
import path from 'path'

export default defineConfig({
  base: '/static/',
  root: 'src',
  build: {
    outDir: path.resolve(__dirname, '..', 'backend', 'static'),
    emptyOutDir: false,
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
