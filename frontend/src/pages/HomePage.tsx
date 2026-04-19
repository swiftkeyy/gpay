import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import api from '../api/client'
import { useCartStore } from '../store/cartStore'
import { useUIStore } from '../store/uiStore'
import BottomNav from '../components/BottomNav'

interface Lot {
  id: number
  title: string
  price: number
  currency_code: string
  images: string[]
  seller_name: string
  seller_rating: number
  rating: number
  delivery_type: string
  stock_count: number
  is_featured: boolean
}

interface Category {
  id: number
  name: string
  slug: string
}

interface Game {
  id: number
  name: string
  slug: string
}

export default function HomePage() {
  const { t } = useTranslation()
  const [lots, setLots] = useState<Lot[]>([])
  const [loading, setLoading] = useState(true)
  const [hasMore, setHasMore] = useState(true)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [sortBy, setSortBy] = useState('popularity')
  const [deliveryType, setDeliveryType] = useState<string>('')
  const [minPrice, setMinPrice] = useState<string>('')
  const [maxPrice, setMaxPrice] = useState<string>('')
  const [showFilters, setShowFilters] = useState(false)
  const [categories, setCategories] = useState<Category[]>([])
  const [games, setGames] = useState<Game[]>([])
  const [selectedGame, setSelectedGame] = useState<string>('')
  const [selectedCategory, setSelectedCategory] = useState<string>('')
  
  const { addItem } = useCartStore()
  const { showToast } = useUIStore()
  const observerTarget = useRef<HTMLDivElement>(null)

  // Fetch categories and games on mount
  useEffect(() => {
    fetchCategories()
    fetchGames()
  }, [])

  // Fetch lots when filters change
  useEffect(() => {
    setLots([])
    setPage(1)
    setHasMore(true)
    fetchLots(1, true)
  }, [search, sortBy, deliveryType, minPrice, maxPrice, selectedGame, selectedCategory])

  // Infinite scroll observer
  useEffect(() => {
    const observer = new IntersectionObserver(
      entries => {
        if (entries[0].isIntersecting && hasMore && !loading) {
          setPage(prev => prev + 1)
        }
      },
      { threshold: 0.1 }
    )

    if (observerTarget.current) {
      observer.observe(observerTarget.current)
    }

    return () => observer.disconnect()
  }, [hasMore, loading])

  // Fetch more lots when page changes
  useEffect(() => {
    if (page > 1) {
      fetchLots(page, false)
    }
  }, [page])

  const fetchCategories = async () => {
    try {
      const response = await api.get('/categories')
      setCategories(Array.isArray(response.data) ? response.data : [])
    } catch (error) {
      console.error('Fetch categories error:', error)
      setCategories([])
    }
  }

  const fetchGames = async () => {
    try {
      const response = await api.get('/games', { params: { limit: 50 } })
      setGames(Array.isArray(response.data?.items) ? response.data.items : [])
    } catch (error) {
      console.error('Fetch games error:', error)
      setGames([])
    }
  }

  const fetchLots = async (pageNum: number, reset: boolean) => {
    try {
      setLoading(true)
      const params: any = {
        page: pageNum,
        limit: 20,
        sort: sortBy
      }

      if (search) params.search = search
      if (deliveryType) params.delivery_type = deliveryType
      if (minPrice) params.min_price = minPrice
      if (maxPrice) params.max_price = maxPrice
      if (selectedGame) params.game_id = selectedGame
      if (selectedCategory) params.category_id = selectedCategory

      const response = await api.get('/lots', { params })
      const newLots = response.data?.items || []

      if (reset) {
        setLots(newLots)
      } else {
        setLots(prev => [...prev, ...newLots])
      }

      setHasMore(Array.isArray(newLots) && newLots.length === 20)
    } catch (error) {
      console.error('Fetch lots error:', error)
      showToast(t('errors.generic'), 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleAddToCart = async (lotId: number, e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    try {
      await addItem(lotId, 1)
      showToast(t('cart.addedToCart'), 'success')
    } catch (error) {
      showToast(t('errors.generic'), 'error')
    }
  }

  const clearFilters = () => {
    setSearch('')
    setSortBy('popularity')
    setDeliveryType('')
    setMinPrice('')
    setMaxPrice('')
    setSelectedGame('')
    setSelectedCategory('')
  }

  return (
    <div className="min-h-screen pb-20">
      {/* Header */}
      <div className="sticky top-0 bg-tg-bg border-b border-gray-200 p-4 z-10">
        <h1 className="text-2xl font-bold mb-3">🎮 {t('app.title')}</h1>
        
        {/* Search */}
        <div className="relative mb-3">
          <input
            type="text"
            placeholder={t('home.search')}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full px-4 py-2 pr-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-tg-button"
          />
          {search && (
            <button
              onClick={() => setSearch('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400"
            >
              ✕
            </button>
          )}
        </div>

        {/* Filter and Sort buttons */}
        <div className="flex gap-2">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium"
          >
            🔍 {t('home.filters')}
          </button>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium"
          >
            <option value="popularity">{t('home.sortBy.popularity')}</option>
            <option value="price_asc">{t('home.sortBy.priceAsc')}</option>
            <option value="price_desc">{t('home.sortBy.priceDesc')}</option>
            <option value="newest">{t('home.sortBy.newest')}</option>
            <option value="rating">{t('home.sortBy.rating')}</option>
          </select>
        </div>
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <div className="bg-tg-secondary p-4 border-b border-gray-200">
          <div className="space-y-3">
            {/* Game filter */}
            <div>
              <label className="block text-sm font-medium mb-1">{t('lot.game')}</label>
              <select
                value={selectedGame}
                onChange={(e) => setSelectedGame(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              >
                <option value="">{t('common.all')}</option>
                {games.map(game => (
                  <option key={game.id} value={game.id}>{game.name}</option>
                ))}
              </select>
            </div>

            {/* Category filter */}
            <div>
              <label className="block text-sm font-medium mb-1">{t('lot.category')}</label>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              >
                <option value="">{t('common.all')}</option>
                {categories.map(cat => (
                  <option key={cat.id} value={cat.id}>{cat.name}</option>
                ))}
              </select>
            </div>

            {/* Delivery type filter */}
            <div>
              <label className="block text-sm font-medium mb-1">{t('product.deliveryType')}</label>
              <select
                value={deliveryType}
                onChange={(e) => setDeliveryType(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              >
                <option value="">{t('common.all')}</option>
                <option value="auto">{t('home.deliveryType.auto')}</option>
                <option value="manual">{t('home.deliveryType.manual')}</option>
              </select>
            </div>

            {/* Price range */}
            <div>
              <label className="block text-sm font-medium mb-1">{t('product.price')}</label>
              <div className="flex gap-2">
                <input
                  type="number"
                  placeholder="Min"
                  value={minPrice}
                  onChange={(e) => setMinPrice(e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg"
                />
                <input
                  type="number"
                  placeholder="Max"
                  value={maxPrice}
                  onChange={(e) => setMaxPrice(e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
            </div>

            {/* Clear filters */}
            <button
              onClick={clearFilters}
              className="w-full py-2 text-tg-link text-sm font-medium"
            >
              {t('common.clear')}
            </button>
          </div>
        </div>
      )}

      {/* Lots Grid */}
      <div className="p-4">
        {loading && lots.length === 0 ? (
          <div className="text-center py-10">{t('app.loading')}</div>
        ) : lots.length === 0 ? (
          <div className="text-center py-10 text-gray-500">{t('home.noResults')}</div>
        ) : (
          <>
            <div className="grid grid-cols-2 gap-4">
              {lots.map((lot) => (
                <div key={lot.id} className="border border-gray-200 rounded-lg overflow-hidden bg-white">
                  <Link to={`/product/${lot.id}`}>
                    <div className="aspect-square bg-gray-100 flex items-center justify-center relative">
                      {lot.images && Array.isArray(lot.images) && lot.images.length > 0 ? (
                        <img 
                          src={lot.images[0]} 
                          alt={lot.title} 
                          className="w-full h-full object-cover"
                          loading="lazy"
                        />
                      ) : (
                        <span className="text-4xl">🎮</span>
                      )}
                      {lot.is_featured && (
                        <div className="absolute top-2 right-2 bg-yellow-400 text-xs px-2 py-1 rounded-full font-bold">
                          ⭐
                        </div>
                      )}
                      {lot.stock_count === 0 && (
                        <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center">
                          <span className="text-white font-bold">{t('product.outOfStock')}</span>
                        </div>
                      )}
                    </div>
                  </Link>
                  
                  <div className="p-3">
                    <Link to={`/product/${lot.id}`}>
                      <h3 className="font-semibold text-sm mb-1 line-clamp-2 min-h-[2.5rem]">
                        {lot.title}
                      </h3>
                    </Link>
                    
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-lg font-bold">
                        {lot.price} {lot.currency_code}
                      </span>
                      <span className="text-xs text-gray-500">
                        ⭐ {lot.rating.toFixed(1)}
                      </span>
                    </div>

                    <div className="text-xs text-gray-500 mb-2">
                      {lot.seller_name} • ⭐ {lot.seller_rating.toFixed(1)}
                    </div>
                    
                    <button
                      onClick={(e) => handleAddToCart(lot.id, e)}
                      disabled={lot.stock_count === 0}
                      className="w-full bg-tg-button text-tg-button-text py-2 rounded-lg text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {t('product.addToCart')}
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {/* Infinite scroll trigger */}
            {hasMore && (
              <div ref={observerTarget} className="text-center py-4">
                {loading && <div className="text-gray-500">{t('app.loading')}</div>}
              </div>
            )}
          </>
        )}
      </div>

      {/* Bottom Navigation */}
      <BottomNav />
    </div>
  )
}
