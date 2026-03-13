import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

// NOTE: App.tsx already wraps itself in <QueryClientProvider> and
// <BrowserRouter>. Do not add them again here — a second BrowserRouter
// around this one creates two competing history instances, which shows up
// as broken back-button behavior and routes occasionally not updating.

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)