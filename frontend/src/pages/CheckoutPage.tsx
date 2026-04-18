import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import api from '../api/client'
import { useCartStore } from '../store/cartStore'
import { useUIStore } from '../store/uiStore'
import LoadingSpinner from '../components/LoadingSpinner'

type PaymentMethod = 'yukassa' | 'tinkoff' | 'cloudpayments' | 'cryptobot' | 'telegram_stars'

interface PaymentMethodOption {
  id: PaymentMethod
  name: string
  icon: string
  description: string
}

export default function CheckoutPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { items, total, fetchCart } = useCartStore()
  const { showToast } = useUIStore()
  
  const [loading, setLoading] = useState(false)
  const [selectedMethod, setSelectedMethod] = useState<PaymentMethod>('yukassa')
  const [termsAccepted, setTermsAccepted] = useState(false)

  const paymentMethods: PaymentMethodOption[] = [
    {
      id: 'yukassa',
      name: 'ЮKassa',
      icon: '💳',
      description: t('checkout.methods.yukassa')
    },
    {
      id: 'tinkoff',
      name: 'Tinkoff',
      icon: '🏦',
      description: t('checkout.methods.tinkoff')
    },
    {
      id: 'cloudpayments',
      name: 'CloudPayments',
      icon: '☁️',
      description: t('checkout.methods.cloudpayments')
    },
    {
      id: 'cryptobot',
      name: 'Crypto Bot',
      icon: '₿',
      description: t('checkout.methods.cryptobot')
    },
    {
      id: 'telegram_stars',
      name: 'Telegram Stars',
      icon: '⭐',
      description: t('checkout.methods.telegram_stars')
    }
  ]

  useEffect(() => {
    fetchCart()
  }, [fetchCart])

  useEffect(() => {
    if (items.length === 0) {
      navigate('/cart')
    }
  }, [items, navigate])

  const handleCheckout = async () => {
    if (!termsAccepted) {
      showToast(t('checkout.acceptTerms'), 'warning')
      return
    }

    try {
      setLoading(true)

      // Create order
      const orderResponse = await api.post('/orders', {
        idempotency_key: `order_${Date.now()}_${Math.random()}`
      })
      const orderId = orderResponse.data.order_id

      // Create payment
      const paymentResponse = await api.post(`/orders/${orderId}/payment`, {
        payment_method: selectedMethod
      })

      // Redirect to payment URL
      if (paymentResponse.data.payment_url) {
        window.location.href = paymentResponse.data.payment_url
      } else {
        // For Telegram Stars, use WebApp payment
        showToast(t('checkout.paymentInitiated'), 'success')
        navigate(`/orders`)
      }
    } catch (error: any) {
      console.error('Checkout error:', error)
      if (error.response?.data?.error_code === 'insufficient_stock') {
        showToast(t('errors.insufficientStock'), 'error')
      } else if (error.response?.data?.error_code === 'cart_empty') {
        showToast(t('errors.cartEmpty'), 'error')
        navigate('/cart')
      } else {
        showToast(t('errors.checkoutFailed'), 'error')
      }
    } finally {
      setLoading(false)
    }
  }

  if (items.length === 0) {
    return null
  }

  return (
    <div className="min-h-screen pb-6">
      {/* Header */}
      <div className="sticky top-0 bg-tg-bg border-b border-gray-200 p-4 z-10">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate(-1)} className="text-tg-link text-xl">
            ←
          </button>
          <h1 className="text-2xl font-bold">💳 {t('checkout.title')}</h1>
        </div>
      </div>

      <div className="p-4">
        {/* Order Summary */}
        <div className="border border-gray-200 rounded-lg p-4 mb-6 bg-white">
          <h2 className="font-semibold mb-3">{t('checkout.orderSummary')}</h2>
          <div className="space-y-2">
            {items.map((item) => (
              <div key={item.id} className="flex justify-between text-sm">
                <span className="text-gray-600">
                  {item.lot_title} × {item.quantity}
                </span>
                <span className="font-medium">
                  {(item.lot_price * item.quantity).toFixed(2)} ₽
                </span>
              </div>
            ))}
            <div className="flex justify-between text-lg font-bold pt-2 border-t border-gray-200">
              <span>{t('cart.total')}</span>
              <span className="text-tg-button">{total.toFixed(2)} ₽</span>
            </div>
          </div>
        </div>

        {/* Payment Method Selection */}
        <div className="border border-gray-200 rounded-lg p-4 mb-6 bg-white">
          <h2 className="font-semibold mb-3">{t('checkout.paymentMethod')}</h2>
          <div className="space-y-2">
            {paymentMethods.map((method) => (
              <button
                key={method.id}
                onClick={() => setSelectedMethod(method.id)}
                className={`w-full p-4 border-2 rounded-lg text-left transition-colors ${
                  selectedMethod === method.id
                    ? 'border-tg-button bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center gap-3">
                  <span className="text-3xl">{method.icon}</span>
                  <div className="flex-1">
                    <div className="font-semibold">{method.name}</div>
                    <div className="text-sm text-gray-600">{method.description}</div>
                  </div>
                  {selectedMethod === method.id && (
                    <span className="text-tg-button text-xl">✓</span>
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Terms and Conditions */}
        <div className="border border-gray-200 rounded-lg p-4 mb-6 bg-white">
          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={termsAccepted}
              onChange={(e) => setTermsAccepted(e.target.checked)}
              className="mt-1 w-5 h-5"
            />
            <span className="text-sm text-gray-600">
              {t('checkout.termsText')}{' '}
              <a href="#" className="text-tg-link underline">
                {t('checkout.termsLink')}
              </a>
            </span>
          </label>
        </div>

        {/* Important Info */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <div className="flex gap-3">
            <span className="text-2xl">ℹ️</span>
            <div className="flex-1 text-sm text-gray-700">
              <p className="font-semibold mb-1">{t('checkout.importantInfo')}</p>
              <ul className="list-disc list-inside space-y-1">
                <li>{t('checkout.info1')}</li>
                <li>{t('checkout.info2')}</li>
                <li>{t('checkout.info3')}</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Checkout Button */}
        <button
          onClick={handleCheckout}
          disabled={loading || !termsAccepted}
          className="w-full bg-tg-button text-tg-button-text py-4 rounded-lg font-semibold text-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <LoadingSpinner size="sm" />
              <span>{t('checkout.processing')}</span>
            </>
          ) : (
            <>
              <span>{t('checkout.payButton')}</span>
              <span>{total.toFixed(2)} ₽</span>
            </>
          )}
        </button>

        {/* Security Notice */}
        <div className="mt-4 text-center text-xs text-gray-500">
          <p>🔒 {t('checkout.securePayment')}</p>
        </div>
      </div>
    </div>
  )
}
