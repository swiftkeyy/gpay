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
    <div className="min-h-screen pb-32">
      {/* Header */}
      <div className="sticky top-0 bg-tg-bg border-b border-gray-200 p-4 z-10">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate(-1)} className="text-tg-link text-xl">
            ←
          </button>
          <h1 className="text-2xl font-bold">🛒 {t('nav.cart')}</h1>
        </div>
      </div>

      {items.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20">
          <div className="text-6xl mb-4">🛒</div>
          <p className="text-gray-500 mb-6">{t('cart.empty')}</p>
          <Link
            to="/"
            className="bg-tg-button text-tg-button-text px-6 py-3 rounded-lg font-semibold"
          >
            {t('cart.continueShopping')}
          </Link>
        </div>
      ) : (
        <>
          <div className="p-4">
            {/* Cart Items */}
            <div className="space-y-3 mb-6">
              {items.map((item) => (
                <div key={item.id} className="border border-gray-200 rounded-lg p-4 bg-white">
                  <div className="flex gap-3">
                    {/* Image */}
                    <Link to={`/product/${item.lot_id}`} className="flex-shrink-0">
                      <div className="w-20 h-20 bg-gray-100 rounded flex items-center justify-center">
                        {item.lot_image ? (
                          <img 
                            src={item.lot_image} 
                            alt={item.lot_title} 
                            className="w-full h-full object-cover rounded"
                          />
                        ) : (
                          <span className="text-2xl">🎮</span>
                        )}
                      </div>
                    </Link>

                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <Link to={`/product/${item.lot_id}`}>
                        <h3 className="font-semibold mb-1 line-clamp-2">{item.lot_title}</h3>
                      </Link>
                      <div className="text-lg font-bold text-tg-button mb-2">
                        {item.lot_price} ₽
                      </div>

                      {/* Quantity Controls */}
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleUpdateQuantity(item.id, item.quantity - 1)}
                          disabled={item.quantity <= 1}
                          className="w-8 h-8 border border-gray-300 rounded-lg font-bold disabled:opacity-30"
                        >
                          -
                        </button>
                        <span className="w-12 text-center font-medium">{item.quantity}</span>
                        <button
                          onClick={() => handleUpdateQuantity(item.id, item.quantity + 1)}
                          className="w-8 h-8 border border-gray-300 rounded-lg font-bold"
                        >
                          +
                        </button>
                      </div>
                    </div>

                    {/* Remove Button */}
                    <button
                      onClick={() => handleRemoveItem(item.id)}
                      className="text-red-500 text-xl self-start"
                    >
                      ✕
                    </button>
                  </div>

                  {/* Item Total */}
                  <div className="mt-3 pt-3 border-t border-gray-200 flex justify-between items-center">
                    <span className="text-sm text-gray-600">{t('cart.itemTotal')}</span>
                    <span className="font-bold">{(item.lot_price * item.quantity).toFixed(2)} ₽</span>
                  </div>
                </div>
              ))}
            </div>

            {/* Promo Code */}
            <div className="border border-gray-200 rounded-lg p-4 mb-6 bg-white">
              <h3 className="font-semibold mb-3">{t('cart.promoCode')}</h3>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={promoCode}
                  onChange={(e) => setPromoCode(e.target.value.toUpperCase())}
                  placeholder={t('cart.enterPromoCode')}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg"
                />
                <button
                  onClick={handleApplyPromo}
                  disabled={!promoCode.trim() || applyingPromo}
                  className="px-6 py-2 bg-tg-button text-tg-button-text rounded-lg font-semibold disabled:opacity-50"
                >
                  {applyingPromo ? '...' : t('cart.apply')}
                </button>
              </div>
              {discount > 0 && (
                <div className="mt-2 text-green-600 text-sm">
                  ✓ {t('cart.discountApplied')}: -{discount.toFixed(2)} ₽
                </div>
              )}
            </div>
          </div>

          {/* Bottom Summary */}
          <div className="fixed bottom-16 left-0 right-0 bg-tg-bg border-t border-gray-200 p-4">
            <div className="space-y-2 mb-4">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">{t('cart.subtotal')}</span>
                <span className="font-medium">{total.toFixed(2)} ₽</span>
              </div>
              {discount > 0 && (
                <div className="flex justify-between text-sm text-green-600">
                  <span>{t('cart.discount')}</span>
                  <span className="font-medium">-{discount.toFixed(2)} ₽</span>
                </div>
              )}
              <div className="flex justify-between text-lg font-bold pt-2 border-t border-gray-200">
                <span>{t('cart.total')}</span>
                <span className="text-tg-button">{finalTotal.toFixed(2)} ₽</span>
              </div>
            </div>
            <button
              onClick={() => navigate('/checkout')}
              className="w-full bg-tg-button text-tg-button-text py-3 rounded-lg font-semibold"
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
