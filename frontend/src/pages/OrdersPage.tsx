import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import api from '../api/client'
import { useUIStore } from '../store/uiStore'
import BottomNav from '../components/BottomNav'
import LoadingSpinner from '../components/LoadingSpinner'

interface Order {
  id: number
  status: string
  total_amount: number
  currency_code: string
  created_at: string
  items_count: number
  deal_id?: number
  payment_method?: string
}

type OrderStatus = 'all' | 'pending' | 'paid' | 'completed' | 'cancelled'

export default function OrdersPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { showToast } = useUIStore()
  
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<OrderStatus>('all')
  const [selectedOrder, setSelectedOrder] = useState<number | null>(null)

  useEffect(() => {
    fetchOrders()
  }, [filter])

  const fetchOrders = async () => {
    try {
      setLoading(true)
      const params: any = { limit: 50 }
      if (filter !== 'all') {
        params.status = filter
      }
      const response = await api.get('/orders', { params })
      setOrders(response.data.items)
    } catch (error) {
      console.error('Fetch orders error:', error)
      showToast(t('errors.generic'), 'error')
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      pending: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      paid: 'bg-blue-100 text-blue-800 border-blue-200',
      completed: 'bg-green-100 text-green-800 border-green-200',
      cancelled: 'bg-red-100 text-red-800 border-red-200',
      refunded: 'bg-gray-100 text-gray-800 border-gray-200'
    }
    return colors[status] || 'bg-gray-100 text-gray-800 border-gray-200'
  }

  const getStatusText = (status: string) => {
    const texts: Record<string, string> = {
      pending: t('order.status.pending'),
      paid: t('order.status.paid'),
      completed: t('order.status.completed'),
      cancelled: t('order.status.cancelled'),
      refunded: t('order.status.refunded')
    }
    return texts[status] || status
  }

  const getStatusIcon = (status: string) => {
    const icons: Record<string, string> = {
      pending: '⏳',
      paid: '💳',
      completed: '✅',
      cancelled: '❌',
      refunded: '↩️'
    }
    return icons[status] || '📦'
  }

  const filters: { value: OrderStatus; label: string }[] = [
    { value: 'all', label: t('order.filter.all') },
    { value: 'pending', label: t('order.filter.pending') },
    { value: 'paid', label: t('order.filter.paid') },
    { value: 'completed', label: t('order.filter.completed') },
    { value: 'cancelled', label: t('order.filter.cancelled') }
  ]

  return (
    <div className="min-h-screen pb-20">
      {/* Header */}
      <div className="sticky top-0 bg-tg-bg border-b border-gray-200 p-4 z-10">
        <h1 className="text-2xl font-bold mb-3">📦 {t('nav.orders')}</h1>
        
        {/* Filter Tabs */}
        <div className="flex gap-2 overflow-x-auto pb-2 -mx-4 px-4">
          {filters.map((f) => (
            <button
              key={f.value}
              onClick={() => setFilter(f.value)}
              className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
                filter === f.value
                  ? 'bg-tg-button text-tg-button-text'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      <div className="p-4">
        {loading ? (
          <div className="flex justify-center py-10">
            <LoadingSpinner size="lg" />
          </div>
        ) : orders.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="text-6xl mb-4">📦</div>
            <p className="text-gray-500 mb-6">{t('order.noOrders')}</p>
            <Link
              to="/"
              className="bg-tg-button text-tg-button-text px-6 py-3 rounded-lg font-semibold"
            >
              {t('order.startShopping')}
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {orders.map((order) => (
              <div
                key={order.id}
                className="border border-gray-200 rounded-lg p-4 bg-white"
              >
                {/* Order Header */}
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <div className="font-semibold text-lg">
                      {t('order.orderNumber', { number: order.id })}
                    </div>
                    <div className="text-sm text-gray-500">
                      {new Date(order.created_at).toLocaleString()}
                    </div>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(order.status)}`}>
                    {getStatusIcon(order.status)} {getStatusText(order.status)}
                  </span>
                </div>

                {/* Order Details */}
                <div className="space-y-2 mb-3">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">{t('order.items')}</span>
                    <span className="font-medium">{order.items_count}</span>
                  </div>
                  {order.payment_method && (
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">{t('order.paymentMethod')}</span>
                      <span className="font-medium">{order.payment_method}</span>
                    </div>
                  )}
                  <div className="flex justify-between text-lg font-bold pt-2 border-t border-gray-200">
                    <span>{t('cart.total')}</span>
                    <span className="text-tg-button">
                      {order.total_amount.toFixed(2)} {order.currency_code}
                    </span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-2">
                  <button
                    onClick={() => setSelectedOrder(selectedOrder === order.id ? null : order.id)}
                    className="flex-1 border border-gray-300 text-gray-700 py-2 rounded-lg text-sm font-medium hover:bg-gray-50"
                  >
                    {selectedOrder === order.id ? t('order.hideDetails') : t('order.viewDetails')}
                  </button>
                  {order.deal_id && (
                    <Link
                      to={`/chat/${order.deal_id}`}
                      className="flex-1 bg-tg-button text-tg-button-text py-2 rounded-lg text-sm font-medium text-center"
                    >
                      💬 {t('order.chat')}
                    </Link>
                  )}
                </div>

                {/* Expanded Details */}
                {selectedOrder === order.id && (
                  <div className="mt-3 pt-3 border-t border-gray-200">
                    <div className="text-sm text-gray-600">
                      <p className="mb-2">{t('order.detailsPlaceholder')}</p>
                      {order.status === 'completed' && (
                        <button className="text-tg-link underline">
                          {t('order.leaveReview')}
                        </button>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      <BottomNav />
    </div>
  )
}
