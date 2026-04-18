import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import api from '../api/client'
import { useUIStore } from '../store/uiStore'
import BottomNav from '../components/BottomNav'
import LoadingSpinner from '../components/LoadingSpinner'

interface AdminDashboard {
  users: {
    total: number
    active_today: number
    new_this_week: number
  }
  sellers: {
    total: number
    active: number
    pending: number
  }
  orders: {
    total: number
    today: number
    pending: number
  }
  revenue: {
    total: number
    today: number
    this_week: number
    this_month: number
  }
  moderation: {
    pending_lots: number
    pending_reviews: number
    active_disputes: number
    pending_withdrawals: number
  }
}

interface User {
  id: number
  telegram_id: number
  username: string | null
  first_name: string
  balance: number
  is_blocked: boolean
  created_at: string
}

interface Seller {
  id: number
  user_id: number
  shop_name: string
  status: 'pending' | 'active' | 'suspended'
  rating: number
  total_sales: number
  created_at: string
  user: {
    username: string | null
    first_name: string
  }
}

interface Lot {
  id: number
  title: string
  price: number
  status: 'pending' | 'active' | 'out_of_stock' | 'rejected'
  seller: {
    shop_name: string
  }
  game: {
    name: string
  }
  created_at: string
}

interface Dispute {
  id: number
  deal_id: number
  reason: string
  status: 'open' | 'resolved'
  created_at: string
  buyer: {
    first_name: string
  }
  seller: {
    shop_name: string
  }
}

type Tab = 'dashboard' | 'users' | 'sellers' | 'lots' | 'disputes'

export default function AdminPanel() {
  const { t } = useTranslation()
  const { showToast } = useUIStore()
  
  const [activeTab, setActiveTab] = useState<Tab>('dashboard')
  const [dashboard, setDashboard] = useState<AdminDashboard | null>(null)
  const [users, setUsers] = useState<User[]>([])
  const [sellers, setSellers] = useState<Seller[]>([])
  const [lots, setLots] = useState<Lot[]>([])
  const [disputes, setDisputes] = useState<Dispute[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    switch (activeTab) {
      case 'dashboard':
        fetchDashboard()
        break
      case 'users':
        fetchUsers()
        break
      case 'sellers':
        fetchSellers()
        break
      case 'lots':
        fetchLots()
        break
      case 'disputes':
        fetchDisputes()
        break
    }
  }, [activeTab])

  const fetchDashboard = async () => {
    try {
      setLoading(true)
      const response = await api.get('/admin/dashboard')
      setDashboard(response.data)
    } catch (error: any) {
      console.error('Fetch admin dashboard error:', error)
      if (error.response?.status === 403) {
        showToast(t('errors.accessDenied'), 'error')
      } else {
        showToast(t('errors.generic'), 'error')
      }
    } finally {
      setLoading(false)
    }
  }

  const fetchUsers = async () => {
    try {
      setLoading(true)
      const response = await api.get('/admin/users', { params: { limit: 50 } })
      setUsers(response.data.items || [])
    } catch (error: any) {
      console.error('Fetch users error:', error)
      showToast(t('errors.generic'), 'error')
    } finally {
      setLoading(false)
    }
  }

  const fetchSellers = async () => {
    try {
      setLoading(true)
      const response = await api.get('/admin/sellers', { params: { limit: 50 } })
      setSellers(response.data.items || [])
    } catch (error: any) {
      console.error('Fetch sellers error:', error)
      showToast(t('errors.generic'), 'error')
    } finally {
      setLoading(false)
    }
  }

  const fetchLots = async () => {
    try {
      setLoading(true)
      const response = await api.get('/admin/lots', { params: { limit: 50 } })
      setLots(response.data.items || [])
    } catch (error: any) {
      console.error('Fetch lots error:', error)
      showToast(t('errors.generic'), 'error')
    } finally {
      setLoading(false)
    }
  }

  const fetchDisputes = async () => {
    try {
      setLoading(true)
      const response = await api.get('/admin/disputes', { params: { limit: 50 } })
      setDisputes(response.data.items || [])
    } catch (error: any) {
      console.error('Fetch disputes error:', error)
      showToast(t('errors.generic'), 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleBlockUser = async (userId: number, block: boolean) => {
    try {
      await api.patch(`/admin/users/${userId}`, { is_blocked: block })
      showToast(block ? t('admin.userBlocked') : t('admin.userUnblocked'), 'success')
      fetchUsers()
    } catch (error: any) {
      console.error('Block user error:', error)
      showToast(t('errors.generic'), 'error')
    }
  }

  const handleApproveSeller = async (sellerId: number, approve: boolean) => {
    try {
      await api.patch(`/admin/sellers/${sellerId}`, { 
        status: approve ? 'active' : 'rejected' 
      })
      showToast(approve ? t('admin.sellerApproved') : t('admin.sellerRejected'), 'success')
      fetchSellers()
    } catch (error: any) {
      console.error('Approve seller error:', error)
      showToast(t('errors.generic'), 'error')
    }
  }

  const handleApproveLot = async (lotId: number, approve: boolean) => {
    try {
      await api.patch(`/admin/lots/${lotId}`, { 
        status: approve ? 'active' : 'rejected' 
      })
      showToast(approve ? t('admin.lotApproved') : t('admin.lotRejected'), 'success')
      fetchLots()
    } catch (error: any) {
      console.error('Approve lot error:', error)
      showToast(t('errors.generic'), 'error')
    }
  }

  const handleResolveDispute = async (disputeId: number, resolution: 'seller' | 'buyer' | 'partial') => {
    try {
      await api.post(`/admin/disputes/${disputeId}/resolve`, { resolution })
      showToast(t('admin.disputeResolved'), 'success')
      fetchDisputes()
    } catch (error: any) {
      console.error('Resolve dispute error:', error)
      showToast(t('errors.generic'), 'error')
    }
  }

  if (loading && !dashboard) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <div className="min-h-screen pb-20">
      {/* Header */}
      <div className="sticky top-0 bg-tg-bg border-b border-gray-200 p-4 z-10">
        <h1 className="text-2xl font-bold mb-3">⚙️ {t('admin.title')}</h1>
        
        {/* Tabs */}
        <div className="flex gap-2 overflow-x-auto pb-2 -mx-4 px-4">
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap ${
              activeTab === 'dashboard'
                ? 'bg-tg-button text-tg-button-text'
                : 'bg-gray-100 text-gray-700'
            }`}
          >
            📊 {t('admin.dashboard')}
          </button>
          <button
            onClick={() => setActiveTab('users')}
            className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap ${
              activeTab === 'users'
                ? 'bg-tg-button text-tg-button-text'
                : 'bg-gray-100 text-gray-700'
            }`}
          >
            👥 {t('admin.users')}
          </button>
          <button
            onClick={() => setActiveTab('sellers')}
            className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap ${
              activeTab === 'sellers'
                ? 'bg-tg-button text-tg-button-text'
                : 'bg-gray-100 text-gray-700'
            }`}
          >
            💼 {t('admin.sellers')}
          </button>
          <button
            onClick={() => setActiveTab('lots')}
            className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap ${
              activeTab === 'lots'
                ? 'bg-tg-button text-tg-button-text'
                : 'bg-gray-100 text-gray-700'
            }`}
          >
            📦 {t('admin.lots')}
          </button>
          <button
            onClick={() => setActiveTab('disputes')}
            className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap ${
              activeTab === 'disputes'
                ? 'bg-tg-button text-tg-button-text'
                : 'bg-gray-100 text-gray-700'
            }`}
          >
            ⚖️ {t('admin.disputes')}
          </button>
        </div>
      </div>

      <div className="p-4">
        {/* Dashboard Tab */}
        {activeTab === 'dashboard' && dashboard && (
          <>
            {/* Revenue Card */}
            <div className="bg-gradient-to-br from-purple-500 to-indigo-600 text-white rounded-lg p-6 mb-4">
              <div className="text-sm opacity-90 mb-1">{t('admin.totalRevenue')}</div>
              <div className="text-4xl font-bold mb-4">
                {dashboard.revenue.total.toFixed(2)} ₽
              </div>
              <div className="grid grid-cols-3 gap-3 text-sm">
                <div>
                  <div className="opacity-75">{t('admin.today')}</div>
                  <div className="font-semibold">{dashboard.revenue.today.toFixed(0)} ₽</div>
                </div>
                <div>
                  <div className="opacity-75">{t('admin.thisWeek')}</div>
                  <div className="font-semibold">{dashboard.revenue.this_week.toFixed(0)} ₽</div>
                </div>
                <div>
                  <div className="opacity-75">{t('admin.thisMonth')}</div>
                  <div className="font-semibold">{dashboard.revenue.this_month.toFixed(0)} ₽</div>
                </div>
              </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 gap-3 mb-4">
              <div className="border border-gray-200 rounded-lg p-4 bg-white">
                <div className="text-sm text-gray-600 mb-1">{t('admin.totalUsers')}</div>
                <div className="text-3xl font-bold mb-1">{dashboard.users.total}</div>
                <div className="text-xs text-green-600">
                  +{dashboard.users.new_this_week} {t('admin.thisWeek')}
                </div>
              </div>
              <div className="border border-gray-200 rounded-lg p-4 bg-white">
                <div className="text-sm text-gray-600 mb-1">{t('admin.activeSellers')}</div>
                <div className="text-3xl font-bold mb-1">{dashboard.sellers.active}</div>
                <div className="text-xs text-yellow-600">
                  {dashboard.sellers.pending} {t('admin.pending')}
                </div>
              </div>
              <div className="border border-gray-200 rounded-lg p-4 bg-white">
                <div className="text-sm text-gray-600 mb-1">{t('admin.totalOrders')}</div>
                <div className="text-3xl font-bold mb-1">{dashboard.orders.total}</div>
                <div className="text-xs text-blue-600">
                  {dashboard.orders.today} {t('admin.today')}
                </div>
              </div>
              <div className="border border-gray-200 rounded-lg p-4 bg-white">
                <div className="text-sm text-gray-600 mb-1">{t('admin.activeDisputes')}</div>
                <div className="text-3xl font-bold mb-1">{dashboard.moderation.active_disputes}</div>
                <div className="text-xs text-red-600">
                  {t('admin.needsAttention')}
                </div>
              </div>
            </div>

            {/* Moderation Queue */}
            <div className="border border-gray-200 rounded-lg p-4 bg-white mb-4">
              <h3 className="font-semibold mb-3">{t('admin.moderationQueue')}</h3>
              <div className="space-y-2">
                <button className="w-full flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">💼</span>
                    <span className="font-medium">{t('admin.pendingSellers')}</span>
                  </div>
                  <span className="bg-yellow-100 text-yellow-800 px-3 py-1 rounded-full text-sm font-semibold">
                    {dashboard.sellers.pending}
                  </span>
                </button>
                <button className="w-full flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">📦</span>
                    <span className="font-medium">{t('admin.pendingLots')}</span>
                  </div>
                  <span className="bg-yellow-100 text-yellow-800 px-3 py-1 rounded-full text-sm font-semibold">
                    {dashboard.moderation.pending_lots}
                  </span>
                </button>
                <button className="w-full flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">⭐</span>
                    <span className="font-medium">{t('admin.pendingReviews')}</span>
                  </div>
                  <span className="bg-yellow-100 text-yellow-800 px-3 py-1 rounded-full text-sm font-semibold">
                    {dashboard.moderation.pending_reviews}
                  </span>
                </button>
                <button className="w-full flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">💰</span>
                    <span className="font-medium">{t('admin.pendingWithdrawals')}</span>
                  </div>
                  <span className="bg-yellow-100 text-yellow-800 px-3 py-1 rounded-full text-sm font-semibold">
                    {dashboard.moderation.pending_withdrawals}
                  </span>
                </button>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="space-y-2">
              <button className="w-full flex items-center justify-between border border-gray-200 rounded-lg p-4 hover:bg-gray-50 bg-white">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">📢</span>
                  <span className="font-medium">{t('admin.sendBroadcast')}</span>
                </div>
                <span className="text-gray-400">›</span>
              </button>
              <button className="w-full flex items-center justify-between border border-gray-200 rounded-lg p-4 hover:bg-gray-50 bg-white">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">📊</span>
                  <span className="font-medium">{t('admin.viewAnalytics')}</span>
                </div>
                <span className="text-gray-400">›</span>
              </button>
              <button className="w-full flex items-center justify-between border border-gray-200 rounded-lg p-4 hover:bg-gray-50 bg-white">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">📝</span>
                  <span className="font-medium">{t('admin.auditLogs')}</span>
                </div>
                <span className="text-gray-400">›</span>
              </button>
            </div>
          </>
        )}

        {/* Other Tabs */}
        {activeTab === 'users' && (
          <div className="space-y-3">
            <h2 className="text-xl font-bold mb-4">{t('admin.userManagement')}</h2>
            {loading ? (
              <div className="flex justify-center py-10">
                <LoadingSpinner size="lg" />
              </div>
            ) : users.length === 0 ? (
              <div className="text-center py-10 text-gray-500">
                {t('admin.noUsers')}
              </div>
            ) : (
              users.map(user => (
                <div key={user.id} className="border border-gray-200 rounded-lg p-4 bg-white">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <div className="font-semibold">
                        {user.first_name} {user.username && `(@${user.username})`}
                      </div>
                      <div className="text-sm text-gray-600">ID: {user.telegram_id}</div>
                      <div className="text-sm text-gray-600">
                        {t('admin.balance')}: {user.balance.toFixed(2)} ₽
                      </div>
                    </div>
                    {user.is_blocked && (
                      <span className="bg-red-100 text-red-800 px-2 py-1 rounded text-xs font-semibold">
                        {t('admin.blocked')}
                      </span>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleBlockUser(user.id, !user.is_blocked)}
                      className={`flex-1 py-2 rounded-lg text-sm font-medium ${
                        user.is_blocked
                          ? 'bg-green-500 text-white'
                          : 'bg-red-500 text-white'
                      }`}
                    >
                      {user.is_blocked ? t('admin.unblock') : t('admin.block')}
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'sellers' && (
          <div className="space-y-3">
            <h2 className="text-xl font-bold mb-4">{t('admin.sellerManagement')}</h2>
            {loading ? (
              <div className="flex justify-center py-10">
                <LoadingSpinner size="lg" />
              </div>
            ) : sellers.length === 0 ? (
              <div className="text-center py-10 text-gray-500">
                {t('admin.noSellers')}
              </div>
            ) : (
              sellers.map(seller => (
                <div key={seller.id} className="border border-gray-200 rounded-lg p-4 bg-white">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <div className="font-semibold">{seller.shop_name}</div>
                      <div className="text-sm text-gray-600">
                        {seller.user.first_name} {seller.user.username && `(@${seller.user.username})`}
                      </div>
                      <div className="text-sm text-gray-600">
                        ⭐ {seller.rating.toFixed(1)} • {seller.total_sales} {t('admin.sales')}
                      </div>
                    </div>
                    <span className={`px-2 py-1 rounded text-xs font-semibold ${
                      seller.status === 'active' ? 'bg-green-100 text-green-800' :
                      seller.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {t(`admin.status.${seller.status}`)}
                    </span>
                  </div>
                  {seller.status === 'pending' && (
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleApproveSeller(seller.id, true)}
                        className="flex-1 bg-green-500 text-white py-2 rounded-lg text-sm font-medium"
                      >
                        ✓ {t('admin.approve')}
                      </button>
                      <button
                        onClick={() => handleApproveSeller(seller.id, false)}
                        className="flex-1 bg-red-500 text-white py-2 rounded-lg text-sm font-medium"
                      >
                        ✗ {t('admin.reject')}
                      </button>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'lots' && (
          <div className="space-y-3">
            <h2 className="text-xl font-bold mb-4">{t('admin.lotManagement')}</h2>
            {loading ? (
              <div className="flex justify-center py-10">
                <LoadingSpinner size="lg" />
              </div>
            ) : lots.length === 0 ? (
              <div className="text-center py-10 text-gray-500">
                {t('admin.noLots')}
              </div>
            ) : (
              lots.map(lot => (
                <div key={lot.id} className="border border-gray-200 rounded-lg p-4 bg-white">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <div className="font-semibold">{lot.title}</div>
                      <div className="text-sm text-gray-600">
                        {lot.game.name} • {lot.seller.shop_name}
                      </div>
                      <div className="text-lg font-bold text-tg-button mt-1">
                        {lot.price.toFixed(2)} ₽
                      </div>
                    </div>
                    <span className={`px-2 py-1 rounded text-xs font-semibold ${
                      lot.status === 'active' ? 'bg-green-100 text-green-800' :
                      lot.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                      lot.status === 'rejected' ? 'bg-red-100 text-red-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {t(`admin.status.${lot.status}`)}
                    </span>
                  </div>
                  {lot.status === 'pending' && (
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleApproveLot(lot.id, true)}
                        className="flex-1 bg-green-500 text-white py-2 rounded-lg text-sm font-medium"
                      >
                        ✓ {t('admin.approve')}
                      </button>
                      <button
                        onClick={() => handleApproveLot(lot.id, false)}
                        className="flex-1 bg-red-500 text-white py-2 rounded-lg text-sm font-medium"
                      >
                        ✗ {t('admin.reject')}
                      </button>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'disputes' && (
          <div className="space-y-3">
            <h2 className="text-xl font-bold mb-4">{t('admin.disputeManagement')}</h2>
            {loading ? (
              <div className="flex justify-center py-10">
                <LoadingSpinner size="lg" />
              </div>
            ) : disputes.length === 0 ? (
              <div className="text-center py-10 text-gray-500">
                {t('admin.noDisputes')}
              </div>
            ) : (
              disputes.map(dispute => (
                <div key={dispute.id} className="border border-gray-200 rounded-lg p-4 bg-white">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <div className="font-semibold">
                        {t('admin.dispute')} #{dispute.deal_id}
                      </div>
                      <div className="text-sm text-gray-600 mt-1">
                        {dispute.buyer.first_name} vs {dispute.seller.shop_name}
                      </div>
                      <div className="text-sm text-gray-700 mt-2 bg-gray-50 p-2 rounded">
                        {dispute.reason}
                      </div>
                    </div>
                    <span className={`px-2 py-1 rounded text-xs font-semibold ${
                      dispute.status === 'open' ? 'bg-red-100 text-red-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {t(`admin.status.${dispute.status}`)}
                    </span>
                  </div>
                  {dispute.status === 'open' && (
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleResolveDispute(dispute.id, 'seller')}
                        className="flex-1 bg-blue-500 text-white py-2 rounded-lg text-xs font-medium"
                      >
                        → {t('admin.toSeller')}
                      </button>
                      <button
                        onClick={() => handleResolveDispute(dispute.id, 'buyer')}
                        className="flex-1 bg-green-500 text-white py-2 rounded-lg text-xs font-medium"
                      >
                        ← {t('admin.toBuyer')}
                      </button>
                      <button
                        onClick={() => handleResolveDispute(dispute.id, 'partial')}
                        className="flex-1 bg-purple-500 text-white py-2 rounded-lg text-xs font-medium"
                      >
                        ⚖️ {t('admin.partial')}
                      </button>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        )}
      </div>

      <BottomNav />
    </div>
  )
}
