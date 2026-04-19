import { create } from 'zustand'
import api from '../api/client'

interface Notification {
  id: number
  title: string
  message: string
  notification_type: string
  reference_type: string | null
  reference_id: number | null
  is_read: boolean
  created_at: string
}

interface NotificationState {
  notifications: Notification[]
  unreadCount: number
  isLoading: boolean
  ws: WebSocket | null
  fetchNotifications: () => Promise<void>
  markAsRead: (id: number) => Promise<void>
  markAllAsRead: () => Promise<void>
  connectWebSocket: (token: string) => void
  disconnectWebSocket: () => void
}

export const useNotificationStore = create<NotificationState>((set, get) => ({
  notifications: [],
  unreadCount: 0,
  isLoading: false,
  ws: null,

  fetchNotifications: async () => {
    try {
      set({ isLoading: true })
      const [notificationsRes, countRes] = await Promise.all([
        api.get('/notifications', { params: { limit: 20 } }),
        api.get('/notifications/unread-count')
      ])
      set({ 
        notifications: notificationsRes.data.items,
        unreadCount: countRes.data.count,
        isLoading: false
      })
    } catch (error) {
      console.error('Fetch notifications error:', error)
      set({ isLoading: false })
    }
  },

  markAsRead: async (id: number) => {
    try {
      await api.patch(`/notifications/${id}/read`)
      set(state => ({
        notifications: state.notifications.map(n => 
          n.id === id ? { ...n, is_read: true } : n
        ),
        unreadCount: Math.max(0, state.unreadCount - 1)
      }))
    } catch (error) {
      console.error('Mark as read error:', error)
    }
  },

  markAllAsRead: async () => {
    try {
      await api.post('/notifications/read-all')
      set(state => ({
        notifications: state.notifications.map(n => ({ ...n, is_read: true })),
        unreadCount: 0
      }))
    } catch (error) {
      console.error('Mark all as read error:', error)
    }
  },

  connectWebSocket: (token: string) => {
    const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
    // Convert http/https to ws/wss
    const WS_URL = API_URL.replace(/^http/, 'ws')
    const ws = new WebSocket(`${WS_URL}/ws/notifications?token=${token}`)

    ws.onopen = () => {
      console.log('Notification WebSocket connected')
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'notification') {
        set(state => ({
          notifications: [data.data, ...state.notifications],
          unreadCount: state.unreadCount + 1
        }))
      }
    }

    ws.onerror = (error) => {
      console.error('Notification WebSocket error:', error)
    }

    ws.onclose = () => {
      console.log('Notification WebSocket closed')
      // Attempt reconnection after 5 seconds
      setTimeout(() => {
        if (get().ws === ws) {
          get().connectWebSocket(token)
        }
      }, 5000)
    }

    set({ ws })
  },

  disconnectWebSocket: () => {
    const { ws } = get()
    if (ws) {
      ws.close()
      set({ ws: null })
    }
  }
}))
