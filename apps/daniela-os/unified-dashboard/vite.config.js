import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

export default defineConfig({
  plugins: [svelte()],
  server: {
    // El Flask del dashboard vive en 9997: el dev server NO puede usar ese
    // puerto (proxy circular). 5173 por defecto, proxy a los servicios reales.
    port: 5173,
    proxy: {
      // Regla especifica ANTES de la generica: /api/iot vive en Daniela :9200
      '/api/iot': {
        target: 'http://localhost:9200',
        changeOrigin: true,
      },
      '/api': {
        target: 'http://localhost:9997',
        changeOrigin: true,
      },
    },
  },
})
