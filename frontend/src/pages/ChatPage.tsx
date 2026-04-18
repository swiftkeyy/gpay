import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '../store/authStore'
import { useUIStore } from '../store/uiStore'
import api from '../api/client'

interface Message {
  id?: number
  sender_id: number
  sender_name?: string
  content: string
  message_type: 'text' | 'image' | 'system'
  is_read: boolean
  created_at: string
}

interface Deal {
  id: number
  order_id: number
  buyer_id: number
  seller_id: number
  status: string
  lot_title: string
  amount: number
}

export default function ChatPage() {
  const { t } = useTranslation()
  const { dealId } = useParams()
  const navigate = useNavigate()
  const { user, token } = useAuthStore()
  const { showToast } = useUIStore()
  
  const [messages, setMessages] = useState<Message[]>([])
  const [deal, setDeal] = useState<Deal | null>(null)
  const [input, setInput] = useState('')
  const [ws, setWs] = useState<WebSocket | null>(null)
  const [isTyping, setIsTyping] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [reconnectAttempts, setReconnectAttempts] = useState(0)
  const [messageQueue, setMessageQueue] = useState<string[]>([])
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const typingTimeoutRef = useRef<NodeJS.Timeout>()
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>()
  const wsRef = useRef<WebSocket | null>(null)

  const maxReconnectAttempts = 5

  // Fetch deal info and message history
  useEffect(() => {
    if (!dealId) return
    
    const fetchDealAndMessages = async () => {
      try {
        const [dealRes, messagesRes] = await Promise.all([
          api.get(`/deals/${dealId}`),
          api.get(`/deals/${dealId}/messages`)
        ])
        setDeal(dealRes.data)
        setMessages(messagesRes.data.items || [])
      } catch (error) {
        console.error('Fetch deal error:', error)
        showToast(t('errors.notFound'), 'error')
      }
    }

    fetchDealAndMessages()
  }, [dealId, showToast, t])

  // WebSocket connection with reconnection logic
  useEffect(() => {
    if (!token || !dealId) return

    const connect = () => {
      const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/api/v1'
      const websocket = new WebSocket(`${WS_URL}/ws/chat/${dealId}?token=${token}`)

      websocket.onopen = () => {
        console.log('WebSocket connected')
        setIsConnected(true)
        setReconnectAttempts(0)
        
        // Send queued messages
        if (messageQueue.length > 0) {
          messageQueue.forEach(msg => {
            websocket.send(msg)
          })
          setMessageQueue([])
        }
      }

      websocket.onmessage = (event) => {
        const data = JSON.parse(event.data)
        
        if (data.type === 'message') {
          setMessages(prev => [...prev, data])
          
          // Mark as read if from other user
          if (data.sender_id !== user?.id) {
            markAsRead()
          }
        } else if (data.type === 'typing') {
          if (data.sender_id !== user?.id) {
            setIsTyping(true)
            if (typingTimeoutRef.current) {
              clearTimeout(typingTimeoutRef.current)
            }
            typingTimeoutRef.current = setTimeout(() => {
              setIsTyping(false)
            }, 3000)
          }
        } else if (data.type === 'read') {
          // Update read status for messages
          setMessages(prev => prev.map(msg => 
            msg.sender_id === user?.id ? { ...msg, is_read: true } : msg
          ))
        }
      }

      websocket.onerror = (error) => {
        console.error('WebSocket error:', error)
        setIsConnected(false)
      }

      websocket.onclose = () => {
        console.log('WebSocket closed')
        setIsConnected(false)
        wsRef.current = null
        
        // Attempt reconnection with exponential backoff
        if (reconnectAttempts < maxReconnectAttempts) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000)
          console.log(`Reconnecting in ${delay}ms...`)
          
          reconnectTimeoutRef.current = setTimeout(() => {
            setReconnectAttempts(prev => prev + 1)
            connect()
          }, delay)
        } else {
          showToast(t('chat.connectionLost'), 'error')
        }
      }

      wsRef.current = websocket
      setWs(websocket)
    }

    connect()

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current)
      }
    }
  }, [dealId, token, reconnectAttempts, user?.id, showToast, t])

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = () => {
    if (!ws || !input.trim()) return

    const message = JSON.stringify({
      type: 'text',
      content: input.trim()
    })

    if (isConnected) {
      ws.send(message)
    } else {
      // Queue message if disconnected
      setMessageQueue(prev => [...prev, message])
      showToast(t('chat.messagQueued'), 'info')
    }

    setInput('')
  }

  const handleTyping = () => {
    if (ws && isConnected) {
      ws.send(JSON.stringify({ type: 'typing' }))
    }
  }

  const markAsRead = async () => {
    if (ws && isConnected) {
      ws.send(JSON.stringify({ type: 'read' }))
    }
  }

  const handleConfirmDelivery = async () => {
    try {
      await api.post(`/deals/${dealId}/confirm`)
      showToast(t('chat.deliveryConfirmed'), 'success')
      // Refresh deal
      const dealRes = await api.get(`/deals/${dealId}`)
      setDeal(dealRes.data)
    } catch (error) {
      showToast(t('errors.generic'), 'error')
    }
  }

  const handleOpenDispute = async () => {
    try {
      await api.post(`/deals/${dealId}/dispute`, {
        reason: 'Проблема с доставкой'
      })
      showToast(t('chat.disputeOpened'), 'success')
      // Refresh deal
      const dealRes = await api.get(`/deals/${dealId}`)
      setDeal(dealRes.data)
    } catch (error) {
      showToast(t('errors.generic'), 'error')
    }
  }

  const isBuyer = user?.id === deal?.buyer_id

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <div className="bg-tg-bg border-b border-gray-200 p-4">
        <div className="flex items-center gap-3 mb-2">
          <button onClick={() => navigate(-1)} className="text-tg-link text-xl">
            ←
          </button>
          <div className="flex-1">
            <h1 className="font-semibold">💬 {t('chat.title')}</h1>
            {!isConnected && (
              <div className="text-xs text-red-500">{t('chat.reconnecting')}</div>
            )}
            {isTyping && (
              <div className="text-xs text-gray-500">{t('chat.typing')}</div>
            )}
          </div>
        </div>

        {/* Deal Info */}
        {deal && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm">
            <div className="font-semibold mb-1">{deal.lot_title}</div>
            <div className="flex justify-between text-gray-600">
              <span>{t('order.orderNumber', { number: deal.order_id })}</span>
              <span className="font-bold">{deal.amount} ₽</span>
            </div>
            <div className="mt-1">
              <span className={`px-2 py-1 rounded text-xs ${
                deal.status === 'completed' ? 'bg-green-100 text-green-800' :
                deal.status === 'dispute' ? 'bg-red-100 text-red-800' :
                'bg-yellow-100 text-yellow-800'
              }`}>
                {t(`order.status.${deal.status}`)}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50">
        {messages.map((msg, idx) => {
          const isOwn = msg.sender_id === user?.id
          
          if (msg.message_type === 'system') {
            return (
              <div key={idx} className="text-center">
                <span className="bg-gray-200 text-gray-600 px-3 py-1 rounded-full text-xs">
                  {msg.content}
                </span>
              </div>
            )
          }

          return (
            <div
              key={idx}
              className={`flex ${isOwn ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`max-w-[70%] ${isOwn ? 'order-2' : 'order-1'}`}>
                {!isOwn && msg.sender_name && (
                  <div className="text-xs text-gray-500 mb-1 px-1">
                    {msg.sender_name}
                  </div>
                )}
                <div className={`p-3 rounded-lg ${
                  isOwn
                    ? 'bg-tg-button text-tg-button-text rounded-br-none'
                    : 'bg-white border border-gray-200 rounded-bl-none'
                }`}>
                  <div className="break-words">{msg.content}</div>
                  <div className={`text-xs mt-1 flex items-center gap-1 ${
                    isOwn ? 'text-tg-button-text opacity-75' : 'text-gray-400'
                  }`}>
                    <span>{new Date(msg.created_at).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })}</span>
                    {isOwn && (
                      <span>{msg.is_read ? '✓✓' : '✓'}</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )
        })}
        <div ref={messagesEndRef} />
      </div>

      {/* Quick Actions */}
      {deal && deal.status === 'in_progress' && isBuyer && (
        <div className="border-t border-gray-200 p-3 bg-white">
          <div className="flex gap-2">
            <button
              onClick={handleConfirmDelivery}
              className="flex-1 bg-green-500 text-white py-2 rounded-lg text-sm font-semibold"
            >
              ✓ {t('chat.confirmDelivery')}
            </button>
            <button
              onClick={handleOpenDispute}
              className="flex-1 bg-red-500 text-white py-2 rounded-lg text-sm font-semibold"
            >
              ⚠️ {t('chat.openDispute')}
            </button>
          </div>
        </div>
      )}

      {/* Input */}
      <div className="border-t border-gray-200 p-4 bg-white">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => {
              setInput(e.target.value)
              handleTyping()
            }}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            placeholder={t('chat.messagePlaceholder')}
            disabled={!isConnected}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50"
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim() || !isConnected}
            className="bg-tg-button text-tg-button-text px-6 py-2 rounded-lg font-semibold disabled:opacity-50"
          >
            ➤
          </button>
        </div>
        {messageQueue.length > 0 && (
          <div className="text-xs text-yellow-600 mt-2">
            {t('chat.messagesQueued', { count: messageQueue.length })}
          </div>
        )}
      </div>
    </div>
  )
}
