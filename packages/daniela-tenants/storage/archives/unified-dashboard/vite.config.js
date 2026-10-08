import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

export default defineConfig({
  plugins: [svelte()],
  server: {
    port: 9997,
    proxy: {
      '/api': {
        target: 'http://localhost:9997',
        changeOrigin: true
      }
    }
  }
})