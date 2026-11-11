import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// The dev proxy lets the browser call /api/... on the same origin as the page,
// so no CORS setup is needed during development.
export default defineConfig({
  plugins: [react()],
  server: { proxy: { '/api': 'http://localhost:8000' } },
  test: {
    environment: 'jsdom',
    setupFiles: './src/setupTests.js',
    globals: true,
  },
})
