import { resolve } from 'path'
import { defineConfig, externalizeDepsPlugin } from 'electron-vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  // @jarvis/shared is TypeScript source: bundle it into main/preload instead of require()-ing it at runtime.
  main: { plugins: [externalizeDepsPlugin({ exclude: ['@jarvis/shared'] })] },
  preload: { plugins: [externalizeDepsPlugin({ exclude: ['@jarvis/shared'] })] },
  renderer: {
    resolve: {
      alias: {
        '@renderer': resolve('src/renderer/src')
      }
    },
    plugins: [react(), tailwindcss()]
  }
})
