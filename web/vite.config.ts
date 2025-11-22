import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: { port: 5173, proxy: { '/datasets': 'http://127.0.0.1:5000',
                                 '/series': 'http://127.0.0.1:5000',
                                 '/smooth': 'http://127.0.0.1:5000',
                                 '/match_pae': 'http://127.0.0.1:5000',
                                 '/spectral': 'http://127.0.0.1:5000',
                                 '/precomputed': 'http://127.0.0.1:5000' } }
})
