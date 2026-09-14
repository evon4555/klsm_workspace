import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const backendUrl = process.env.QA_DASHBOARD_BACKEND_URL || 'http://localhost:8002'

export default defineConfig({
  plugins: [react()],
  resolve: {
    // Keep dependency resolution stable from the numbered workspace path.
    preserveSymlinks: true,
  },
  server: {
    port: 5174,
    // Proxy API and WebSocket requests to the FastAPI backend.
    proxy: {
      '/api': backendUrl,
      '/ws': {
        target: backendUrl,
        ws: true,
      },
    },
  },
  build: {
    // Ant Design is intentionally isolated into a cached vendor chunk; the
    // application/page chunks stay small and load on demand.
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return undefined
          if (id.includes('/react/') || id.includes('/react-dom/') || id.includes('/scheduler/')) {
            return 'react-vendor'
          }
          if (
            id.includes('/antd/')
            || id.includes('/@ant-design/')
            || id.includes('/@rc-component/')
            || id.includes('/rc-')
          ) {
            return 'antd-vendor'
          }
          if (id.includes('/recharts/') || id.includes('/d3-')) return 'charts-vendor'
          return 'vendor'
        },
      },
    },
  },
})
