import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import api from '../api/client'
import { useUIStore } from '../store/uiStore'
import LoadingSpinner from './LoadingSpinner'

interface WithdrawModalProps {
  availableBalance: number
  onClose: () => void
  onSuccess: () => void
}

export default function WithdrawModal({ availableBalance, onClose, onSuccess }: WithdrawModalProps) {
  const { t } = useTranslation()
  const { showToast } = useUIStore()
  
  const [submitting, setSubmitting] = useState(false)
  const [formData, setFormData] = useState({
    amount: '',
    method: 'card' as 'card' | 'qiwi' | 'yoomoney' | 'crypto',
    details: ''
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    const amount = parseFloat(formData.amount)
    
    if (!amount || amount <= 0) {
      showToast(t('errors.invalidInput'), 'error')
      return
    }
    
    if (amount > availableBalance) {
      showToast(t('errors.insufficientBalance'), 'error')
      return
    }
    
    if (!formData.details.trim()) {
      showToast(t('withdraw.enterDetails'), 'error')
      return
    }

    try {
      setSubmitting(true)
      await api.post('/sellers/me/withdrawals', {
        amount,
        method: formData.method,
        details: formData.details.trim()
      })
      
      showToast(t('withdraw.requestSubmitted'), 'success')
      onSuccess()
      onClose()
    } catch (error: any) {
      console.error('Withdraw error:', error)
      showToast(error.response?.data?.detail || t('errors.generic'), 'error')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold">{t('withdraw.title')}</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl"
          >
            ×
          </button>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
          <div className="text-sm text-blue-800">
            {t('withdraw.availableBalance')}
          </div>
          <div className="text-2xl font-bold text-blue-900">
            {availableBalance.toFixed(2)} ₽
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">
              {t('withdraw.amount')} (₽) *
            </label>
            <input
              type="number"
              value={formData.amount}
              onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
              min="0"
              max={availableBalance}
              step="0.01"
              placeholder="0.00"
              required
            />
            <div className="text-xs text-gray-500 mt-1">
              {t('withdraw.minAmount')}: 100 ₽
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              {t('withdraw.method')} *
            </label>
            <select
              value={formData.method}
              onChange={(e) => setFormData({ ...formData, method: e.target.value as any })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
              required
            >
              <option value="card">{t('withdraw.methods.card')}</option>
              <option value="qiwi">{t('withdraw.methods.qiwi')}</option>
              <option value="yoomoney">{t('withdraw.methods.yoomoney')}</option>
              <option value="crypto">{t('withdraw.methods.crypto')}</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              {t('withdraw.details')} *
            </label>
            <textarea
              value={formData.details}
              onChange={(e) => setFormData({ ...formData, details: e.target.value })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
              rows={3}
              placeholder={
                formData.method === 'card' ? '1234 5678 9012 3456' :
                formData.method === 'qiwi' ? '+79001234567' :
                formData.method === 'yoomoney' ? '410012345678901' :
                'TQn4...xyz'
              }
              required
            />
            <div className="text-xs text-gray-500 mt-1">
              {formData.method === 'card' && t('withdraw.cardHint')}
              {formData.method === 'qiwi' && t('withdraw.qiwiHint')}
              {formData.method === 'yoomoney' && t('withdraw.yoomoneyHint')}
              {formData.method === 'crypto' && t('withdraw.cryptoHint')}
            </div>
          </div>

          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 text-sm text-yellow-800">
            ⚠️ {t('withdraw.processingTime')}
          </div>

          <div className="flex gap-3 pt-2">
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
              {submitting ? <LoadingSpinner size="sm" /> : t('withdraw.submit')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
