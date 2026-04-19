"""Catalog and search router."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.models import Game, Category, Product, Lot, Seller
from api.services.cache import get_cache_service
from api.dependencies.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

# Real game images mapping (Playerok-style)
GAME_IMAGES = {
    "brawl-stars": "https://i.imgur.com/8QZqZ5L.png",
    "roblox": "https://i.imgur.com/xVpIvMZ.png",
    "genshin-impact": "https://i.imgur.com/yH8UqLJ.png",
    "cs2": "https://i.imgur.com/9fRaldg.png",
    "minecraft": "https://i.imgur.com/5MzQwYc.png",
    "standoff-2": "https://i.imgur.com/kF3jYvN.png",
    "fortnite": "https://i.imgur.com/TQcGHrA.png",
    "valorant": "https://i.imgur.com/X3FqJqZ.png",
    "pubg": "https://i.imgur.com/nRGzYvL.png",
    "mobile-legends": "https://i.imgur.com/8pLqZ5M.png",
}


class GameResponse(BaseModel):
    id: int
    title: str
    description: str | None
    image_url: str | None
    is_active: bool


class CategoryResponse(BaseModel):
    id: int
    title: str
    game_id: int
    parent_id: int | None


class ProductResponse(BaseModel):
    id: int
    title: str
    description: str | None
    category_id: int


class LotResponse(BaseModel):
    id: int
    title: str
    description: str | None
    price: float
    currency_code: str
    seller_id: int
    delivery_type: str
    stock_count: int
    status: str


@router.get("/games")
async def get_games(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    search: str | None = None,
    session: AsyncSession = Depends(get_db_session)
):
    """Get list of games with pagination, search, and Redis caching (5-minute TTL)."""
    # Generate cache key
    cache_key = f"games:page={page}:limit={limit}:search={search or ''}"
    
    # Try to get from cache
    cache = get_cache_service()
    cached_data = await cache.get(cache_key)
    if cached_data:
        logger.info(f"Cache HIT for {cache_key}")
        return cached_data
    
    logger.info(f"Cache MISS for {cache_key}")
    
    # Build query
    query = select(Game).where(Game.is_active == True)
    
    if search:
        query = query.where(Game.title.ilike(f"%{search}%"))
    
    # Get total count for pagination
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination and ordering
    query = query.order_by(Game.sort_order.asc()).offset((page - 1) * limit).limit(limit)
    result = await session.execute(query)
    games = result.scalars().all()
    
    # Build response
    response_data = {
        "items": [
            {
                "id": game.id,
                "name": game.title,
                "slug": game.slug,
                "description": game.description,
                "image_url": GAME_IMAGES.get(game.slug, f"https://picsum.photos/seed/{game.slug}/200/200"),
                "is_active": game.is_active
            }
            for game in games
        ],
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit if total > 0 else 0
    }
    
    # Cache the response
    await cache.set(cache_key, response_data)
    
    return response_data


@router.get("/games/{game_id}")
async def get_game(
    game_id: int,
    session: AsyncSession = Depends(get_db_session)
):
    """Get game details."""
    result = await session.execute(select(Game).where(Game.id == game_id))
    game = result.scalar_one_or_none()
    
    if not game:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Game not found")
    
    return GameResponse(
        id=game.id,
        title=game.title,
        description=game.description,
        image_url=None,
        is_active=game.is_active
    )


@router.get("/categories")
async def get_categories(
    game_id: int | None = None,
    session: AsyncSession = Depends(get_db_session)
):
    """Get hierarchical category structure with Redis caching (5-minute TTL)."""
    # Generate cache key
    cache_key = f"categories:game_id={game_id or 'all'}"
    
    # Try to get from cache
    cache = get_cache_service()
    cached_data = await cache.get(cache_key)
    if cached_data:
        logger.info(f"Cache HIT for {cache_key}")
        return cached_data
    
    logger.info(f"Cache MISS for {cache_key}")
    
    # Build query
    query = select(Category).where(Category.is_active == True)
    
    if game_id:
        query = query.where(Category.game_id == game_id)
    
    query = query.order_by(Category.sort_order.asc())
    result = await session.execute(query)
    categories = result.scalars().all()
    
    # Build hierarchical structure
    # Note: Current schema doesn't have parent_id, so we return flat list
    # If parent_id is added later, we can build tree structure here
    response_data = {
        "items": [
            {
                "id": cat.id,
                "name": cat.title,
                "slug": cat.slug,
                "game_id": cat.game_id,
                "description": cat.description,
                "is_active": cat.is_active
            }
            for cat in categories
        ],
        "total": len(categories)
    }
    
    # Cache the response
    await cache.set(cache_key, response_data)
    
    return response_data


@router.get("/products", response_model=list[ProductResponse])
async def get_products(
    game_id: int | None = None,
    category_id: int | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    session: AsyncSession = Depends(get_db_session)
):
    """Get list of products with filters and Redis caching (5-minute TTL)."""
    # Generate cache key
    cache_key = f"products:game_id={game_id or 'all'}:category_id={category_id or 'all'}:page={page}:limit={limit}"
    
    # Try to get from cache
    cache = get_cache_service()
    cached_data = await cache.get(cache_key)
    if cached_data:
        logger.info(f"Cache HIT for {cache_key}")
        return cached_data
    
    logger.info(f"Cache MISS for {cache_key}")
    
    # Build query
    query = select(Product).where(Product.is_active == True)
    
    if game_id:
        query = query.where(Product.game_id == game_id)
    if category_id:
        query = query.where(Product.category_id == category_id)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    query = query.order_by(Product.sort_order.asc()).offset((page - 1) * limit).limit(limit)
    result = await session.execute(query)
    products = result.scalars().all()
    
    # Build response
    response_data = [
        ProductResponse(
            id=prod.id,
            title=prod.title,
            description=prod.description,
            category_id=prod.category_id
        ).model_dump()
        for prod in products
    ]
    
    # Cache the response
    await cache.set(cache_key, response_data)
    
    return response_data


@router.get("/lots")
async def search_lots(
    game_id: int | None = None,
    category_id: int | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    delivery_type: str | None = None,
    min_seller_rating: float | None = None,
    sort: str = "popularity",
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    session: AsyncSession = Depends(get_db_session)
):
    """Search lots with filters and sorting.
    
    Filters:
    - game_id: Filter by game
    - category_id: Filter by category
    - min_price: Minimum price
    - max_price: Maximum price
    - delivery_type: Filter by delivery type (auto, manual, coordinates)
    - min_seller_rating: Minimum seller rating
    
    Sorting:
    - popularity: Sort by boosted status, featured status, and sales count (default)
    - price_asc: Sort by price ascending
    - price_desc: Sort by price descending
    - newest: Sort by creation date descending
    - rating: Sort by seller rating descending
    
    **Validates Requirements 22.3**: Prioritizes boosted lots in search results.
    Boosted lots (with boosted_until > current_time) appear first in all sort modes.
    """
    from app.models import Seller
    from sqlalchemy.orm import joinedload
    from datetime import datetime
    
    logger.info(f"Searching lots: game_id={game_id}, category_id={category_id}, min_price={min_price}, "
                f"max_price={max_price}, delivery_type={delivery_type}, min_seller_rating={min_seller_rating}, "
                f"sort={sort}, page={page}, limit={limit}")
    
    # Build query for lots with joins
    query = select(Lot).join(Lot.seller).join(Lot.product).options(
        joinedload(Lot.seller),
        joinedload(Lot.product)
    ).where(
        Lot.is_deleted == False,
        Lot.status == "active"
    )
    
    # Apply filters
    if game_id:
        query = query.where(Product.game_id == game_id)
    
    if category_id:
        query = query.where(Product.category_id == category_id)
    
    if min_price is not None:
        query = query.where(Lot.price >= min_price)
    
    if max_price is not None:
        query = query.where(Lot.price <= max_price)
    
    if delivery_type:
        query = query.where(Lot.delivery_type == delivery_type)
    
    if min_seller_rating is not None:
        query = query.where(Seller.rating >= min_seller_rating)
    
    # Apply sorting with boosted lots prioritized (Requirement 22.3)
    # Boosted lots (boosted_until > now) always appear first
    now = datetime.utcnow()
    
    # Create a case expression for boost priority
    # 1 if boosted and not expired, 0 otherwise
    from sqlalchemy import case
    boost_priority = case(
        (Lot.boosted_until > now, 1),
        else_=0
    )
    
    if sort == "price_asc":
        query = query.order_by(boost_priority.desc(), Lot.price.asc())
    elif sort == "price_desc":
        query = query.order_by(boost_priority.desc(), Lot.price.desc())
    elif sort == "newest":
        query = query.order_by(boost_priority.desc(), Lot.created_at.desc())
    elif sort == "rating":
        query = query.order_by(boost_priority.desc(), Seller.rating.desc())
    else:  # popularity (default)
        query = query.order_by(boost_priority.desc(), Lot.is_featured.desc(), Lot.sold_count.desc())
    
    # Get total count for pagination
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    query = query.offset((page - 1) * limit).limit(limit)
    result = await session.execute(query)
    lots = result.scalars().all()
    
    logger.info(f"Found {len(lots)} lots (total: {total})")
    
    # Build response
    items = []
    for lot in lots:
        # Get game info for images
        game_result = await session.execute(
            select(Game).where(Game.id == lot.product.game_id)
        )
        game = game_result.scalar_one_or_none()
        
        # Use game-specific images
        game_slug = game.slug if game else "default"
        game_image = GAME_IMAGES.get(game_slug, f"https://picsum.photos/seed/{game_slug}/400/400")
        
        # Get lot images or use game image as fallback
        image_urls = []
        if lot.images:
            # TODO: Get actual image URLs from media_files table
            image_urls = [game_image]  # Fallback for now
        else:
            image_urls = [
                game_image,
                f"https://picsum.photos/seed/{lot.id}-2/400/400",
                f"https://picsum.photos/seed/{lot.id}-3/400/400",
            ]
        
        # Check if lot is currently boosted (Requirement 22.3)
        is_boosted = lot.boosted_until is not None and lot.boosted_until > now
        
        items.append({
            "id": lot.id,
            "title": lot.title,
            "description": lot.description or "",
            "price": float(lot.price),
            "currency_code": lot.currency_code,
            "images": image_urls,
            "game_slug": game_slug,
            "game_name": game.title if game else "Unknown",
            "game_image_url": game_image,
            "seller_id": lot.seller_id,
            "seller_name": lot.seller.shop_name,
            "seller_rating": float(lot.seller.rating),
            "delivery_type": lot.delivery_type.value,
            "stock_count": lot.stock_count - lot.reserved_count,
            "is_featured": lot.is_featured,
            "is_boosted": is_boosted,
            "boosted_until": lot.boosted_until.isoformat() if lot.boosted_until else None,
            "status": lot.status.value,
        })
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit if total > 0 else 0
    }


@router.get("/lots/{lot_id}")
async def get_lot(
    lot_id: int,
    session: AsyncSession = Depends(get_db_session)
):
    """Get lot details with full information."""
    from sqlalchemy.orm import joinedload
    from app.models import Seller
    
    # Get lot with relationships
    result = await session.execute(
        select(Lot)
        .options(
            joinedload(Lot.seller),
            joinedload(Lot.product),
            joinedload(Lot.images)
        )
        .where(Lot.id == lot_id, Lot.is_deleted == False)
    )
    lot = result.scalar_one_or_none()
    
    if not lot:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Lot not found")
    
    # Get game info
    game_result = await session.execute(
        select(Game).where(Game.id == lot.product.game_id)
    )
    game = game_result.scalar_one_or_none()
    
    # Get category info
    category_result = await session.execute(
        select(Category).where(Category.id == lot.product.category_id)
    )
    category = category_result.scalar_one_or_none()
    
    # Use game-specific images
    game_slug = game.slug if game else "default"
    game_image = GAME_IMAGES.get(game_slug, f"https://picsum.photos/seed/{game_slug}/400/400")
    
    # Get lot images or use game image as fallback
    image_urls = []
    if lot.images:
        # TODO: Get actual image URLs from media_files table
        image_urls = [game_image]  # Fallback for now
    else:
        image_urls = [
            game_image,
            f"https://picsum.photos/seed/{lot.id}-2/400/400",
            f"https://picsum.photos/seed/{lot.id}-3/400/400",
        ]
    
    # Calculate available stock
    available_stock = lot.stock_count - lot.reserved_count
    
    return {
        "id": lot.id,
        "title": lot.title,
        "description": lot.description or "",
        "price": float(lot.price),
        "currency_code": lot.currency_code,
        "images": image_urls,
        "game_slug": game_slug,
        "game_name": game.title if game else "Unknown",
        "game_image_url": game_image,
        "category_name": category.title if category else "Unknown",
        "seller_id": lot.seller_id,
        "seller_name": lot.seller.shop_name,
        "seller_rating": float(lot.seller.rating),
        "seller_total_sales": lot.seller.total_sales,
        "seller_is_verified": lot.seller.is_verified,
        "delivery_type": lot.delivery_type.value,
        "delivery_time_minutes": lot.delivery_time_minutes,
        "stock_count": available_stock,
        "is_featured": lot.is_featured,
        "status": lot.status.value,
        "created_at": lot.created_at.isoformat(),
        "updated_at": lot.updated_at.isoformat() if lot.updated_at else None,
    }


@router.post("/lots/{lot_id}/favorite")
async def add_to_favorites(
    lot_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user)
):
    """Add lot to favorites.
    
    **Validates Requirements 21.1**: Creates favorite record with user ID and lot ID.
    """
    from app.models import Favorite
    
    # Check if lot exists
    lot_result = await session.execute(
        select(Lot).where(Lot.id == lot_id, Lot.is_deleted == False)
    )
    lot = lot_result.scalar_one_or_none()
    
    if not lot:
        raise HTTPException(status_code=404, detail="Lot not found")
    
    # Check if already favorited (duplicate check as per requirement 21.1)
    result = await session.execute(
        select(Favorite).where(
            Favorite.user_id == current_user.id,
            Favorite.lot_id == lot_id
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        return {"message": "Already in favorites"}
    
    favorite = Favorite(user_id=current_user.id, lot_id=lot_id)
    session.add(favorite)
    await session.commit()
    
    return {"message": "Added to favorites"}


@router.delete("/lots/{lot_id}/favorite")
async def remove_from_favorites(
    lot_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user)
):
    """Remove lot from favorites.
    
    **Validates Requirements 21.2**: Deletes the favorite record.
    """
    from app.models import Favorite
    from sqlalchemy import delete
    
    await session.execute(
        delete(Favorite).where(
            Favorite.user_id == current_user.id,
            Favorite.lot_id == lot_id
        )
    )
    await session.commit()
    
    return {"message": "Removed from favorites"}


@router.get("/lots/{lot_id}/reviews")
async def get_lot_reviews(
    lot_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session)
):
    """Get reviews for a lot (product)."""
    from app.models.entities import Review
    
    # Check if product exists
    result = await session.execute(
        select(Product).where(Product.id == lot_id, Product.is_active == True)
    )
    product = result.scalar_one_or_none()
    
    if not product:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Lot not found")
    
    # Get reviews for this product
    offset = (page - 1) * limit
    
    result = await session.execute(
        select(Review)
        .where(Review.product_id == lot_id, Review.status == "published")
        .order_by(Review.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    reviews = result.scalars().all()
    
    # Get total count
    from sqlalchemy import func
    result = await session.execute(
        select(func.count(Review.id)).where(
            Review.product_id == lot_id,
            Review.status == "published"
        )
    )
    total = result.scalar() or 0
    
    return {
        "items": [
            {
                "id": review.id,
                "user_id": review.user_id,
                "rating": review.rating,
                "text": review.text,
                "created_at": review.created_at.isoformat()
            }
            for review in reviews
        ],
        "total": total,
        "page": page,
        "limit": limit,
        "average_rating": 5.0  # TODO: Calculate real average
    }
