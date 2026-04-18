import { Link, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useCartStore } from '../store/cartStore'
import { useAuthStore } from '../store/authStore'

export default function BottomNav() {
  const { t } = useTranslation()
  const location = useLocation()
  const { items } = useCartStore()
  const { user } = useAuthStore()
  
  const cartCount = items.reduce((sum, item) => sum + item.quantity, 0)

  const isActive = (path: string) => location.pathname === path

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-tg-bg border-t border-gray-200 flex justify-around py-2 safe-area-inset-bottom">
      <Link 
        to="/" 
        className={`flex flex-col items-center p-2 ${isActive('/') ? 'text-tg-button' : 'text-gray-600'}`}
      >
        <span className="text-2xl">{isActive('/') ? '🏠' : '🏘️'}</span>
        <span className="text-xs">{t('nav.home')}</span>
      </Link>
      
      <Link 
        to="/cart" 
        className={`flex flex-col items-center p-2 relative ${isActive('/cart') ? 'text-tg-button' : 'text-gray-600'}`}
      >
        <span className="text-2xl">🛒</span>
        {cartCount > 0 && (
          <span className="absolute top-0 right-0 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
            {cartCount}
          </span>
        )}
        <span className="text-xs">{t('nav.cart')}</span>
      </Link>
      
      <Link 
        to="/orders" 
        className={`flex flex-col items-center p-2 ${isActive('/orders') ? 'text-tg-button' : 'text-gray-600'}`}
      >
        <span className="text-2xl">📦</span>
        <span className="text-xs">{t('nav.orders')}</span>
      </Link>
      
      {user?.is_seller && (
        <Link 
          to="/seller" 
          className={`flex flex-col items-center p-2 ${isActive('/seller') ? 'text-tg-button' : 'text-gray-600'}`}
        >
          <span className="text-2xl">💼</span>
          <span className="text-xs">{t('nav.seller')}</span>
        </Link>
      )}
      
      <Link 
        to="/profile" 
        className={`flex flex-col items-center p-2 ${isActive('/profile') ? 'text-tg-button' : 'text-gray-600'}`}
      >
        <span className="text-2xl">👤</span>
        <span className="text-xs">{t('nav.profile')}</span>
      </Link>
    </div>
  )
}
