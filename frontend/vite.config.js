import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'node:fs'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    https: {
      key: fs.readFileSync(new URL('../certs/dev-key.pem', import.meta.url)),
      cert: fs.readFileSync(new URL('../certs/dev-cert.pem', import.meta.url)),
    },
  },
})
