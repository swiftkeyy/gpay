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
      <div className="relative z-10 bg-gradient-to-br from-neon-red via-neon-purple to-neon-cyan p-6 border-b-2 border-neon-red/30 shadow-neon-red">
        <div className="flex items-center gap-4 mb-4">
          <div className="w-20 h-20 bg-black/60 backdrop-blur-sm border-2 border-neon-gold rounded-full flex items-center justify-center text-4xl animate-float shadow-neon-gold">
            👤
          </div>
          <div className="flex-1">
            <div className="text-2xl font-black font-gaming text-white drop-shadow-[0_0_10px_rgba(255,255,255,0.8)]">
              {user.first_name || user.username || t('profile.user')}
            </div>
            <div className="text-sm font-gaming text-neon-cyan">
              @{user.username || `user${user.telegram_id}`}
            </div>
          </div>
        </div>

        {/* Balance Card */}
        <div className="bg-black/60 backdrop-blur-xl border-2 border-neon-gold/50 rounded-xl p-4 hover:border-neon-gold hover:shadow-neon-gold transition-all duration-300">
          <div className="text-sm font-gaming text-neon-cyan mb-1">{t('profile.balance')}</div>
          <div className="text-4xl font-black font-gaming text-neon-gold drop-shadow-[0_0_15px_rgba(255,215,0,0.8)]">
            {typeof user.balance === 'number' ? user.balance.toFixed(2) : '0.00'} ₽
          </div>
          <button className="mt-2 text-sm font-gaming text-white underline hover:text-neon-cyan transition-colors duration-200">
            💎 {t('profile.topUp')}
          </button>
        </div>
      </div>

      <div className="p-4 relative z-10">
        {/* Referral Program */}
        {referralStats && (
          <div className="relative overflow-hidden rounded-xl bg-black/40 backdrop-blur-sm border-2 border-neon-gold/30 p-4 mb-4 hover:border-neon-gold hover:shadow-neon-gold transition-all duration-300">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-3xl animate-float">🎁</span>
              <h2 className="font-gaming font-black text-neon-gold text-xl">{t('profile.referralProgram')}</h2>
            </div>
            
            <div className="grid grid-cols-2 gap-3 mb-3">
              <div className="bg-black/60 backdrop-blur-sm border-2 border-neon-cyan/30 rounded-lg p-3 hover:border-neon-cyan hover:shadow-neon-cyan transition-all duration-200">
                <div className="text-sm text-gray-400 font-gaming">{t('profile.referrals')}</div>
                <div className="text-3xl font-black font-gaming text-neon-cyan">{referralStats.total_referrals}</div>
              </div>
              <div className="bg-black/60 backdrop-blur-sm border-2 border-neon-gold/30 rounded-lg p-3 hover:border-neon-gold hover:shadow-neon-gold transition-all duration-200">
                <div className="text-sm text-gray-400 font-gaming">{t('profile.earned')}</div>
                <div className="text-3xl font-black font-gaming text-neon-gold">
                  {typeof referralStats.total_earned === 'number' ? referralStats.total_earned.toFixed(0) : '0'} ₽
                </div>
              </div>
            </div>

            <div className="bg-black/60 backdrop-blur-sm border-2 border-neon-purple/30 rounded-lg p-3 mb-3 hover:border-neon-purple transition-all duration-200">
              <div className="text-sm text-gray-400 font-gaming mb-2">{t('profile.yourCode')}</div>
              <div className="flex items-center gap-2">
                <code className="flex-1 bg-black/80 border border-neon-red/30 px-3 py-2 rounded font-mono text-lg text-neon-red font-bold">
                  {referralStats.referral_code}
                </code>
                <button
                  onClick={handleCopyReferralCode}
                  className="px-4 py-2 bg-black/80 border-2 border-neon-cyan/50 rounded font-gaming font-bold text-neon-cyan hover:border-neon-cyan hover:shadow-neon-cyan hover:scale-110 transition-all duration-200"
                >
                  📋
                </button>
              </div>
            </div>

            <button
              onClick={handleShareReferral}
              className="w-full bg-gradient-to-r from-neon-gold to-yellow-500 text-black py-3 rounded-xl font-gaming font-black tracking-wide shadow-neon-gold hover:scale-105 transition-all duration-200"
            >
              {t('profile.shareReferral')}
            </button>
          </div>
        )}

        {/* Quick Actions */}
        <div className="space-y-3 mb-6">
          <Link
            to="/orders"
            className="flex items-center justify-between rounded-xl bg-black/40 backdrop-blur-sm border-2 border-neon-red/30 p-4 hover:border-neon-red hover:shadow-neon-red hover:scale-[1.02] transition-all duration-300"
          >
            <div className="flex items-center gap-3">
              <span className="text-3xl">📦</span>
              <span className="font-gaming font-bold text-white">{t('nav.orders')}</span>
            </div>
            <span className="text-neon-red text-2xl">›</span>
          </Link>

          {user.is_seller && (
            <Link
              to="/seller"
              className="flex items-center justify-between rounded-xl bg-black/40 backdrop-blur-sm border-2 border-neon-gold/30 p-4 hover:border-neon-gold hover:shadow-neon-gold hover:scale-[1.02] transition-all duration-300"
            >
              <div className="flex items-center gap-3">
                <span className="text-3xl">💼</span>
                <span className="font-gaming font-bold text-white">{t('nav.seller')}</span>
              </div>
              <span className="text-neon-gold text-2xl">›</span>
            </Link>
          )}

          {!user.is_seller && (
            <button className="w-full flex items-center justify-between rounded-xl bg-black/40 backdrop-blur-sm border-2 border-neon-purple/30 p-4 hover:border-neon-purple hover:shadow-neon-purple hover:scale-[1.02] transition-all duration-300">
              <div className="flex items-center gap-3">
                <span className="text-3xl">🏪</span>
                <span className="font-gaming font-bold text-white">{t('profile.becomeSeller')}</span>
              </div>
              <span className="text-neon-purple text-2xl">›</span>
            </button>
          )}

          {user.is_admin && (
            <Link
              to="/admin"
              className="flex items-center justify-between rounded-xl bg-black/40 backdrop-blur-sm border-2 border-neon-cyan/30 p-4 hover:border-neon-cyan hover:shadow-neon-cyan hover:scale-[1.02] transition-all duration-300"
            >
              <div className="flex items-center gap-3">
                <span className="text-3xl">⚙️</span>
                <span className="font-gaming font-bold text-white">{t('nav.admin')}</span>
              </div>
              <span className="text-neon-cyan text-2xl">›</span>
            </Link>
          )}
        </div>

        {/* Settings */}
        <div className="border-t-2 border-neon-red/30 pt-4">
          <h2 className="font-gaming font-black text-neon-cyan mb-4 text-xl">⚙️ {t('profile.settings')}</h2>
          
          <div className="space-y-3">
            <button
              onClick={() => setShowLanguageModal(true)}
              className="w-full flex items-center justify-between rounded-xl bg-black/40 backdrop-blur-sm border-2 border-neon-purple/30 p-4 hover:border-neon-purple hover:shadow-neon-purple hover:scale-[1.02] transition-all duration-300"
            >
              <div className="flex items-center gap-3">
                <span className="text-3xl">🌐</span>
                <div className="text-left">
                  <div className="font-gaming font-bold text-white">{t('profile.language')}</div>
                  <div className="text-sm text-gray-400 font-gaming">
                    {i18n.language === 'ru' ? 'Русский' : 'English'}
                  </div>
                </div>
              </div>
              <span className="text-neon-purple text-2xl">›</span>
            </button>

            <button
              onClick={handleToggleTheme}
              className="w-full flex items-center justify-between rounded-xl bg-black/40 backdrop-blur-sm border-2 border-neon-cyan/30 p-4 hover:border-neon-cyan hover:shadow-neon-cyan hover:scale-[1.02] transition-all duration-300"
            >
              <div className="flex items-center gap-3">
                <span className="text-3xl">{theme === 'light' ? '☀️' : '🌙'}</span>
                <div className="text-left">
                  <div className="font-gaming font-bold text-white">{t('profile.theme')}</div>
                  <div className="text-sm text-gray-400 font-gaming">
                    {theme === 'light' ? t('profile.lightTheme') : t('profile.darkTheme')}
                  </div>
                </div>
              </div>
              <span className="text-neon-cyan text-2xl">›</span>
            </button>

            <Link
              to="/notifications"
              className="flex items-center justify-between rounded-xl bg-black/40 backdrop-blur-sm border-2 border-neon-gold/30 p-4 hover:border-neon-gold hover:shadow-neon-gold hover:scale-[1.02] transition-all duration-300 relative"
            >
              <div className="flex items-center gap-3">
                <span className="text-3xl">🔔</span>
                <span className="font-gaming font-bold text-white">{t('profile.notifications')}</span>
              </div>
              <div className="flex items-center gap-2">
                {unreadCount > 0 && (
                  <span className="bg-gradient-to-r from-neon-red to-neon-purple text-white text-xs rounded-full w-7 h-7 flex items-center justify-center font-gaming font-black animate-pulse-glow">
                    {unreadCount}
                  </span>
                )}
                <span className="text-neon-gold text-2xl">›</span>
              </div>
            </Link>

            <button className="w-full flex items-center justify-between rounded-xl bg-black/40 backdrop-blur-sm border-2 border-neon-cyan/30 p-4 hover:border-neon-cyan hover:shadow-neon-cyan hover:scale-[1.02] transition-all duration-300">
              <div className="flex items-center gap-3">
                <span className="text-3xl">❓</span>
                <span className="font-gaming font-bold text-white">{t('profile.help')}</span>
              </div>
              <span className="text-neon-cyan text-2xl">›</span>
            </button>

            <button
              onClick={logout}
              className="w-full flex items-center justify-between rounded-xl bg-black/40 backdrop-blur-sm border-2 border-neon-red/50 p-4 hover:border-neon-red hover:shadow-neon-red hover:scale-[1.02] transition-all duration-300 text-neon-red"
            >
              <div className="flex items-center gap-3">
                <span className="text-3xl">🚪</span>
                <span className="font-gaming font-bold">{t('profile.logout')}</span>
              </div>
            </button>
          </div>
        </div>
      </div>

      {/* Language Modal */}
      {showLanguageModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in">
          <div className="bg-cyber-dark border-2 border-neon-purple rounded-xl p-6 max-w-sm w-full shadow-neon-purple">
            <h3 className="text-2xl font-black font-gaming text-neon-purple mb-4">{t('profile.selectLanguage')}</h3>
            <div className="space-y-3">
              <button
                onClick={() => handleChangeLanguage('ru')}
                className={`w-full p-4 border-2 rounded-xl text-left font-gaming font-bold transition-all duration-200 hover:scale-105 ${
                  i18n.language === 'ru' ? 'border-neon-red bg-neon-red/20 text-neon-red shadow-neon-red' : 'border-gray-700 text-gray-400 hover:border-neon-red/50'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span>🇷🇺 Русский</span>
                  {i18n.language === 'ru' && <span className="text-neon-red text-xl">✓</span>}
                </div>
              </button>
              <button
                onClick={() => handleChangeLanguage('en')}
                className={`w-full p-4 border-2 rounded-xl text-left font-gaming font-bold transition-all duration-200 hover:scale-105 ${
                  i18n.language === 'en' ? 'border-neon-red bg-neon-red/20 text-neon-red shadow-neon-red' : 'border-gray-700 text-gray-400 hover:border-neon-red/50'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span>🇬🇧 English</span>
                  {i18n.language === 'en' && <span className="text-neon-red text-xl">✓</span>}
                </div>
              </button>
            </div>
            <button
              onClick={() => setShowLanguageModal(false)}
              className="w-full mt-4 py-3 border-2 border-gray-700 rounded-xl font-gaming font-bold text-white hover:border-neon-cyan hover:text-neon-cyan hover:scale-105 transition-all duration-200"
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
