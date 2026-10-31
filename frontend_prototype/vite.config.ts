import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/health': 'http://localhost:8002',
      '/system': 'http://localhost:8002',
      '/architecture': 'http://localhost:8002',
      '/questions': 'http://localhost:8002',
      '/score': 'http://localhost:8002',
      '/interview': 'http://localhost:8002',
      '/asr': 'http://localhost:8002',
      '/fairness': 'http://localhost:8002',
      '/metrics': 'http://localhost:8002',
      '/test': 'http://localhost:8002',
      '/ws': {
        target: 'ws://localhost:8002',
        ws: true,
      },
    },
  },
});
