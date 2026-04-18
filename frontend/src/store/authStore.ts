import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import WebApp from '@twa-dev/sdk'
import api from '../api/client'

interface User {
  id: number
  telegram_id: number
  username: string | null
  first_name: string | null
  balance: number
  referral_code: string
  language_code: string
  is_admin: boolean
  is_seller: boolean
  created_at: string
}

interface AuthState {
  user: User | null
  token: string | null
  isLoading: boolean
  error: string | null
  initAuth: () => Promise<void>
  refreshUser: () => Promise<void>
  updateLanguage: (languageCode: string) => Promise<void>
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isLoading: true,
      error: null,

      initAuth: async () => {
        try {
          set({ isLoading: true, error: null })
          const initData = WebApp.initData
          
          if (!initData) {
            console.error('No initData from Telegram')
            set({ isLoading: false, error: 'No Telegram data' })
            return
          }

          // Authenticate with backend
          const response = await api.post('/auth/telegram', { init_data: initData })
          const { access_token, user } = response.data

          // Save token and user
          set({ token: access_token, user, isLoading: false, error: null })
          
          // Set token for future requests
          api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
        } catch (error: any) {
          console.error('Auth error:', error)
          set({ 
            isLoading: false, 
            error: error.response?.data?.message || 'Authentication failed' 
          })
        }
      },

      refreshUser: async () => {
        try {
          const response = await api.get('/users/me')
          set({ user: response.data })
        } catch (error) {
          console.error('Refresh user error:', error)
        }
      },

      updateLanguage: async (languageCode: string) => {
        try {
          const response = await api.patch('/users/me', { language_code: languageCode })
          set({ user: response.data })
        } catch (error) {
          console.error('Update language error:', error)
          throw error
        }
      },

      logout: () => {
        set({ user: null, token: null, error: null })
        delete api.defaults.headers.common['Authorization']
        localStorage.removeItem('auth-storage')
      }
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ token: state.token, user: state.user })
    }
  )
)
