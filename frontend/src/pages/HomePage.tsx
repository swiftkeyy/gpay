import { useState, useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import api from '../api/client'
import { useCartStore } from '../store/cartStore'
import { useUIStore } from '../store/uiStore'
import BottomNav from '../components/BottomNav'
import ProductCard from '../components/ProductCard'

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
  game_name?: string
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

  useEffect(() => {
    fetchCategories()
    fetchGames()
  }, [])

  useEffect(() => {
    setLots([])
    setPage(1)
    setHasMore(true)
    fetchLots(1, true)
  }, [search, sortBy, deliveryType, minPrice, maxPrice, selectedGame, selectedCategory])

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

      {/* Epic Header with Logo */}
      <div className="sticky top-0 z-50 backdrop-blur-xl bg-cyber-dark/90 border-b border-neon-red/30 shadow-neon-red">
        <div className="p-4">
          {/* Logo and Balance */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              {/* Game Pay Logo */}
              <div className="relative">
                <div className="text-4xl font-black font-gaming text-white tracking-wider drop-shadow-[0_0_15px_rgba(255,0,51,0.8)]">
                  <span className="text-neon-red">G</span>
                  <span className="text-white">P</span>
                </div>
                <div className="absolute -bottom-1 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-neon-red to-transparent animate-pulse-glow" />
              </div>
              <div>
                <div className="text-xl font-black font-gaming text-neon-red tracking-wide drop-shadow-[0_0_10px_rgba(255,0,51,0.8)]">
                  GAME PAY
                </div>
                <div className="text-[8px] text-neon-cyan font-gaming tracking-widest">
                  PREMIUM MARKETPLACE
                </div>
              </div>
            </div>
            
            {/* Balance */}
            <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-black/40 border border-neon-gold/30 shadow-neon-gold">
              <span className="text-2xl">💎</span>
              <div className="text-right">
                <div className="text-xs text-neon-cyan font-gaming">BALANCE</div>
                <div className="text-sm font-bold text-neon-gold">0 ₽</div>
              </div>
            </div>
          </div>
          
          {/* Epic Search */}
          <div className="relative mb-4 group">
            <div className="absolute inset-0 bg-gradient-to-r from-neon-red/20 via-neon-purple/20 to-neon-cyan/20 rounded-xl blur-lg group-focus-within:blur-xl transition-all" />
            <div className="relative">
              <input
                type="text"
                placeholder="🔍 Search epic items..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full px-5 py-3 pr-12 bg-black/60 border-2 border-neon-red/50 rounded-xl text-white placeholder-gray-400 font-gaming focus:outline-none focus:border-neon-red focus:scale-[1.02] transition-all shadow-neon-red backdrop-blur-sm"
              />
              {search && (
                <button
                  onClick={() => setSearch('')}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-neon-red hover:text-white transition-colors"
                >
                  ✕
                </button>
              )}
            </div>
          </div>

          {/* Game Categories - Cyberpunk Style */}
          {games.length > 0 && (
            <div className="mb-4 -mx-4 px-4 overflow-x-auto scrollbar-hide">
              <div className="flex gap-2 pb-2">
                <button
                  onClick={() => setSelectedGame('')}
                  className={`flex-shrink-0 px-4 py-2 rounded-lg font-gaming text-xs font-bold tracking-wide transition-all ${
                    selectedGame === '' 
                      ? 'bg-gradient-to-r from-neon-red to-neon-purple text-white shadow-neon-red-lg animate-pulse-glow border-2 border-neon-red' 
                      : 'bg-black/40 text-gray-400 border-2 border-gray-700 hover:border-neon-red/50 hover:text-white'
                  }`}
                >
                  ALL GAMES
                </button>
                {games.map(game => (
                  <button
                    key={game.id}
                    onClick={() => setSelectedGame(String(game.id))}
                    className={`flex-shrink-0 px-4 py-2 rounded-lg font-gaming text-xs font-bold tracking-wide transition-all ${
                      selectedGame === String(game.id)
                        ? 'bg-gradient-to-r from-neon-red to-neon-purple text-white shadow-neon-red-lg animate-pulse-glow border-2 border-neon-red'
                        : 'bg-black/40 text-gray-400 border-2 border-gray-700 hover:border-neon-red/50 hover:text-white'
                    }`}
                  >
                    {game.name.toUpperCase()}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Filter and Sort - Gaming HUD Style */}
          <div className="flex gap-2">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`flex-1 px-4 py-2 rounded-lg font-gaming text-xs font-bold tracking-wide transition-all ${
                showFilters 
                  ? 'bg-gradient-to-r from-neon-purple to-neon-cyan text-white shadow-neon-purple border-2 border-neon-purple' 
                  : 'bg-black/40 text-gray-400 border-2 border-gray-700 hover:border-neon-purple/50 hover:text-white'
              }`}
            >
              🎯 FILTERS
            </button>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="flex-1 px-4 py-2 bg-black/60 border-2 border-neon-cyan/50 rounded-lg text-white font-gaming text-xs font-bold focus:outline-none focus:border-neon-cyan focus:shadow-neon-cyan transition-all"
            >
              <option value="popularity">🔥 POPULAR</option>
              <option value="price_asc">💰 CHEAP FIRST</option>
              <option value="price_desc">💎 EXPENSIVE FIRST</option>
              <option value="newest">⚡ NEWEST</option>
              <option value="rating">⭐ TOP RATED</option>
            </select>
          </div>
        </div>
      </div>

      {/* Filters Panel - Cyberpunk */}
      {showFilters && (
        <div className="bg-black/80 backdrop-blur-xl border-b border-neon-purple/30 p-4 shadow-neon-purple animate-slide-down">
          <div className="space-y-3">
            <div>
              <label className="block text-xs font-gaming font-bold text-neon-cyan mb-2 tracking-wide">CATEGORY</label>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="w-full px-3 py-2 bg-black/60 border-2 border-neon-purple/50 rounded-lg text-white font-gaming text-sm focus:outline-none focus:border-neon-purple focus:shadow-neon-purple transition-all"
              >
                <option value="">ALL CATEGORIES</option>
                {categories.map(cat => (
                  <option key={cat.id} value={cat.id}>{cat.name.toUpperCase()}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-gaming font-bold text-neon-cyan mb-2 tracking-wide">DELIVERY</label>
              <select
                value={deliveryType}
                onChange={(e) => setDeliveryType(e.target.value)}
                className="w-full px-3 py-2 bg-black/60 border-2 border-neon-purple/50 rounded-lg text-white font-gaming text-sm focus:outline-none focus:border-neon-purple focus:shadow-neon-purple transition-all"
              >
                <option value="">ALL TYPES</option>
                <option value="auto">⚡ AUTO DELIVERY</option>
                <option value="manual">👤 MANUAL</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-gaming font-bold text-neon-cyan mb-2 tracking-wide">PRICE RANGE</label>
              <div className="flex gap-2">
                <input
                  type="number"
                  placeholder="MIN"
                  value={minPrice}
                  onChange={(e) => setMinPrice(e.target.value)}
                  className="flex-1 px-3 py-2 bg-black/60 border-2 border-neon-purple/50 rounded-lg text-white font-gaming text-sm focus:outline-none focus:border-neon-purple focus:shadow-neon-purple transition-all"
                />
                <input
                  type="number"
                  placeholder="MAX"
                  value={maxPrice}
                  onChange={(e) => setMaxPrice(e.target.value)}
                  className="flex-1 px-3 py-2 bg-black/60 border-2 border-neon-purple/50 rounded-lg text-white font-gaming text-sm focus:outline-none focus:border-neon-purple focus:shadow-neon-purple transition-all"
                />
              </div>
            </div>

            <button
              onClick={clearFilters}
              className="w-full py-2 text-neon-red font-gaming text-sm font-bold hover:text-white transition-colors"
            >
              ✕ CLEAR ALL
            </button>
          </div>
        </div>
      )}

      {/* Epic Product Grid */}
      <div className="p-4 relative z-10">
        {loading && lots.length === 0 ? (
          <div className="text-center py-20">
            <div className="inline-block animate-spin text-6xl">⚡</div>
            <div className="text-neon-cyan font-gaming mt-4">LOADING EPIC ITEMS...</div>
          </div>
        ) : lots.length === 0 ? (
          <div className="text-center py-20 text-gray-500 font-gaming">NO ITEMS FOUND</div>
        ) : (
          <>
            <div className="grid grid-cols-2 gap-4">
              {lots.map((lot) => (
                <ProductCard
                  key={lot.id}
                  id={lot.id}
                  title={lot.title}
                  price={lot.price}
                  images={lot.images}
                  game_name={lot.game_name}
                  seller_name={lot.seller_name}
                  seller_rating={lot.seller_rating}
                  rating={lot.rating}
                  delivery_type={lot.delivery_type}
                  stock_count={lot.stock_count}
                  is_featured={lot.is_featured}
                  onAddToCart={(e) => handleAddToCart(lot.id, e)}
                />
              ))}
            </div>

            {/* Infinite Scroll Trigger */}
            {hasMore && (
              <div ref={observerTarget} className="text-center py-8">
                {loading && (
                  <div className="inline-block animate-spin text-4xl">⚡</div>
                )}
              </div>
            )}
          </>
        )}
      </div>

      {/* Epic Bottom Navigation */}
      <BottomNav />
    </div>
  )
}
