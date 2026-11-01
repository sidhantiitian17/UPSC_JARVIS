import { resolve } from 'path'
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  // vitest bundles its own vite (v7) while the app uses vite 8, so the plugin type differs; runtime is fine.
  plugins: [react() as never],
  resolve: { alias: { '@renderer': resolve('src/renderer/src') } },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/renderer/src/test-setup.ts'],
    include: ['src/**/*.test.{ts,tsx}'],
    css: false
  }
})
