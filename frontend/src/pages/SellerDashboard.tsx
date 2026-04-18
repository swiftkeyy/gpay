import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import api from '../api/client'
import { useUIStore } from '../store/uiStore'
import BottomNav from '../components/BottomNav'
import LoadingSpinner from '../components/LoadingSpinner'
import CreateLotModal from '../components/CreateLotModal'
import EditLotModal from '../components/EditLotModal'
import WithdrawModal from '../components/WithdrawModal'

interface SellerDashboard {
  balance: {
    available: number
    pending_withdrawals: number
    escrow_held: number
  }
  today: {
    sales: number
    revenue: number
    orders: number
  }
  week: {
    sales: number
    revenue: number
    orders: number
  }
  month: {
    sales: number
    revenue: number
    orders: number
  }
  all_time: {
    sales: number
    revenue: number
    orders: number
  }
  performance: {
    rating: number
    total_reviews: number
    response_time_minutes: number
    completion_rate: number
  }
}

interface Lot {
  id: number
  title: string
  price: number
  stock_count: number
  status: string
  is_featured: boolean
  total_sales: number
}

type Tab = 'dashboard' | 'lots' | 'withdrawals'

export default function SellerDashboard() {
  const { t } = useTranslation()
  const { showToast } = useUIStore()
  
  const [activeTab, setActiveTab] = useState<Tab>('dashboard')
  const [dashboard, setDashboard] = useState<SellerDashboard | null>(null)
  const [lots, setLots] = useState<Lot[]>([])
  const [loading, setLoading] = useState(true)
  const [isSeller, setIsSeller] = useState(false)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showWithdrawModal, setShowWithdrawModal] = useState(false)
  const [editingLotId, setEditingLotId] = useState<number | null>(null)

  useEffect(() => {
    checkSellerStatus()
  }, [])

  useEffect(() => {
    if (isSeller) {
      if (activeTab === 'dashboard') {
        fetchDashboard()
      } else if (activeTab === 'lots') {
        fetchLots()
      }
    }
  }, [activeTab, isSeller])

  const checkSellerStatus = async () => {
    try {
      await api.get('/sellers/me')
      setIsSeller(true)
      setLoading(false)
    } catch (error: any) {
      if (error.response?.status === 404) {
        setIsSeller(false)
      }
      setLoading(false)
    }
  }

  const fetchDashboard = async () => {
    try {
      setLoading(true)
      const response = await api.get('/sellers/me/dashboard')
      setDashboard(response.data)
    } catch (error) {
      console.error('Fetch dashboard error:', error)
      showToast(t('errors.generic'), 'error')
    } finally {
      setLoading(false)
    }
  }

  const fetchLots = async () => {
    try {
      setLoading(true)
      const response = await api.get('/sellers/me/lots')
      setLots(response.data.items)
    } catch (error) {
      console.error('Fetch lots error:', error)
      showToast(t('errors.generic'), 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleApplyAsSeller = async () => {
    try {
      await api.post('/sellers/apply', {
        shop_name: 'My Shop',
        description: 'My shop description'
      })
      showToast(t('seller.applicationSubmitted'), 'success')
      checkSellerStatus()
    } catch (error) {
      showToast(t('errors.generic'), 'error')
    }
  }

  const handleEditLot = (lotId: number) => {
    setEditingLotId(lotId)
    setShowEditModal(true)
  }

  const handleDeleteLot = async (lotId: number) => {
    if (!confirm(t('lot.confirmDelete'))) return
    
    try {
      await api.delete(`/sellers/me/lots/${lotId}`)
      showToast(t('lot.deleted'), 'success')
      fetchLots()
    } catch (error: any) {
      console.error('Delete lot error:', error)
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

  if (!isSeller) {
    return (
      <div className="min-h-screen pb-20">
        <div className="p-4">
          <h1 className="text-2xl font-bold mb-6">💼 {t('seller.title')}</h1>
          
          <div className="text-center py-10">
            <div className="text-6xl mb-4">🏪</div>
            <h2 className="text-xl font-bold mb-2">{t('seller.notSeller')}</h2>
            <p className="text-gray-600 mb-6">{t('seller.becomeSellerText')}</p>
            
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6 text-left">
              <h3 className="font-semibold mb-2">{t('seller.benefits')}</h3>
              <ul className="space-y-2 text-sm">
                <li>✓ {t('seller.benefit1')}</li>
                <li>✓ {t('seller.benefit2')}</li>
                <li>✓ {t('seller.benefit3')}</li>
                <li>✓ {t('seller.benefit4')}</li>
              </ul>
            </div>

            <button
              onClick={handleApplyAsSeller}
              className="bg-tg-button text-tg-button-text px-8 py-3 rounded-lg font-semibold text-lg"
            >
              {t('seller.applyNow')}
            </button>
          </div>
        </div>
        <BottomNav />
      </div>
    )
  }

  return (
    <div className="min-h-screen pb-20">
      {/* Header */}
      <div className="sticky top-0 bg-tg-bg border-b border-gray-200 p-4 z-10">
        <h1 className="text-2xl font-bold mb-3">💼 {t('seller.dashboard')}</h1>
        
        {/* Tabs */}
        <div className="flex gap-2">
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`flex-1 py-2 rounded-lg text-sm font-medium ${
              activeTab === 'dashboard'
                ? 'bg-tg-button text-tg-button-text'
                : 'bg-gray-100 text-gray-700'
            }`}
          >
            📊 {t('seller.stats')}
          </button>
          <button
            onClick={() => setActiveTab('lots')}
            className={`flex-1 py-2 rounded-lg text-sm font-medium ${
              activeTab === 'lots'
                ? 'bg-tg-button text-tg-button-text'
                : 'bg-gray-100 text-gray-700'
            }`}
          >
            📦 {t('seller.lots')}
          </button>
          <button
            onClick={() => setActiveTab('withdrawals')}
            className={`flex-1 py-2 rounded-lg text-sm font-medium ${
              activeTab === 'withdrawals'
                ? 'bg-tg-button text-tg-button-text'
                : 'bg-gray-100 text-gray-700'
            }`}
          >
            💰 {t('seller.withdrawals')}
          </button>
        </div>
      </div>

      <div className="p-4">
        {/* Dashboard Tab */}
        {activeTab === 'dashboard' && dashboard && (
          <>
            {/* Balance Card */}
            <div className="bg-gradient-to-br from-green-500 to-emerald-600 text-white rounded-lg p-6 mb-4">
              <div className="text-sm opacity-90 mb-1">{t('seller.availableBalance')}</div>
              <div className="text-4xl font-bold mb-4">
                {dashboard.balance.available.toFixed(2)} ₽
              </div>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <div className="opacity-75">{t('seller.inEscrow')}</div>
                  <div className="font-semibold">{dashboard.balance.escrow_held.toFixed(2)} ₽</div>
                </div>
                <div>
                  <div className="opacity-75">{t('seller.pending')}</div>
                  <div className="font-semibold">{dashboard.balance.pending_withdrawals.toFixed(2)} ₽</div>
                </div>
              </div>
              <button 
                onClick={() => setShowWithdrawModal(true)}
                className="w-full mt-4 bg-white text-green-600 py-2 rounded-lg font-semibold"
              >
                {t('seller.withdraw')}
              </button>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 gap-3 mb-4">
              <div className="border border-gray-200 rounded-lg p-4 bg-white">
                <div className="text-sm text-gray-600 mb-1">{t('seller.today')}</div>
                <div className="text-2xl font-bold">{dashboard.today.sales}</div>
                <div className="text-xs text-gray-500">{dashboard.today.revenue.toFixed(0)} ₽</div>
              </div>
              <div className="border border-gray-200 rounded-lg p-4 bg-white">
                <div className="text-sm text-gray-600 mb-1">{t('seller.thisWeek')}</div>
                <div className="text-2xl font-bold">{dashboard.week.sales}</div>
                <div className="text-xs text-gray-500">{dashboard.week.revenue.toFixed(0)} ₽</div>
              </div>
              <div className="border border-gray-200 rounded-lg p-4 bg-white">
                <div className="text-sm text-gray-600 mb-1">{t('seller.thisMonth')}</div>
                <div className="text-2xl font-bold">{dashboard.month.sales}</div>
                <div className="text-xs text-gray-500">{dashboard.month.revenue.toFixed(0)} ₽</div>
              </div>
              <div className="border border-gray-200 rounded-lg p-4 bg-white">
                <div className="text-sm text-gray-600 mb-1">{t('seller.allTime')}</div>
                <div className="text-2xl font-bold">{dashboard.all_time.sales}</div>
                <div className="text-xs text-gray-500">{dashboard.all_time.revenue.toFixed(0)} ₽</div>
              </div>
            </div>

            {/* Performance */}
            <div className="border border-gray-200 rounded-lg p-4 bg-white">
              <h3 className="font-semibold mb-3">{t('seller.performance')}</h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">{t('seller.rating')}</span>
                  <span className="font-semibold">
                    ⭐ {dashboard.performance.rating.toFixed(1)} ({dashboard.performance.total_reviews})
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">{t('seller.responseTime')}</span>
                  <span className="font-semibold">{dashboard.performance.response_time_minutes} мин</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">{t('seller.completionRate')}</span>
                  <span className="font-semibold">{(dashboard.performance.completion_rate * 100).toFixed(1)}%</span>
                </div>
              </div>
            </div>
          </>
        )}

        {/* Lots Tab */}
        {activeTab === 'lots' && (
          <>
            <button 
              onClick={() => setShowCreateModal(true)}
              className="w-full bg-tg-button text-tg-button-text py-3 rounded-lg font-semibold mb-4"
            >
              ➕ {t('seller.createLot')}
            </button>

            {loading ? (
              <div className="flex justify-center py-10">
                <LoadingSpinner size="lg" />
              </div>
            ) : lots.length === 0 ? (
              <div className="text-center py-10 text-gray-500">
                {t('seller.noLots')}
              </div>
            ) : (
              <div className="space-y-3">
                {lots.map((lot) => (
                  <div key={lot.id} className="border border-gray-200 rounded-lg p-4 bg-white">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="font-semibold flex-1">{lot.title}</h3>
                      {lot.is_featured && <span className="text-yellow-500">⭐</span>}
                    </div>
                    <div className="flex justify-between items-center mb-3">
                      <span className="text-lg font-bold">{lot.price} ₽</span>
                      <span className={`px-2 py-1 rounded text-xs ${
                        lot.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                      }`}>
                        {lot.status}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm text-gray-600 mb-3">
                      <span>{t('seller.stock')}: {lot.stock_count}</span>
                      <span>{t('seller.sold')}: {lot.total_sales}</span>
                    </div>
                    <div className="flex gap-2">
                      <button 
                        onClick={() => handleEditLot(lot.id)}
                        className="flex-1 border border-gray-300 py-2 rounded-lg text-sm"
                      >
                        ✏️ {t('common.edit')}
                      </button>
                      <button 
                        onClick={() => handleDeleteLot(lot.id)}
                        className="border border-red-300 text-red-600 px-3 py-2 rounded-lg text-sm"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {/* Withdrawals Tab */}
        {activeTab === 'withdrawals' && (
          <div className="text-center py-10 text-gray-500">
            {t('seller.withdrawalsPlaceholder')}
          </div>
        )}
      </div>

      {/* Create Lot Modal */}
      {showCreateModal && (
        <CreateLotModal
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            fetchLots()
            setActiveTab('lots')
          }}
        />
      )}

      {/* Edit Lot Modal */}
      {showEditModal && editingLotId && (
        <EditLotModal
          lotId={editingLotId}
          onClose={() => {
            setShowEditModal(false)
            setEditingLotId(null)
          }}
          onSuccess={() => {
            fetchLots()
          }}
        />
      )}

      {/* Withdraw Modal */}
      {showWithdrawModal && dashboard && (
        <WithdrawModal
          availableBalance={dashboard.balance.available}
          onClose={() => setShowWithdrawModal(false)}
          onSuccess={() => {
            fetchDashboard()
          }}
        />
      )}

      <BottomNav />
    </div>
  )
}
