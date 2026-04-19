import { Link } from 'react-router-dom'

interface ProductCardProps {
  id: number
  title: string
  price: number
  images: string[]
  game_name?: string
  seller_name: string
  seller_rating: number
  rating: number
  delivery_type: string
  stock_count: number
  is_featured: boolean
  onAddToCart: (e: React.MouseEvent) => void
}

// Определяем редкость на основе цены и featured статуса
const getRarity = (price: number, is_featured: boolean) => {
  if (is_featured || price > 5000) return 'legendary'
  if (price > 2000) return 'epic'
  if (price > 500) return 'rare'
  return 'common'
}

const rarityConfig = {
  common: {
    border: 'border-gray-500/50',
    borderHover: 'hover:border-gray-400',
    shadow: 'hover:shadow-[0_0_20px_rgba(156,163,175,0.4)]',
    glow: 'shadow-[0_0_15px_rgba(156,163,175,0.3)]',
    badge: 'bg-gray-600/80 text-gray-200 border-gray-500/50',
    badgeText: 'ОБЫЧНЫЙ',
    gradient: 'from-gray-600/20 to-gray-800/20'
  },
  rare: {
    border: 'border-blue-500/50',
    borderHover: 'hover:border-blue-400',
    shadow: 'hover:shadow-[0_0_25px_rgba(59,130,246,0.5)]',
    glow: 'shadow-[0_0_20px_rgba(59,130,246,0.4)]',
    badge: 'bg-blue-600/80 text-blue-100 border-blue-400/50',
    badgeText: 'РЕДКИЙ',
    gradient: 'from-blue-600/20 to-blue-800/20'
  },
  epic: {
    border: 'border-neon-purple/50',
    borderHover: 'hover:border-neon-purple',
    shadow: 'hover:shadow-[0_0_30px_rgba(157,78,221,0.6)]',
    glow: 'shadow-[0_0_25px_rgba(157,78,221,0.5)]',
    badge: 'bg-gradient-to-r from-neon-purple to-purple-600 text-white border-neon-purple/50',
    badgeText: 'ЭПИЧЕСКИЙ',
    gradient: 'from-neon-purple/20 to-purple-800/20'
  },
  legendary: {
    border: 'border-orange-500/50',
    borderHover: 'hover:border-orange-400',
    shadow: 'hover:shadow-[0_0_35px_rgba(249,115,22,0.7)]',
    glow: 'shadow-[0_0_30px_rgba(249,115,22,0.6)] animate-pulse-glow',
    badge: 'bg-gradient-to-r from-orange-500 via-red-500 to-orange-600 text-white border-orange-400/50 animate-pulse-glow',
    badgeText: 'ЛЕГЕНДАРНЫЙ',
    gradient: 'from-orange-600/20 to-red-800/20'
  }
}

export default function ProductCard({
  id,
  title,
  price,
  images,
  game_name,
  seller_name,
  seller_rating,
  rating,
  delivery_type,
  stock_count,
  is_featured,
  onAddToCart
}: ProductCardProps) {

  return (
    <Link 
      to={`/product/${id}`}
      className="group relative block"
    >
      {/* Premium Card Container */}
      <div className="relative overflow-hidden rounded-2xl bg-[#0F0F17] backdrop-blur-xl border-2 border-neon-red/30 hover:border-neon-red hover:shadow-[0_0_30px_rgba(255,0,51,0.6)] transition-all duration-300 hover:scale-[1.03] hover:-translate-y-1">
        
        {/* Shine Effect on Hover */}
        <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none">
          <div className="absolute top-0 -left-full h-full w-1/2 bg-gradient-to-r from-transparent via-white/10 to-transparent skew-x-12 group-hover:animate-shine" />
        </div>

        {/* Image Container */}
        <div className="aspect-[4/3] relative overflow-hidden">
          {images && Array.isArray(images) && images.length > 0 ? (
            <img 
              src={images[0]} 
              alt={title} 
              className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700"
              loading="lazy"
            />
          ) : (
            <div className="w-full h-full bg-gradient-to-br from-neon-red/20 to-neon-purple/20 flex items-center justify-center">
              <span className="text-7xl opacity-50">🎮</span>
            </div>
          )}
          
          {/* Dark Gradient Overlay for Better Text Readability */}
          <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent" />
          
          {/* Game Badge - Top Left */}
          {game_name && (
            <div className="absolute top-3 left-3 px-3 py-1.5 bg-black/90 backdrop-blur-md border-2 border-neon-cyan/60 rounded-lg font-gaming text-xs font-black text-neon-cyan tracking-wider shadow-neon-cyan">
              {game_name.toUpperCase()}
            </div>
          )}
          
          {/* Auto Delivery Badge - Bottom Left */}
          {delivery_type === 'auto' && (
            <div className="absolute bottom-3 left-3 px-3 py-1.5 bg-gradient-to-r from-green-500 to-emerald-500 backdrop-blur-md border-2 border-green-400/50 rounded-lg font-gaming text-xs font-black text-white shadow-[0_0_15px_rgba(34,197,94,0.5)]">
              ⚡ МОМЕНТАЛЬНО
            </div>
          )}
          
          {/* Out of Stock Overlay */}
          {stock_count === 0 && (
            <div className="absolute inset-0 bg-black/90 backdrop-blur-sm flex items-center justify-center">
              <div className="text-center">
                <div className="text-neon-red font-gaming font-black text-xl mb-2">ПРОДАНО</div>
                <div className="text-gray-400 font-gaming text-xs">НЕТ В НАЛИЧИИ</div>
              </div>
            </div>
          )}
        </div>
        
        {/* Card Content */}
        <div className="p-4 space-y-3 relative z-10">
          {/* Title */}
          <h3 className="font-gaming font-black text-base text-white leading-tight line-clamp-2 min-h-[2.5rem] group-hover:text-neon-cyan transition-colors duration-200">
            {title}
          </h3>
          
          {/* Price and Rating Row */}
          <div className="flex items-center justify-between">
            <div className="flex flex-col">
              <div className="text-xs text-gray-400 font-gaming mb-0.5">ЦЕНА</div>
              <div className="text-3xl font-black font-gaming text-neon-red drop-shadow-[0_0_15px_rgba(255,0,51,0.8)]">
                {price}₽
              </div>
            </div>
            <div className="flex flex-col items-end">
              <div className="flex items-center gap-1 text-neon-gold text-sm font-gaming mb-1">
                ⭐ {rating.toFixed(1)}
              </div>
              <div className="text-xs text-gray-500 font-gaming">
                {Math.floor(Math.random() * 100 + 20)} отзывов
              </div>
            </div>
          </div>

          {/* Seller Info */}
          <div className="flex items-center gap-2 py-2 px-3 bg-black/40 rounded-lg border border-gray-700/50">
            <div className="w-6 h-6 rounded-full bg-gradient-to-br from-neon-cyan to-neon-purple flex items-center justify-center text-xs">
              {seller_name.charAt(0).toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-xs text-gray-300 font-gaming truncate">{seller_name}</div>
            </div>
            <div className="flex items-center gap-1 text-neon-gold text-xs font-gaming">
              ⭐ {seller_rating.toFixed(1)}
            </div>
          </div>
          
          {/* Buy Button */}
          <button
            onClick={onAddToCart}
            disabled={stock_count === 0}
            className="w-full py-3 rounded-xl font-gaming text-sm font-black tracking-wider transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 bg-gradient-to-r from-neon-red to-neon-purple text-white shadow-[0_0_20px_rgba(255,0,51,0.6)] hover:shadow-[0_0_30px_rgba(255,0,51,0.8)] hover:scale-105"
          >
            <span className="text-lg">💎</span>
            КУПИТЬ СЕЙЧАС
          </button>
        </div>
      </div>
    </Link>
  )
}
