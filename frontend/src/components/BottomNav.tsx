import { Link, useLocation } from 'react-router-dom'
import { useCartStore } from '../store/cartStore'
import { useAuthStore } from '../store/authStore'

export default function BottomNav() {
  const location = useLocation()
  const { items } = useCartStore()
  const { user } = useAuthStore()
  
  const cartCount = items.reduce((sum, item) => sum + item.quantity, 0)

  const isActive = (path: string) => location.pathname === path

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 backdrop-blur-xl bg-cyber-dark/95 border-t-2 border-neon-red/30 shadow-neon-red">
      {/* Neon Top Line */}
      <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-neon-red to-transparent animate-pulse-glow" />
      
      <div className="flex justify-around items-center py-2 px-2 safe-area-inset-bottom">
        {/* Home */}
        <Link 
          to="/" 
          className={`flex flex-col items-center p-2 min-w-[60px] transition-all ${
            isActive('/') 
              ? 'text-neon-red scale-110' 
              : 'text-gray-500 hover:text-neon-cyan'
          }`}
        >
          <div className={`relative ${isActive('/') ? 'animate-float' : ''}`}>
            <div className={`text-2xl ${isActive('/') ? 'drop-shadow-[0_0_10px_rgba(255,0,51,0.8)]' : ''}`}>
              🏠
            </div>
            {isActive('/') && (
              <div className="absolute -bottom-1 left-0 right-0 h-0.5 bg-neon-red shadow-neon-red" />
            )}
          </div>
          <span className={`text-[10px] font-gaming font-bold mt-1 tracking-wide ${
            isActive('/') ? 'text-neon-red' : 'text-gray-500'
          }`}>
            HOME
          </span>
        </Link>
        
        {/* Cart */}
        <Link 
          to="/cart" 
          className={`flex flex-col items-center p-2 min-w-[60px] relative transition-all ${
            isActive('/cart') 
              ? 'text-neon-red scale-110' 
              : 'text-gray-500 hover:text-neon-cyan'
          }`}
        >
          <div className={`relative ${isActive('/cart') ? 'animate-float' : ''}`}>
            <div className={`text-2xl ${isActive('/cart') ? 'drop-shadow-[0_0_10px_rgba(255,0,51,0.8)]' : ''}`}>
              🛒
            </div>
            {cartCount > 0 && (
              <div className="absolute -top-1 -right-1 min-w-[18px] h-[18px] flex items-center justify-center bg-gradient-to-r from-neon-red to-neon-purple text-white text-[10px] font-gaming font-black rounded-full border border-white shadow-neon-red animate-pulse-glow">
                {cartCount}
              </div>
            )}
            {isActive('/cart') && (
              <div className="absolute -bottom-1 left-0 right-0 h-0.5 bg-neon-red shadow-neon-red" />
            )}
          </div>
          <span className={`text-[10px] font-gaming font-bold mt-1 tracking-wide ${
            isActive('/cart') ? 'text-neon-red' : 'text-gray-500'
          }`}>
            CART
          </span>
        </Link>
        
        {/* Orders */}
        <Link 
          to="/orders" 
          className={`flex flex-col items-center p-2 min-w-[60px] transition-all ${
            isActive('/orders') 
              ? 'text-neon-red scale-110' 
              : 'text-gray-500 hover:text-neon-cyan'
          }`}
        >
          <div className={`relative ${isActive('/orders') ? 'animate-float' : ''}`}>
            <div className={`text-2xl ${isActive('/orders') ? 'drop-shadow-[0_0_10px_rgba(255,0,51,0.8)]' : ''}`}>
              📦
            </div>
            {isActive('/orders') && (
              <div className="absolute -bottom-1 left-0 right-0 h-0.5 bg-neon-red shadow-neon-red" />
            )}
          </div>
          <span className={`text-[10px] font-gaming font-bold mt-1 tracking-wide ${
            isActive('/orders') ? 'text-neon-red' : 'text-gray-500'
          }`}>
            ORDERS
          </span>
        </Link>
        
        {/* Seller (if applicable) */}
        {user?.is_seller && (
          <Link 
            to="/seller" 
            className={`flex flex-col items-center p-2 min-w-[60px] transition-all ${
              isActive('/seller') 
                ? 'text-neon-gold scale-110' 
                : 'text-gray-500 hover:text-neon-cyan'
            }`}
          >
            <div className={`relative ${isActive('/seller') ? 'animate-float' : ''}`}>
              <div className={`text-2xl ${isActive('/seller') ? 'drop-shadow-[0_0_10px_rgba(255,215,0,0.8)]' : ''}`}>
                💼
              </div>
              {isActive('/seller') && (
                <div className="absolute -bottom-1 left-0 right-0 h-0.5 bg-neon-gold shadow-neon-gold" />
              )}
            </div>
            <span className={`text-[10px] font-gaming font-bold mt-1 tracking-wide ${
              isActive('/seller') ? 'text-neon-gold' : 'text-gray-500'
            }`}>
              SELL
            </span>
          </Link>
        )}
        
        {/* Profile */}
        <Link 
          to="/profile" 
          className={`flex flex-col items-center p-2 min-w-[60px] transition-all ${
            isActive('/profile') 
              ? 'text-neon-purple scale-110' 
              : 'text-gray-500 hover:text-neon-cyan'
          }`}
        >
          <div className={`relative ${isActive('/profile') ? 'animate-float' : ''}`}>
            <div className={`text-2xl ${isActive('/profile') ? 'drop-shadow-[0_0_10px_rgba(157,78,221,0.8)]' : ''}`}>
              👤
            </div>
            {isActive('/profile') && (
              <div className="absolute -bottom-1 left-0 right-0 h-0.5 bg-neon-purple shadow-neon-purple" />
            )}
          </div>
          <span className={`text-[10px] font-gaming font-bold mt-1 tracking-wide ${
            isActive('/profile') ? 'text-neon-purple' : 'text-gray-500'
          }`}>
            PROFILE
          </span>
        </Link>
      </div>
    </div>
  )
}
