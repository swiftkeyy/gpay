import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import api from '../api/client'
import { useUIStore } from '../store/uiStore'
import BottomNav from '../components/BottomNav'

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
      pending: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50',
      paid: 'bg-blue-500/20 text-blue-400 border-blue-500/50',
      completed: 'bg-green-500/20 text-green-400 border-green-500/50',
      cancelled: 'bg-red-500/20 text-red-400 border-red-500/50',
      refunded: 'bg-gray-500/20 text-gray-400 border-gray-500/50'
    }
    return colors[status] || 'bg-gray-500/20 text-gray-400 border-gray-500/50'
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
    <div className="min-h-screen pb-20 bg-cyber-dark relative overflow-hidden">
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
        <h1 className="text-2xl font-black font-gaming text-neon-red drop-shadow-[0_0_10px_rgba(255,0,51,0.8)] mb-3">📦 {t('nav.orders')}</h1>
        
        {/* Filter Tabs */}
        <div className="flex gap-2 overflow-x-auto pb-2 -mx-4 px-4 scrollbar-hide">
          {filters.map((f) => (
            <button
              key={f.value}
              onClick={() => setFilter(f.value)}
              className={`px-4 py-2 rounded-lg text-sm font-gaming font-bold whitespace-nowrap transition-all duration-200 hover:scale-105 ${
                filter === f.value
                  ? 'bg-gradient-to-r from-neon-red to-neon-purple text-white shadow-neon-red'
                  : 'bg-black/60 border-2 border-gray-700 text-gray-400 hover:border-neon-red/50 hover:text-white'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      <div className="p-4 relative z-10">
        {loading ? (
          <div className="flex justify-center py-10">
            <div className="inline-block animate-spin text-6xl">⚡</div>
          </div>
        ) : orders.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="text-8xl mb-4 animate-float">📦</div>
            <p className="text-gray-400 mb-6 font-gaming text-lg">{t('order.noOrders')}</p>
            <Link
              to="/"
              className="bg-gradient-to-r from-neon-red to-neon-purple text-white px-8 py-4 rounded-xl font-gaming font-black tracking-wide shadow-neon-red hover:shadow-neon-purple hover:scale-105 transition-all duration-300"
            >
              {t('order.startShopping')}
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {orders.map((order) => (
              <div
                key={order.id}
                className="relative overflow-hidden rounded-xl bg-black/40 backdrop-blur-sm border-2 border-neon-red/30 p-4 hover:border-neon-red hover:shadow-neon-red-lg transition-all duration-300 hover:scale-[1.02]"
              >
                {/* Order Header */}
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <div className="font-gaming font-black text-white text-lg">
                      {t('order.orderNumber', { number: order.id })}
                    </div>
                    <div className="text-sm text-gray-400 font-gaming">
                      {new Date(order.created_at).toLocaleString()}
                    </div>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-gaming font-black border-2 ${getStatusColor(order.status)}`}>
                    {getStatusIcon(order.status)} {getStatusText(order.status)}
                  </span>
                </div>

                {/* Order Details */}
                <div className="space-y-2 mb-3">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-400 font-gaming">{t('order.items')}</span>
                    <span className="font-gaming font-bold text-white">{order.items_count}</span>
                  </div>
                  {order.payment_method && (
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-400 font-gaming">{t('order.paymentMethod')}</span>
                      <span className="font-gaming font-bold text-white">{order.payment_method}</span>
                    </div>
                  )}
                  <div className="flex justify-between text-xl font-black pt-2 border-t border-neon-red/30">
                    <span className="font-gaming text-neon-cyan">{t('cart.total')}</span>
                    <span className="font-gaming text-neon-red drop-shadow-[0_0_10px_rgba(255,0,51,0.8)]">
                      {order.total_amount.toFixed(2)} {order.currency_code}
                    </span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-2">
                  <button
                    onClick={() => setSelectedOrder(selectedOrder === order.id ? null : order.id)}
                    className="flex-1 border-2 border-neon-purple text-neon-purple py-2 rounded-lg text-sm font-gaming font-bold hover:bg-neon-purple/10 hover:shadow-neon-purple hover:scale-105 transition-all duration-200"
                  >
                    {selectedOrder === order.id ? t('order.hideDetails') : t('order.viewDetails')}
                  </button>
                  {order.deal_id && (
                    <Link
                      to={`/chat/${order.deal_id}`}
                      className="flex-1 bg-gradient-to-r from-neon-cyan to-neon-purple text-white py-2 rounded-lg text-sm font-gaming font-bold text-center shadow-neon-cyan hover:scale-105 transition-all duration-200"
                    >
                      💬 {t('order.chat')}
                    </Link>
                  )}
                </div>

                {/* Expanded Details */}
                {selectedOrder === order.id && (
                  <div className="mt-3 pt-3 border-t border-neon-purple/30 animate-slide-down">
                    <div className="text-sm text-gray-300 font-gaming">
                      <p className="mb-2">{t('order.detailsPlaceholder')}</p>
                      {order.status === 'completed' && (
                        <button className="text-neon-cyan underline hover:text-white transition-colors duration-200">
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
