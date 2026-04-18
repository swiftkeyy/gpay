import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface Toast {
  id: string
  message: string
  type: 'success' | 'error' | 'info' | 'warning'
  duration?: number
}

interface UIState {
  theme: 'light' | 'dark'
  toasts: Toast[]
  toast: Toast | null
  isOnline: boolean
  showToast: (message: string, type?: Toast['type'], duration?: number) => void
  hideToast: () => void
  removeToast: (id: string) => void
  setTheme: (theme: 'light' | 'dark') => void
  setOnline: (isOnline: boolean) => void
}

export const useUIStore = create<UIState>()(
  persist(
    (set, get) => ({
      theme: 'light',
      toasts: [],
      toast: null,
      isOnline: navigator.onLine,

      showToast: (message: string, type: Toast['type'] = 'info', duration: number = 3000) => {
        const id = `toast-${Date.now()}-${Math.random()}`
        const toast: Toast = { id, message, type, duration }
        
        set({ toast, toasts: [...get().toasts, toast] })

        if (duration > 0) {
          setTimeout(() => {
            get().removeToast(id)
          }, duration)
        }
      },

      hideToast: () => {
        set({ toast: null })
      },

      removeToast: (id: string) => {
        set(state => ({ 
          toasts: state.toasts.filter(t => t.id !== id),
          toast: state.toast?.id === id ? null : state.toast
        }))
      },

      setTheme: (theme: 'light' | 'dark') => {
        set({ theme })
        document.documentElement.classList.toggle('dark', theme === 'dark')
      },

      setOnline: (isOnline: boolean) => {
        set({ isOnline })
      }
    }),
    {
      name: 'ui-storage',
      partialize: (state) => ({ theme: state.theme })
    }
  )
)

// Listen to online/offline events
if (typeof window !== 'undefined') {
  window.addEventListener('online', () => useUIStore.getState().setOnline(true))
  window.addEventListener('offline', () => useUIStore.getState().setOnline(false))
}
