import { useEffect, useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useCartStore } from '../store/cartStore'
import { useUIStore } from '../store/uiStore'
import BottomNav from '../components/BottomNav'
import LoadingSpinner from '../components/LoadingSpinner'
import api from '../api/client'

export default function CartPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { items, total, fetchCart, removeItem, updateQuantity, isLoading } = useCartStore()
  const { showToast } = useUIStore()
  const [promoCode, setPromoCode] = useState('')
  const [discount, setDiscount] = useState(0)
  const [applyingPromo, setApplyingPromo] = useState(false)

  useEffect(() => {
    fetchCart()
  }, [fetchCart])

  const handleRemoveItem = async (itemId: number) => {
    try {
      await removeItem(itemId)
      showToast(t('cart.itemRemoved'), 'success')
    } catch (error) {
      showToast(t('errors.generic'), 'error')
    }
  }

  const handleUpdateQuantity = async (itemId: number, newQuantity: number) => {
    if (newQuantity < 1) return
    try {
      await updateQuantity(itemId, newQuantity)
    } catch (error: any) {
      if (error.response?.data?.error_code === 'insufficient_stock') {
        showToast(t('errors.insufficientStock'), 'error')
      } else {
        showToast(t('errors.generic'), 'error')
      }
    }
  }

  const handleApplyPromo = async () => {
    if (!promoCode.trim()) return
    
    try {
      setApplyingPromo(true)
      const response = await api.post('/cart/apply-promo', { promo_code: promoCode })
      setDiscount(response.data.discount_amount)
      showToast(t('cart.promoApplied'), 'success')
    } catch (error: any) {
      if (error.response?.data?.error_code === 'promo_not_found') {
        showToast(t('errors.promoNotFound'), 'error')
      } else if (error.response?.data?.error_code === 'promo_expired') {
        showToast(t('errors.promoExpired'), 'error')
      } else {
        showToast(t('errors.generic'), 'error')
      }
    } finally {
      setApplyingPromo(false)
    }
  }

  const finalTotal = total - discount

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <div className="min-h-screen pb-32 bg-cyber-dark relative overflow-hidden">
      {/* Animated Background Grid */}
      <div className="fixed inset-0 opacity-10 pointer-events-none">
        <div className="absolute inset-0" style={{
          backgroundImage: `
            linear-gradient(rgba(255, 0, 51, 0.1) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255, 0, 51, 0.1) 1px, transparent 1px)
          `,
          backgroundSize: '50px 50px'
        }} />
      </div>

      {/* Header */}
      <div className="sticky top-0 backdrop-blur-xl bg-cyber-dark/90 border-b border-neon-red/30 shadow-neon-red p-4 z-10 transition-all duration-300">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate(-1)} className="text-neon-cyan text-2xl hover:text-neon-red transition-all duration-200 hover:scale-110">
            ←
          </button>
          <h1 className="text-2xl font-black font-gaming text-neon-red drop-shadow-[0_0_10px_rgba(255,0,51,0.8)]">🛒 {t('nav.cart')}</h1>
        </div>
      </div>

      {items.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 relative z-10">
          <div className="text-8xl mb-4 animate-float">🛒</div>
          <p className="text-gray-400 mb-6 font-gaming text-lg">{t('cart.empty')}</p>
          <Link
            to="/"
            className="bg-gradient-to-r from-neon-red to-neon-purple text-white px-8 py-4 rounded-xl font-gaming font-black tracking-wide shadow-neon-red hover:shadow-neon-purple hover:scale-105 transition-all duration-300"
          >
            {t('cart.continueShopping')}
          </Link>
        </div>
      ) : (
        <>
          <div className="p-4 relative z-10">
            {/* Cart Items */}
            <div className="space-y-4 mb-6">
              {items.map((item) => (
                <div key={item.id} className="relative overflow-hidden rounded-xl bg-black/40 backdrop-blur-sm border-2 border-neon-red/30 hover:border-neon-red hover:shadow-neon-red-lg transition-all duration-300 hover:scale-[1.02] p-4">
                  <div className="flex gap-3">
                    {/* Image */}
                    <Link to={`/product/${item.lot_id}`} className="flex-shrink-0 group">
                      <div className="w-24 h-24 bg-gradient-to-br from-neon-red/20 to-neon-purple/20 rounded-lg flex items-center justify-center overflow-hidden border-2 border-neon-cyan/30 transition-all duration-300 group-hover:border-neon-cyan group-hover:scale-105">
                        {item.lot_image ? (
                          <img 
                            src={item.lot_image} 
                            alt={item.lot_title} 
                            className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                          />
                        ) : (
                          <span className="text-4xl">🎮</span>
                        )}
                      </div>
                    </Link>

                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <Link to={`/product/${item.lot_id}`}>
                        <h3 className="font-gaming font-bold text-white mb-1 line-clamp-2 hover:text-neon-cyan transition-colors duration-200">{item.lot_title}</h3>
                      </Link>
                      <div className="text-xl font-black font-gaming text-neon-red drop-shadow-[0_0_10px_rgba(255,0,51,0.8)] mb-3">
                        {item.lot_price} ₽
                      </div>

                      {/* Quantity Controls */}
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleUpdateQuantity(item.id, item.quantity - 1)}
                          disabled={item.quantity <= 1}
                          className="w-10 h-10 bg-black/60 border-2 border-neon-purple/50 rounded-lg font-gaming font-black text-white hover:border-neon-purple hover:shadow-neon-purple disabled:opacity-30 transition-all duration-200 hover:scale-110"
                        >
                          -
                        </button>
                        <span className="w-12 text-center font-gaming font-bold text-neon-cyan text-lg">{item.quantity}</span>
                        <button
                          onClick={() => handleUpdateQuantity(item.id, item.quantity + 1)}
                          className="w-10 h-10 bg-black/60 border-2 border-neon-purple/50 rounded-lg font-gaming font-black text-white hover:border-neon-purple hover:shadow-neon-purple transition-all duration-200 hover:scale-110"
                        >
                          +
                        </button>
                      </div>
                    </div>

                    {/* Remove Button */}
                    <button
                      onClick={() => handleRemoveItem(item.id)}
                      className="text-neon-red text-2xl self-start hover:text-white hover:scale-125 transition-all duration-200"
                    >
                      ✕
                    </button>
                  </div>

                  {/* Item Total */}
                  <div className="mt-3 pt-3 border-t border-neon-red/30 flex justify-between items-center">
                    <span className="text-sm text-neon-cyan font-gaming">{t('cart.itemTotal')}</span>
                    <span className="font-gaming font-black text-neon-gold text-lg">{(item.lot_price * item.quantity).toFixed(2)} ₽</span>
                  </div>
                </div>
              ))}
            </div>

            {/* Promo Code */}
            <div className="relative overflow-hidden rounded-xl bg-black/40 backdrop-blur-sm border-2 border-neon-purple/30 p-4 mb-6 hover:border-neon-purple hover:shadow-neon-purple transition-all duration-300">
              <h3 className="font-gaming font-bold text-neon-cyan mb-3 tracking-wide">🎁 {t('cart.promoCode')}</h3>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={promoCode}
                  onChange={(e) => setPromoCode(e.target.value.toUpperCase())}
                  placeholder={t('cart.enterPromoCode')}
                  className="flex-1 px-4 py-3 bg-black/60 border-2 border-neon-purple/50 rounded-lg text-white placeholder-gray-400 font-gaming focus:outline-none focus:border-neon-purple focus:shadow-neon-purple transition-all duration-200"
                />
                <button
                  onClick={handleApplyPromo}
                  disabled={!promoCode.trim() || applyingPromo}
                  className="px-6 py-3 bg-gradient-to-r from-neon-purple to-neon-cyan text-white rounded-lg font-gaming font-black disabled:opacity-50 hover:scale-105 transition-all duration-200 shadow-neon-purple"
                >
                  {applyingPromo ? '...' : t('cart.apply')}
                </button>
              </div>
              {discount > 0 && (
                <div className="mt-3 text-green-400 text-sm font-gaming animate-fade-in">
                  ✓ {t('cart.discountApplied')}: -{discount.toFixed(2)} ₽
                </div>
              )}
            </div>
          </div>

          {/* Bottom Summary */}
          <div className="fixed bottom-16 left-0 right-0 backdrop-blur-xl bg-cyber-dark/95 border-t-2 border-neon-red/30 shadow-neon-red p-4 transition-all duration-300">
            <div className="space-y-2 mb-4">
              <div className="flex justify-between text-sm">
                <span className="text-gray-400 font-gaming">{t('cart.subtotal')}</span>
                <span className="font-gaming font-bold text-white">{total.toFixed(2)} ₽</span>
              </div>
              {discount > 0 && (
                <div className="flex justify-between text-sm text-green-400">
                  <span className="font-gaming">{t('cart.discount')}</span>
                  <span className="font-gaming font-bold">-{discount.toFixed(2)} ₽</span>
                </div>
              )}
              <div className="flex justify-between text-xl font-black pt-2 border-t border-neon-red/30">
                <span className="font-gaming text-neon-cyan">{t('cart.total')}</span>
                <span className="font-gaming text-neon-red drop-shadow-[0_0_10px_rgba(255,0,51,0.8)]">{finalTotal.toFixed(2)} ₽</span>
              </div>
            </div>
            <button
              onClick={() => navigate('/checkout')}
              className="w-full bg-gradient-to-r from-neon-red to-neon-purple text-white py-4 rounded-xl font-gaming font-black tracking-wide shadow-neon-red hover:shadow-neon-purple hover:scale-105 transition-all duration-300"
            >
              {t('cart.checkout')}
            </button>
          </div>
        </>
      )}

      <BottomNav />
    </div>
  )
}
