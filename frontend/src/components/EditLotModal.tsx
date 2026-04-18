import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import api from '../api/client'
import { useUIStore } from '../store/uiStore'
import LoadingSpinner from './LoadingSpinner'

interface EditLotModalProps {
  lotId: number
  onClose: () => void
  onSuccess: () => void
}

interface Game {
  id: number
  name: string
}

export default function EditLotModal({ lotId, onClose, onSuccess }: EditLotModalProps) {
  const { t } = useTranslation()
  const { showToast } = useUIStore()
  
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [games, setGames] = useState<Game[]>([])
  
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    price: '',
    game_id: '',
    delivery_type: 'auto' as 'auto' | 'manual',
    stock_quantity: ''
  })

  useEffect(() => {
    fetchLotAndGames()
  }, [lotId])

  const fetchLotAndGames = async () => {
    try {
      setLoading(true)
      const [lotRes, gamesRes] = await Promise.all([
        api.get(`/sellers/me/lots/${lotId}`),
        api.get('/games', { params: { limit: 100 } })
      ])
      
      const lot = lotRes.data
      setFormData({
        title: lot.title,
        description: lot.description || '',
        price: lot.price.toString(),
        game_id: lot.game_id.toString(),
        delivery_type: lot.delivery_type,
        stock_quantity: lot.stock_quantity?.toString() || ''
      })
      
      setGames(gamesRes.data.items || [])
    } catch (error: any) {
      console.error('Fetch lot error:', error)
      showToast(t('errors.generic'), 'error')
      onClose()
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.title.trim() || !formData.price || !formData.game_id) {
      showToast(t('errors.invalidInput'), 'error')
      return
    }

    try {
      setSubmitting(true)
      await api.patch(`/sellers/me/lots/${lotId}`, {
        title: formData.title.trim(),
        description: formData.description.trim() || null,
        price: parseFloat(formData.price),
        game_id: parseInt(formData.game_id),
        delivery_type: formData.delivery_type
      })
      
      showToast(t('seller.lotUpdated'), 'success')
      onSuccess()
      onClose()
    } catch (error: any) {
      console.error('Update lot error:', error)
      showToast(error.response?.data?.detail || t('errors.generic'), 'error')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg p-6 w-full max-w-md">
          <div className="flex justify-center">
            <LoadingSpinner size="lg" />
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold">{t('lot.edit')}</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl"
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">
              {t('lot.title')} *
            </label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
              maxLength={255}
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              {t('lot.description')}
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
              rows={3}
              maxLength={2000}
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              {t('lot.price')} (₽) *
            </label>
            <input
              type="number"
              value={formData.price}
              onChange={(e) => setFormData({ ...formData, price: e.target.value })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
              min="0"
              step="0.01"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              {t('lot.game')} *
            </label>
            <select
              value={formData.game_id}
              onChange={(e) => setFormData({ ...formData, game_id: e.target.value })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
              required
            >
              <option value="">Выберите игру</option>
              {games.map(game => (
                <option key={game.id} value={game.id}>
                  {game.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              {t('lot.deliveryType')} *
            </label>
            <select
              value={formData.delivery_type}
              onChange={(e) => setFormData({ ...formData, delivery_type: e.target.value as 'auto' | 'manual' })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
              required
            >
              <option value="auto">Авто-доставка</option>
              <option value="manual">Ручная доставка</option>
            </select>
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 border border-gray-300 text-gray-700 py-2 rounded-lg font-medium"
              disabled={submitting}
            >
              {t('common.cancel')}
            </button>
            <button
              type="submit"
              className="flex-1 bg-tg-button text-tg-button-text py-2 rounded-lg font-medium disabled:opacity-50"
              disabled={submitting}
            >
              {submitting ? <LoadingSpinner size="sm" /> : t('common.save')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
