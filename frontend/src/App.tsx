import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { useEffect } from 'react'
import WebApp from '@twa-dev/sdk'

// Pages
import HomePage from './pages/HomePage'
import ProductPage from './pages/ProductPage'
import CartPage from './pages/CartPage'
import CheckoutPage from './pages/CheckoutPage'
import OrdersPage from './pages/OrdersPage'
import ChatPage from './pages/ChatPage'
import SellerDashboard from './pages/SellerDashboard'
import ProfilePage from './pages/ProfilePage'
import AdminPanel from './pages/AdminPanel'

// Components
import Toast from './components/Toast'

// Store
import { useAuthStore } from './store/authStore'
import { useNotificationStore } from './store/notificationStore'
import { useUIStore } from './store/uiStore'

function App() {
  const { initAuth, token } = useAuthStore()
  const { connectWebSocket, disconnectWebSocket } = useNotificationStore()
  const { theme } = useUIStore()

  useEffect(() => {
    // Initialize Telegram WebApp
    WebApp.ready()
    WebApp.expand()
    
    // Set header color based on theme
    WebApp.setHeaderColor(theme === 'dark' ? '#1a1a1a' : 'bg_color')
    
    // Initialize auth
    initAuth()
  }, [initAuth])

  useEffect(() => {
    // Connect to notification WebSocket when authenticated
    if (token) {
      connectWebSocket(token)
    }

    return () => {
      disconnectWebSocket()
    }
  }, [token, connectWebSocket, disconnectWebSocket])

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-tg-bg text-tg-text">
        <Toast />
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/product/:id" element={<ProductPage />} />
          <Route path="/cart" element={<CartPage />} />
          <Route path="/checkout" element={<CheckoutPage />} />
          <Route path="/orders" element={<OrdersPage />} />
          <Route path="/chat/:dealId" element={<ChatPage />} />
          <Route path="/seller" element={<SellerDashboard />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/admin" element={<AdminPanel />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}

export default App
