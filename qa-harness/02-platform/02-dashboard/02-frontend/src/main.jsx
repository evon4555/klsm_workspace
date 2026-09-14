import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'

// Global styles
const globalStyle = document.createElement('style')
globalStyle.textContent = `
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }
  /* Custom scrollbar */
  ::-webkit-scrollbar { width: 6px; height: 6px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: #c1c1c1; border-radius: 3px; }
  ::-webkit-scrollbar-thumb:hover { background: #a0a0a0; }
  /* Smooth transitions for sidebar */
  .ant-layout-sider { transition: all 0.2s ease !important; }
  .ant-menu-item { border-radius: 6px !important; margin: 4px 8px !important; }
`
document.head.appendChild(globalStyle)

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
