import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './cryptoforge/styles/theme.css'
import CryptoForgeApp from './cryptoforge/CryptoForgeApp.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <CryptoForgeApp />
  </StrictMode>,
)