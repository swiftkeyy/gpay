import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import WebApp from '@twa-dev/sdk'
import { useAuthStore } from '../store/authStore'
import { useUIStore } from '../store/uiStore'
import { useNotificationStore } from '../store/notificationStore'
import BottomNav from '../components/BottomNav'
import api from '../api/client'

interface ReferralStats {
  total_referrals: number
  total_earned: number
  referral_code: string
}

export default function ProfilePage() {
  const { t, i18n } = useTranslation()
  const { user, updateLanguage, logout } = useAuthStore()
  const { showToast, theme, setTheme } = useUIStore()
  const { unreadCount } = useNotificationStore()
  
  const [referralStats, setReferralStats] = useState<ReferralStats | null>(null)
  const [showLanguageModal, setShowLanguageModal] = useState(false)

  useEffect(() => {
    if (user) {
      fetchReferralStats()
    }
  }, [user])

  const fetchReferralStats = async () => {
    try {
      const response = await api.get('/users/me/referrals')
      setReferralStats(response.data)
    } catch (error) {
      console.error('Fetch referral stats error:', error)
    }
  }

  const handleShareReferral = () => {
    if (!referralStats) return
    
    const referralLink = `https://t.me/${WebApp.initDataUnsafe.user?.username}?start=${referralStats.referral_code}`
    const text = t('profile.referralShareText', { link: referralLink })
    
    WebApp.openTelegramLink(`https://t.me/share/url?url=${encodeURIComponent(referralLink)}&text=${encodeURIComponent(text)}`)
  }

  const handleCopyReferralCode = () => {
    if (!referralStats) return
    
    navigator.clipboard.writeText(referralStats.referral_code)
    showToast(t('profile.referralCodeCopied'), 'success')
  }

  const handleChangeLanguage = async (lang: string) => {
    try {
      await updateLanguage(lang)
      i18n.changeLanguage(lang)
      setShowLanguageModal(false)
      showToast(t('profile.languageChanged'), 'success')
    } catch (error) {
      showToast(t('errors.generic'), 'error')
    }
  }

  const handleToggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light'
    setTheme(newTheme)
    showToast(t('profile.themeChanged'), 'success')
  }

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center pb-20">
        <div className="text-center">
          <p className="mb-4">{t('profile.notAuthenticated')}</p>
        </div>
        <BottomNav />
      </div>
    )
  }

  return (
    <div className="min-h-screen pb-20">
      {/* Header */}
      <div className="bg-gradient-to-br from-tg-button to-blue-600 text-white p-6">
        <div className="flex items-center gap-4 mb-4">
          <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center text-3xl">
            👤
          </div>
          <div className="flex-1">
            <div className="text-xl font-bold">
              {user.first_name || user.username || t('profile.user')}
            </div>
            <div className="text-sm opacity-90">
              @{user.username || `user${user.telegram_id}`}
            </div>
          </div>
        </div>

        {/* Balance Card */}
        <div className="bg-white bg-opacity-20 backdrop-blur rounded-lg p-4">
          <div className="text-sm opacity-90 mb-1">{t('profile.balance')}</div>
          <div className="text-3xl font-bold">
            {typeof user.balance === 'number' ? user.balance.toFixed(2) : '0.00'} ₽
          </div>
          <button className="mt-2 text-sm underline opacity-90">
            {t('profile.topUp')}
          </button>
        </div>
      </div>

      <div className="p-4">
        {/* Referral Program */}
        {referralStats && (
          <div className="border border-gray-200 rounded-lg p-4 mb-4 bg-gradient-to-br from-yellow-50 to-orange-50">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-2xl">🎁</span>
              <h2 className="font-semibold text-lg">{t('profile.referralProgram')}</h2>
            </div>
            
            <div className="grid grid-cols-2 gap-3 mb-3">
              <div className="bg-white rounded-lg p-3">
                <div className="text-sm text-gray-600">{t('profile.referrals')}</div>
                <div className="text-2xl font-bold">{referralStats.total_referrals}</div>
              </div>
              <div className="bg-white rounded-lg p-3">
                <div className="text-sm text-gray-600">{t('profile.earned')}</div>
                <div className="text-2xl font-bold">
                  {typeof referralStats.total_earned === 'number' ? referralStats.total_earned.toFixed(0) : '0'} ₽
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg p-3 mb-3">
              <div className="text-sm text-gray-600 mb-2">{t('profile.yourCode')}</div>
              <div className="flex items-center gap-2">
                <code className="flex-1 bg-gray-100 px-3 py-2 rounded font-mono text-lg">
                  {referralStats.referral_code}
                </code>
                <button
                  onClick={handleCopyReferralCode}
                  className="px-4 py-2 bg-gray-200 rounded font-medium"
                >
                  📋
                </button>
              </div>
            </div>

            <button
              onClick={handleShareReferral}
              className="w-full bg-tg-button text-tg-button-text py-3 rounded-lg font-semibold"
            >
              {t('profile.shareReferral')}
            </button>
          </div>
        )}

        {/* Quick Actions */}
        <div className="space-y-2 mb-6">
          <Link
            to="/orders"
            className="flex items-center justify-between border border-gray-200 rounded-lg p-4 hover:bg-gray-50 bg-white"
          >
            <div className="flex items-center gap-3">
              <span className="text-2xl">📦</span>
              <span className="font-medium">{t('nav.orders')}</span>
            </div>
            <span className="text-gray-400">›</span>
          </Link>

          {user.is_seller && (
            <Link
              to="/seller"
              className="flex items-center justify-between border border-gray-200 rounded-lg p-4 hover:bg-gray-50 bg-white"
            >
              <div className="flex items-center gap-3">
                <span className="text-2xl">💼</span>
                <span className="font-medium">{t('nav.seller')}</span>
              </div>
              <span className="text-gray-400">›</span>
            </Link>
          )}

          {!user.is_seller && (
            <button className="w-full flex items-center justify-between border border-gray-200 rounded-lg p-4 hover:bg-gray-50 bg-white">
              <div className="flex items-center gap-3">
                <span className="text-2xl">🏪</span>
                <span className="font-medium">{t('profile.becomeSeller')}</span>
              </div>
              <span className="text-gray-400">›</span>
            </button>
          )}

          {user.is_admin && (
            <Link
              to="/admin"
              className="flex items-center justify-between border border-gray-200 rounded-lg p-4 hover:bg-gray-50 bg-white"
            >
              <div className="flex items-center gap-3">
                <span className="text-2xl">⚙️</span>
                <span className="font-medium">{t('nav.admin')}</span>
              </div>
              <span className="text-gray-400">›</span>
            </Link>
          )}
        </div>

        {/* Settings */}
        <div className="border-t border-gray-200 pt-4">
          <h2 className="font-semibold mb-3">{t('profile.settings')}</h2>
          
          <div className="space-y-2">
            <button
              onClick={() => setShowLanguageModal(true)}
              className="w-full flex items-center justify-between border border-gray-200 rounded-lg p-4 hover:bg-gray-50 bg-white"
            >
              <div className="flex items-center gap-3">
                <span className="text-2xl">🌐</span>
                <div className="text-left">
                  <div className="font-medium">{t('profile.language')}</div>
                  <div className="text-sm text-gray-500">
                    {i18n.language === 'ru' ? 'Русский' : 'English'}
                  </div>
                </div>
              </div>
              <span className="text-gray-400">›</span>
            </button>

            <button
              onClick={handleToggleTheme}
              className="w-full flex items-center justify-between border border-gray-200 rounded-lg p-4 hover:bg-gray-50 bg-white"
            >
              <div className="flex items-center gap-3">
                <span className="text-2xl">{theme === 'light' ? '☀️' : '🌙'}</span>
                <div className="text-left">
                  <div className="font-medium">{t('profile.theme')}</div>
                  <div className="text-sm text-gray-500">
                    {theme === 'light' ? t('profile.lightTheme') : t('profile.darkTheme')}
                  </div>
                </div>
              </div>
              <span className="text-gray-400">›</span>
            </button>

            <Link
              to="/notifications"
              className="flex items-center justify-between border border-gray-200 rounded-lg p-4 hover:bg-gray-50 bg-white relative"
            >
              <div className="flex items-center gap-3">
                <span className="text-2xl">🔔</span>
                <span className="font-medium">{t('profile.notifications')}</span>
              </div>
              <div className="flex items-center gap-2">
                {unreadCount > 0 && (
                  <span className="bg-red-500 text-white text-xs rounded-full w-6 h-6 flex items-center justify-center">
                    {unreadCount}
                  </span>
                )}
                <span className="text-gray-400">›</span>
              </div>
            </Link>

            <button className="w-full flex items-center justify-between border border-gray-200 rounded-lg p-4 hover:bg-gray-50 bg-white">
              <div className="flex items-center gap-3">
                <span className="text-2xl">❓</span>
                <span className="font-medium">{t('profile.help')}</span>
              </div>
              <span className="text-gray-400">›</span>
            </button>

            <button
              onClick={logout}
              className="w-full flex items-center justify-between border border-red-200 rounded-lg p-4 hover:bg-red-50 bg-white text-red-600"
            >
              <div className="flex items-center gap-3">
                <span className="text-2xl">🚪</span>
                <span className="font-medium">{t('profile.logout')}</span>
              </div>
            </button>
          </div>
        </div>
      </div>

      {/* Language Modal */}
      {showLanguageModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-6 max-w-sm w-full">
            <h3 className="text-xl font-bold mb-4">{t('profile.selectLanguage')}</h3>
            <div className="space-y-2">
              <button
                onClick={() => handleChangeLanguage('ru')}
                className={`w-full p-4 border-2 rounded-lg text-left ${
                  i18n.language === 'ru' ? 'border-tg-button bg-blue-50' : 'border-gray-200'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium">🇷🇺 Русский</span>
                  {i18n.language === 'ru' && <span className="text-tg-button">✓</span>}
                </div>
              </button>
              <button
                onClick={() => handleChangeLanguage('en')}
                className={`w-full p-4 border-2 rounded-lg text-left ${
                  i18n.language === 'en' ? 'border-tg-button bg-blue-50' : 'border-gray-200'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium">🇬🇧 English</span>
                  {i18n.language === 'en' && <span className="text-tg-button">✓</span>}
                </div>
              </button>
            </div>
            <button
              onClick={() => setShowLanguageModal(false)}
              className="w-full mt-4 py-3 border border-gray-300 rounded-lg font-medium"
            >
              {t('common.cancel')}
            </button>
          </div>
        </div>
      )}

      <BottomNav />
    </div>
  )
}
