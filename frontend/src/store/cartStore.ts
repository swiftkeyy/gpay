import { create } from 'zustand'
import api from '../api/client'

interface CartItem {
  id: number
  lot_id: number
  lot_title: string
  lot_price: number
  quantity: number
  lot_image?: string
}

interface CartState {
  items: CartItem[]
  total: number
  isLoading: boolean
  fetchCart: () => Promise<void>
  addItem: (lotId: number, quantity: number) => Promise<void>
  updateQuantity: (itemId: number, quantity: number) => Promise<void>
  removeItem: (itemId: number) => Promise<void>
  clearCart: () => Promise<void>
}

export const useCartStore = create<CartState>((set, get) => ({
  items: [],
  total: 0,
  isLoading: false,

  fetchCart: async () => {
    try {
      set({ isLoading: true })
      const response = await api.get('/cart')
      set({ 
        items: response.data.items,
        total: response.data.total,
        isLoading: false
      })
    } catch (error) {
      console.error('Fetch cart error:', error)
      set({ isLoading: false })
    }
  },

  addItem: async (lotId: number, quantity: number) => {
    try {
      await api.post('/cart/items', { lot_id: lotId, quantity })
      await get().fetchCart()
    } catch (error) {
      console.error('Add to cart error:', error)
      throw error
    }
  },

  updateQuantity: async (itemId: number, quantity: number) => {
    try {
      await api.patch(`/cart/items/${itemId}`, { quantity })
      await get().fetchCart()
    } catch (error) {
      console.error('Update quantity error:', error)
      throw error
    }
  },

  removeItem: async (itemId: number) => {
    try {
      await api.delete(`/cart/items/${itemId}`)
      await get().fetchCart()
    } catch (error) {
      console.error('Remove item error:', error)
      throw error
    }
  },

  clearCart: async () => {
    try {
      await api.delete('/cart')
      set({ items: [], total: 0 })
    } catch (error) {
      console.error('Clear cart error:', error)
      throw error
    }
  }
}))
