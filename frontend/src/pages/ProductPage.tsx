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
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">{t('app.loading')}</div>
      </div>
    )
  }

  if (!lot) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="mb-4">{t('errors.notFound')}</p>
          <button
            onClick={() => navigate('/')}
            className="text-tg-link"
          >
            {t('common.back')}
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen pb-20">
      {/* Header */}
      <div className="sticky top-0 bg-tg-bg border-b border-gray-200 p-4 z-10 flex items-center gap-3">
        <button onClick={() => navigate(-1)} className="text-tg-link text-xl">
          ←
        </button>
        <h1 className="font-semibold">{t('product.title')}</h1>
      </div>

      {/* Image Gallery */}
      <div className="bg-gray-100">
        <div className="aspect-square flex items-center justify-center relative">
          {lot.images && lot.images.length > 0 ? (
            <>
              <img 
                src={lot.images[selectedImage]} 
                alt={lot.title} 
                className="w-full h-full object-cover"
              />
              {lot.images.length > 1 && (
                <>
                  <button
                    onClick={() => setSelectedImage(prev => Math.max(0, prev - 1))}
                    disabled={selectedImage === 0}
                    className="absolute left-2 top-1/2 -translate-y-1/2 bg-black bg-opacity-50 text-white w-10 h-10 rounded-full disabled:opacity-30"
                  >
                    ‹
                  </button>
                  <button
                    onClick={() => setSelectedImage(prev => Math.min(lot.images.length - 1, prev + 1))}
                    disabled={selectedImage === lot.images.length - 1}
                    className="absolute right-2 top-1/2 -translate-y-1/2 bg-black bg-opacity-50 text-white w-10 h-10 rounded-full disabled:opacity-30"
                  >
                    ›
                  </button>
                  <div className="absolute bottom-2 left-1/2 -translate-x-1/2 bg-black bg-opacity-50 text-white px-3 py-1 rounded-full text-sm">
                    {selectedImage + 1} / {lot.images.length}
                  </div>
                </>
              )}
            </>
          ) : (
            <span className="text-6xl">🎮</span>
          )}
        </div>

        {/* Thumbnail strip */}
        {lot.images && lot.images.length > 1 && (
          <div className="flex gap-2 p-2 overflow-x-auto">
            {lot.images.map((img, idx) => (
              <button
                key={idx}
                onClick={() => setSelectedImage(idx)}
                className={`flex-shrink-0 w-16 h-16 rounded border-2 ${
                  selectedImage === idx ? 'border-tg-button' : 'border-gray-300'
                }`}
              >
                <img src={img} alt="" className="w-full h-full object-cover rounded" />
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="p-4">
        {/* Title and Price */}
        <h1 className="text-2xl font-bold mb-2">{lot.title}</h1>
        <div className="flex items-center justify-between mb-4">
          <div className="text-3xl font-bold text-tg-button">
            {lot.price} {lot.currency_code}
          </div>
          <div className="text-right">
            <div className="text-yellow-500">⭐ {lot.rating.toFixed(1)}</div>
            <div className="text-xs text-gray-500">{lot.total_reviews} {t('product.reviews')}</div>
          </div>
        </div>

        {/* Game and Category */}
        <div className="flex gap-2 mb-4">
          <span className="px-3 py-1 bg-gray-100 rounded-full text-sm">{lot.game_name}</span>
          <span className="px-3 py-1 bg-gray-100 rounded-full text-sm">{lot.category_name}</span>
        </div>

        {/* Delivery Info */}
        <div className="border border-gray-200 rounded-lg p-3 mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600">{t('product.deliveryType')}</span>
            <span className="font-medium">
              {lot.delivery_type === 'auto' ? t('home.deliveryType.auto') : t('home.deliveryType.manual')}
            </span>
          </div>
          {lot.delivery_time_minutes && (
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">{t('product.deliveryTime')}</span>
              <span className="font-medium">{lot.delivery_time_minutes} мин</span>
            </div>
          )}
          <div className="flex items-center justify-between mt-2">
            <span className="text-sm text-gray-600">{t('product.stock')}</span>
            <span className={`font-medium ${lot.stock_count === 0 ? 'text-red-500' : 'text-green-500'}`}>
              {lot.stock_count > 0 ? `${lot.stock_count} шт` : t('product.outOfStock')}
            </span>
          </div>
        </div>

        {/* Seller Info */}
        <Link
          to={`/seller/${lot.seller_id}`}
          className="border border-gray-200 rounded-lg p-3 mb-4 block hover:bg-gray-50"
        >
          <div className="flex items-center justify-between">
            <div>
              <div className="font-semibold">{lot.seller_name}</div>
              <div className="text-sm text-gray-500">
                ⭐ {lot.seller_rating.toFixed(1)} • {lot.seller_total_sales} {t('seller.sales')}
              </div>
            </div>
            <span className="text-tg-link">›</span>
          </div>
        </Link>

        {/* Description */}
        <div className="mb-4">
          <h2 className="font-semibold mb-2">{t('product.description')}</h2>
          <p className="text-gray-600 whitespace-pre-wrap">{lot.description}</p>
        </div>

        {/* Quantity Selector */}
        {lot.stock_count > 0 && (
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">{t('cart.quantity')}</label>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setQuantity(Math.max(1, quantity - 1))}
                className="w-10 h-10 border border-gray-300 rounded-lg font-bold"
              >
                -
              </button>
              <input
                type="number"
                value={quantity}
                onChange={(e) => setQuantity(Math.max(1, Math.min(lot.stock_count, parseInt(e.target.value) || 1)))}
                className="w-20 text-center border border-gray-300 rounded-lg py-2"
              />
              <button
                onClick={() => setQuantity(Math.min(lot.stock_count, quantity + 1))}
                className="w-10 h-10 border border-gray-300 rounded-lg font-bold"
              >
                +
              </button>
              <span className="text-sm text-gray-500">
                {t('product.stock')}: {lot.stock_count}
              </span>
            </div>
          </div>
        )}

        {/* Reviews */}
        {reviews.length > 0 && (
          <div className="mb-4">
            <h2 className="font-semibold mb-3">{t('product.reviews')}</h2>
            <div className="space-y-3">
              {reviews.map(review => (
                <div key={review.id} className="border border-gray-200 rounded-lg p-3">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium">{review.user_name}</span>
                    <span className="text-yellow-500">{'⭐'.repeat(review.rating)}</span>
                  </div>
                  {review.text && <p className="text-sm text-gray-600 mb-2">{review.text}</p>}
                  {review.photos && review.photos.length > 0 && (
                    <div className="flex gap-2 mb-2">
                      {review.photos.map((photo, idx) => (
                        <img key={idx} src={photo} alt="" className="w-16 h-16 object-cover rounded" />
                      ))}
                    </div>
                  )}
                  <div className="text-xs text-gray-400">
                    {new Date(review.created_at).toLocaleDateString()}
                  </div>
                  {review.reply && (
                    <div className="mt-2 pl-4 border-l-2 border-gray-200">
                      <div className="text-sm text-gray-600">{review.reply}</div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Bottom Actions */}
      <div className="fixed bottom-0 left-0 right-0 bg-tg-bg border-t border-gray-200 p-4">
        <div className="flex gap-2">
          <button
            onClick={handleAddToCart}
            disabled={lot.stock_count === 0}
            className="flex-1 border border-tg-button text-tg-button py-3 rounded-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {t('product.addToCart')}
          </button>
          <button
            onClick={handleBuyNow}
            disabled={lot.stock_count === 0}
            className="flex-1 bg-tg-button text-tg-button-text py-3 rounded-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {t('product.buyNow')}
          </button>
        </div>
      </div>
    </div>
  )
}
