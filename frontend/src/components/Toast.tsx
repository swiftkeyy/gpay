import { useEffect } from 'react'
import { useUIStore } from '../store/uiStore'

export default function Toast() {
  const { toast, hideToast } = useUIStore()

  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => {
        hideToast()
      }, 3000)
      return () => clearTimeout(timer)
    }
  }, [toast, hideToast])

  if (!toast) return null

  const bgColor = {
    success: 'bg-green-500',
    error: 'bg-red-500',
    info: 'bg-blue-500',
    warning: 'bg-yellow-500'
  }[toast.type]

  return (
    <div className="fixed top-4 left-4 right-4 z-50 animate-slide-down">
      <div className={`${bgColor} text-white px-4 py-3 rounded-lg shadow-lg flex items-center justify-between`}>
        <span>{toast.message}</span>
        <button onClick={hideToast} className="ml-4 text-white font-bold">
          ✕
        </button>
      </div>
    </div>
  )
}
