import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import api from '../api/client'
import { useCartStore } from '../store/cartStore'
import { useUIStore } from '../store/uiStore'

interface Lot {
  id: number
  title: string
  description: string
  price: number
  currency_code: string
  images: string[]
  seller_id: number
  seller_name: string
  seller_rating: number
  seller_total_sales: number
  rating: number
  total_reviews: number
  delivery_type: string
  delivery_time_minutes: number | null
  stock_count: number
  game_name: string
  category_name: string
}

interface Review {
  id: number
  user_name: string
  rating: number
  text: string
  photos: string[]
  created_at: string
  reply: string | null
}

export default function ProductPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { t } = useTranslation()
  const [lot, setLot] = useState<Lot | null>(null)
  const [reviews, setReviews] = useState<Review[]>([])
  const [loading, setLoading] = useState(true)
  const [quantity, setQuantity] = useState(1)
  const [selectedImage, setSelectedImage] = useState(0)
  const { addItem } = useCartStore()
  const { showToast } = useUIStore()

  useEffect(() => {
    fetchLot()
    fetchReviews()
  }, [id])

  const fetchLot = async () => {
    try {
      const response = await api.get(`/lots/${id}`)
      setLot(response.data)
    } catch (error) {
      console.error('Fetch lot error:', error)
      showToast(t('errors.notFound'), 'error')
    } finally {
      setLoading(false)
    }
  }

  const fetchReviews = async () => {
    try {
      const response = await api.get(`/lots/${id}/reviews`, {
        params: { limit: 5 }
      })
      setReviews(response.data.items)
    } catch (error) {
      console.error('Fetch reviews error:', error)
    }
  }

  const handleAddToCart = async () => {
    try {
      await addItem(Number(id), quantity)
      showToast(t('cart.addedToCart'), 'success')
    } catch (error: any) {
      if (error.response?.data?.error_code === 'insufficient_stock') {
        showToast(t('errors.insufficientStock'), 'error')
      } else {
        showToast(t('errors.generic'), 'error')
      }
    }
  }

  const handleBuyNow = async () => {
    try {
      await addItem(Number(id), quantity)
      navigate('/cart')
    } catch (error: any) {
      if (error.response?.data?.error_code === 'insufficient_stock') {
        showToast(t('errors.insufficientStock'), 'error')
      } else {
        showToast(t('errors.generic'), 'error')
      }
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-cyber-dark">
        <div className="text-center">
          <div className="inline-block animate-spin text-6xl mb-4">⚡</div>
          <div className="text-neon-cyan font-gaming">{t('app.loading')}</div>
        </div>
      </div>
    )
  }

  if (!lot) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-cyber-dark">
        <div className="text-center">
          <p className="mb-4 text-gray-400 font-gaming">{t('errors.notFound')}</p>
          <button
            onClick={() => navigate('/')}
            className="text-neon-cyan font-gaming hover:text-neon-red transition-colors duration-200"
          >
            {t('common.back')}
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen pb-24 bg-cyber-dark relative overflow-hidden">
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
      <div className="sticky top-0 backdrop-blur-xl bg-cyber-dark/90 border-b border-neon-red/30 shadow-neon-red p-4 z-10 flex items-center gap-3 transition-all duration-300">
        <button onClick={() => navigate(-1)} className="text-neon-cyan text-2xl hover:text-neon-red transition-all duration-200 hover:scale-110">
          ←
        </button>
        <h1 className="font-gaming font-black text-neon-red drop-shadow-[0_0_10px_rgba(255,0,51,0.8)]">{t('product.title')}</h1>
      </div>

      {/* Image Gallery */}
      <div className="bg-black/60 backdrop-blur-sm relative z-10">
        <div className="aspect-square flex items-center justify-center relative overflow-hidden">
          {lot.images && lot.images.length > 0 ? (
            <>
              <img 
                src={lot.images[selectedImage]} 
                alt={lot.title} 
                className="w-full h-full object-cover transition-transform duration-500"
              />
              {lot.images.length > 1 && (
                <>
                  <button
                    onClick={() => setSelectedImage(prev => Math.max(0, prev - 1))}
                    disabled={selectedImage === 0}
                    className="absolute left-2 top-1/2 -translate-y-1/2 bg-black/80 backdrop-blur-sm border-2 border-neon-red/50 text-neon-red w-12 h-12 rounded-full disabled:opacity-30 hover:border-neon-red hover:shadow-neon-red hover:scale-110 transition-all duration-200 font-gaming text-2xl"
                  >
                    ‹
                  </button>
                  <button
                    onClick={() => setSelectedImage(prev => Math.min(lot.images.length - 1, prev + 1))}
                    disabled={selectedImage === lot.images.length - 1}
                    className="absolute right-2 top-1/2 -translate-y-1/2 bg-black/80 backdrop-blur-sm border-2 border-neon-red/50 text-neon-red w-12 h-12 rounded-full disabled:opacity-30 hover:border-neon-red hover:shadow-neon-red hover:scale-110 transition-all duration-200 font-gaming text-2xl"
                  >
                    ›
                  </button>
                  <div className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-black/80 backdrop-blur-sm border border-neon-cyan/50 text-neon-cyan px-4 py-2 rounded-full text-sm font-gaming font-bold">
                    {selectedImage + 1} / {lot.images.length}
                  </div>
                </>
              )}
            </>
          ) : (
            <div className="w-full h-full bg-gradient-to-br from-neon-red/20 to-neon-purple/20 flex items-center justify-center">
              <span className="text-8xl animate-float">🎮</span>
            </div>
          )}
        </div>

        {/* Thumbnail strip */}
        {lot.images && lot.images.length > 1 && (
          <div className="flex gap-2 p-2 overflow-x-auto scrollbar-hide">
            {lot.images.map((img, idx) => (
              <button
                key={idx}
                onClick={() => setSelectedImage(idx)}
                className={`flex-shrink-0 w-20 h-20 rounded-lg border-2 transition-all duration-200 hover:scale-110 ${
                  selectedImage === idx ? 'border-neon-red shadow-neon-red' : 'border-gray-700 hover:border-neon-cyan'
                }`}
              >
                <img src={img} alt="" className="w-full h-full object-cover rounded-lg" />
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="p-4 relative z-10">
        {/* Title and Price */}
        <h1 className="text-2xl font-black font-gaming text-white mb-3 drop-shadow-[0_0_10px_rgba(255,255,255,0.3)]">{lot.title}</h1>
        <div className="flex items-center justify-between mb-4">
          <div className="text-4xl font-black font-gaming text-neon-red drop-shadow-[0_0_15px_rgba(255,0,51,0.8)]">
            {lot.price} {lot.currency_code}
          </div>
          <div className="text-right">
            <div className="text-neon-gold text-xl font-gaming">⭐ {lot.rating.toFixed(1)}</div>
            <div className="text-xs text-gray-400 font-gaming">{lot.total_reviews} {t('product.reviews')}</div>
          </div>
        </div>

        {/* Game and Category */}
        <div className="flex gap-2 mb-4">
          <span className="px-4 py-2 bg-black/60 border-2 border-neon-cyan/50 rounded-lg text-sm font-gaming font-bold text-neon-cyan hover:border-neon-cyan hover:shadow-neon-cyan transition-all duration-200">{lot.game_name}</span>
          <span className="px-4 py-2 bg-black/60 border-2 border-neon-purple/50 rounded-lg text-sm font-gaming font-bold text-neon-purple hover:border-neon-purple hover:shadow-neon-purple transition-all duration-200">{lot.category_name}</span>
        </div>

        {/* Delivery Info */}
        <div className="relative overflow-hidden rounded-xl bg-black/40 backdrop-blur-sm border-2 border-neon-purple/30 p-4 mb-4 hover:border-neon-purple hover:shadow-neon-purple transition-all duration-300">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm text-gray-400 font-gaming">{t('product.deliveryType')}</span>
            <span className="font-gaming font-bold text-neon-cyan">
              {lot.delivery_type === 'auto' ? '⚡ ' + t('home.deliveryType.auto') : '👤 ' + t('home.deliveryType.manual')}
            </span>
          </div>
          {lot.delivery_time_minutes && (
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-gray-400 font-gaming">{t('product.deliveryTime')}</span>
              <span className="font-gaming font-bold text-white">{lot.delivery_time_minutes} мин</span>
            </div>
          )}
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-400 font-gaming">{t('product.stock')}</span>
            <span className={`font-gaming font-bold ${lot.stock_count === 0 ? 'text-neon-red' : 'text-green-400'}`}>
              {lot.stock_count > 0 ? `${lot.stock_count} шт` : t('product.outOfStock')}
            </span>
          </div>
        </div>

        {/* Seller Info */}
        <Link
          to={`/seller/${lot.seller_id}`}
          className="relative overflow-hidden rounded-xl bg-black/40 backdrop-blur-sm border-2 border-neon-gold/30 p-4 mb-4 block hover:border-neon-gold hover:shadow-neon-gold hover:scale-[1.02] transition-all duration-300"
        >
          <div className="flex items-center justify-between">
            <div>
              <div className="font-gaming font-bold text-white text-lg">{lot.seller_name}</div>
              <div className="text-sm text-gray-400 font-gaming">
                ⭐ {lot.seller_rating.toFixed(1)} • {lot.seller_total_sales} {t('seller.sales')}
              </div>
            </div>
            <span className="text-neon-gold text-2xl">›</span>
          </div>
        </Link>

        {/* Description */}
        <div className="relative overflow-hidden rounded-xl bg-black/40 backdrop-blur-sm border-2 border-neon-red/30 p-4 mb-4 hover:border-neon-red hover:shadow-neon-red transition-all duration-300">
          <h2 className="font-gaming font-bold text-neon-cyan mb-3 text-lg">{t('product.description')}</h2>
          <p className="text-gray-300 whitespace-pre-wrap font-gaming leading-relaxed">{lot.description}</p>
        </div>

        {/* Quantity Selector */}
        {lot.stock_count > 0 && (
          <div className="relative overflow-hidden rounded-xl bg-black/40 backdrop-blur-sm border-2 border-neon-purple/30 p-4 mb-4 hover:border-neon-purple hover:shadow-neon-purple transition-all duration-300">
            <label className="block text-sm font-gaming font-bold text-neon-cyan mb-3">{t('cart.quantity')}</label>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setQuantity(Math.max(1, quantity - 1))}
                className="w-12 h-12 bg-black/60 border-2 border-neon-purple/50 rounded-lg font-gaming font-black text-white hover:border-neon-purple hover:shadow-neon-purple hover:scale-110 transition-all duration-200"
              >
                -
              </button>
              <input
                type="number"
                value={quantity}
                onChange={(e) => setQuantity(Math.max(1, Math.min(lot.stock_count, parseInt(e.target.value) || 1)))}
                className="w-24 text-center bg-black/60 border-2 border-neon-purple/50 rounded-lg py-3 text-white font-gaming font-bold focus:outline-none focus:border-neon-purple focus:shadow-neon-purple transition-all duration-200"
              />
              <button
                onClick={() => setQuantity(Math.min(lot.stock_count, quantity + 1))}
                className="w-12 h-12 bg-black/60 border-2 border-neon-purple/50 rounded-lg font-gaming font-black text-white hover:border-neon-purple hover:shadow-neon-purple hover:scale-110 transition-all duration-200"
              >
                +
              </button>
              <span className="text-sm text-gray-400 font-gaming">
                {t('product.stock')}: {lot.stock_count}
              </span>
            </div>
          </div>
        )}

        {/* Reviews */}
        {reviews.length > 0 && (
          <div className="mb-4">
            <h2 className="font-gaming font-black text-neon-cyan mb-4 text-xl">⭐ {t('product.reviews')}</h2>
            <div className="space-y-3">
              {reviews.map(review => (
                <div key={review.id} className="relative overflow-hidden rounded-xl bg-black/40 backdrop-blur-sm border-2 border-neon-red/30 p-4 hover:border-neon-red hover:shadow-neon-red transition-all duration-300">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-gaming font-bold text-white">{review.user_name}</span>
                    <span className="text-neon-gold font-gaming">{'⭐'.repeat(review.rating)}</span>
                  </div>
                  {review.text && <p className="text-sm text-gray-300 mb-2 font-gaming">{review.text}</p>}
                  {review.photos && review.photos.length > 0 && (
                    <div className="flex gap-2 mb-2">
                      {review.photos.map((photo, idx) => (
                        <img key={idx} src={photo} alt="" className="w-16 h-16 object-cover rounded-lg border-2 border-neon-cyan/30 hover:border-neon-cyan hover:scale-110 transition-all duration-200" />
                      ))}
                    </div>
                  )}
                  <div className="text-xs text-gray-500 font-gaming">
                    {new Date(review.created_at).toLocaleDateString()}
                  </div>
                  {review.reply && (
                    <div className="mt-3 pl-4 border-l-2 border-neon-purple">
                      <div className="text-sm text-gray-300 font-gaming">{review.reply}</div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Bottom Actions */}
      <div className="fixed bottom-0 left-0 right-0 backdrop-blur-xl bg-cyber-dark/95 border-t-2 border-neon-red/30 shadow-neon-red p-4 transition-all duration-300">
        <div className="flex gap-3">
          <button
            onClick={handleAddToCart}
            disabled={lot.stock_count === 0}
            className="flex-1 border-2 border-neon-red text-neon-red py-4 rounded-xl font-gaming font-black tracking-wide disabled:opacity-50 disabled:cursor-not-allowed hover:bg-neon-red/10 hover:shadow-neon-red hover:scale-105 transition-all duration-200"
          >
            🛒 {t('product.addToCart')}
          </button>
          <button
            onClick={handleBuyNow}
            disabled={lot.stock_count === 0}
            className="flex-1 bg-gradient-to-r from-neon-red to-neon-purple text-white py-4 rounded-xl font-gaming font-black tracking-wide disabled:opacity-50 disabled:cursor-not-allowed shadow-neon-red hover:shadow-neon-purple hover:scale-105 transition-all duration-200"
          >
            ⚡ {t('product.buyNow')}
          </button>
        </div>
      </div>
    </div>
  )
}
