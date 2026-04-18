import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import api from '../api/client'
import { useUIStore } from '../store/uiStore'
import LoadingSpinner from './LoadingSpinner'

interface CreateLotModalProps {
  onClose: () => void
  onSuccess: () => void
}

export default function CreateLotModal({ onClose, onSuccess }: CreateLotModalProps) {
  const { t } = useTranslation()
  const { showToast } = useUIStore()
  
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    price: '',
    game_id: '',
    category_id: '',
    product_id: '',
    delivery_type: 'manual' as 'auto' | 'manual',
    delivery_time_minutes: '60',
    stock_count: '1'
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.title || !formData.price || !formData.game_id) {
      showToast(t('errors.invalidInput'), 'error')
      return
    }

    try {
      setLoading(true)
      await api.post('/sellers/me/lots', {
        title: formData.title,
        description: formData.description,
        price: parseFloat(formData.price),
        game_id: parseInt(formData.game_id),
        category_id: formData.category_id ? parseInt(formData.category_id) : null,
        product_id: formData.product_id ? parseInt(formData.product_id) : null,
        delivery_type: formData.delivery_type,
        delivery_time_minutes: formData.delivery_type === 'auto' ? parseInt(formData.delivery_time_minutes) : null,
        stock_count: parseInt(formData.stock_count)
      })
      
      showToast(t('seller.lotCreated'), 'success')
      onSuccess()
      onClose()
    } catch (error: any) {
      console.error('Create lot error:', error)
      showToast(error.response?.data?.message || t('errors.generic'), 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-lg w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-200 p-4 flex items-center justify-between">
          <h2 className="text-xl font-bold">{t('seller.createLot')}</h2>
          <button onClick={onClose} className="text-gray-500 text-2xl">✕</button>
        </div>

        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          {/* Title */}
          <div>
            <label className="block text-sm font-medium mb-1">{t('lot.title')} *</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              placeholder="Например: Аккаунт Dota 2 с 5000 MMR"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              required
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium mb-1">{t('lot.description')}</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Подробное описание товара..."
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            />
          </div>

          {/* Price */}
          <div>
            <label className="block text-sm font-medium mb-1">{t('lot.price')} * (₽)</label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={formData.price}
              onChange={(e) => setFormData({ ...formData, price: e.target.value })}
              placeholder="1000.00"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              required
            />
          </div>

          {/* Game ID (simplified - in real app would be a select) */}
          <div>
            <label className="block text-sm font-medium mb-1">{t('lot.game')} * (ID)</label>
            <input
              type="number"
              value={formData.game_id}
              onChange={(e) => setFormData({ ...formData, game_id: e.target.value })}
              placeholder="1"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              required
            />
            <p className="text-xs text-gray-500 mt-1">Временно: введите ID игры (1-700)</p>
          </div>

          {/* Delivery Type */}
          <div>
            <label className="block text-sm font-medium mb-1">{t('lot.deliveryType')} *</label>
            <select
              value={formData.delivery_type}
              onChange={(e) => setFormData({ ...formData, delivery_type: e.target.value as 'auto' | 'manual' })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            >
              <option value="manual">{t('home.deliveryType.manual')}</option>
              <option value="auto">{t('home.deliveryType.auto')}</option>
            </select>
          </div>

          {/* Delivery Time (only for auto) */}
          {formData.delivery_type === 'auto' && (
            <div>
              <label className="block text-sm font-medium mb-1">{t('product.deliveryTime')} (мин)</label>
              <input
                type="number"
                min="1"
                value={formData.delivery_time_minutes}
                onChange={(e) => setFormData({ ...formData, delivery_time_minutes: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            </div>
          )}

          {/* Stock Count */}
          <div>
            <label className="block text-sm font-medium mb-1">{t('lot.stock')} *</label>
            <input
              type="number"
              min="0"
              value={formData.stock_count}
              onChange={(e) => setFormData({ ...formData, stock_count: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              required
            />
          </div>

          {/* Buttons */}
          <div className="flex gap-2 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 border border-gray-300 py-3 rounded-lg font-semibold"
            >
              {t('common.cancel')}
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 bg-tg-button text-tg-button-text py-3 rounded-lg font-semibold disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <LoadingSpinner size="sm" />
                  <span>{t('app.loading')}</span>
                </>
              ) : (
                t('lot.save')
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
