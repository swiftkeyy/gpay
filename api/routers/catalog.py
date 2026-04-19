"""Catalog and search router."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.models import Game, Category, Product, Lot

router = APIRouter()


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
    """Get list of games with pagination."""
    query = select(Game).where(Game.is_active == True)
    
    if search:
        query = query.where(Game.title.ilike(f"%{search}%"))
    
    query = query.order_by(Game.sort_order.asc()).offset((page - 1) * limit).limit(limit)
    result = await session.execute(query)
    games = result.scalars().all()
    
    return {
        "items": [
            {
                "id": game.id,
                "name": game.title,
                "slug": game.slug,
                "description": game.description,
                "is_active": game.is_active
            }
            for game in games
        ],
        "total": len(games),
        "page": page,
        "limit": limit,
    }


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
    """Get list of categories."""
    query = select(Category).where(Category.is_active == True)
    
    if game_id:
        query = query.where(Category.game_id == game_id)
    
    query = query.order_by(Category.sort_order.asc())
    result = await session.execute(query)
    categories = result.scalars().all()
    
    return [
        {
            "id": cat.id,
            "name": cat.title,
            "slug": cat.slug,
            "game_id": cat.game_id
        }
        for cat in categories
    ]


@router.get("/products", response_model=list[ProductResponse])
async def get_products(
    category_id: int | None = None,
    session: AsyncSession = Depends(get_db_session)
):
    """Get list of products."""
    query = select(Product).where(Product.is_active == True)
    
    if category_id:
        query = query.where(Product.category_id == category_id)
    
    result = await session.execute(query)
    products = result.scalars().all()
    
    return [
        ProductResponse(
            id=prod.id,
            title=prod.title,
            description=prod.description,
            category_id=prod.category_id
        )
        for prod in products
    ]


@router.get("/lots")
async def search_lots(
    game_id: int | None = None,
    category_id: int | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    delivery_type: str | None = None,
    sort: str = "popularity",
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    session: AsyncSession = Depends(get_db_session)
):
    """Search lots with filters and sorting.
    
    TEMPORARY: Returns products as lots until we have real sellers and lots.
    """
    import logging
    from app.models import Price
    
    logger = logging.getLogger(__name__)
    logger.info(f"Fetching lots: game_id={game_id}, category_id={category_id}, page={page}, limit={limit}")
    
    # Query products with their prices
    query = select(Product).where(Product.is_active == True)
    
    if game_id:
        query = query.where(Product.game_id == game_id)
    if category_id:
        query = query.where(Product.category_id == category_id)
    
    # Sorting
    if sort == "price_asc":
        query = query.order_by(Product.sort_order.asc())
    elif sort == "price_desc":
        query = query.order_by(Product.sort_order.desc())
    elif sort == "newest":
        query = query.order_by(Product.created_at.desc())
    else:  # popularity
        query = query.order_by(Product.is_featured.desc(), Product.sort_order.asc())
    
    query = query.offset((page - 1) * limit).limit(limit)
    result = await session.execute(query)
    products = result.scalars().all()
    
    logger.info(f"Found {len(products)} products")
    
    # Get prices for products
    items = []
    for product in products:
        logger.info(f"Processing product: id={product.id}, title={product.title}")
        
        # Get active price
        price_result = await session.execute(
            select(Price).where(
                Price.product_id == product.id,
                Price.is_active == True
            ).limit(1)
        )
        price = price_result.scalar_one_or_none()
        
        if price:
            logger.info(f"Found price for product {product.id}: {price.base_price} {price.currency_code}")
            items.append({
                "id": product.id,
                "title": product.title or "Без названия",
                "description": product.description or "",
                "price": float(price.base_price) if price.base_price else 0.0,
                "currency_code": price.currency_code or "RUB",
                "images": [],  # TODO: Get from media_files
                "seller_name": "Game Pay",  # Temporary
                "seller_rating": 5.0,  # Temporary
                "rating": 5.0,  # Temporary
                "delivery_type": "manual",
                "stock_count": 999,  # Temporary - always in stock
                "is_featured": product.is_featured or False,
            })
        else:
            logger.warning(f"No price found for product {product.id}")
    
    logger.info(f"Returning {len(items)} items")
    
    return {
        "items": items,
        "total": len(items),
        "page": page,
        "limit": limit,
    }


@router.get("/lots/{lot_id}")
async def get_lot(
    lot_id: int,
    session: AsyncSession = Depends(get_db_session)
):
    """Get lot details."""
    result = await session.execute(select(Lot).where(Lot.id == lot_id))
    lot = result.scalar_one_or_none()
    
    if not lot:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Lot not found")
    
    return LotResponse(
        id=lot.id,
        title=lot.title,
        description=lot.description,
        price=float(lot.price),
        currency_code=lot.currency_code,
        seller_id=lot.seller_id,
        delivery_type=lot.delivery_type.value,
        stock_count=lot.stock_count,
        status=lot.status.value
    )


@router.post("/lots/{lot_id}/favorite")
async def add_to_favorites(
    lot_id: int,
    user_id: int = 1,  # TODO: Extract from auth token
    session: AsyncSession = Depends(get_db_session)
):
    """Add lot to favorites."""
    from app.models import Favorite
    
    # Check if already favorited
    result = await session.execute(
        select(Favorite).where(
            Favorite.user_id == user_id,
            Favorite.lot_id == lot_id
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        return {"message": "Already in favorites"}
    
    favorite = Favorite(user_id=user_id, lot_id=lot_id)
    session.add(favorite)
    await session.commit()
    
    return {"message": "Added to favorites"}


@router.delete("/lots/{lot_id}/favorite")
async def remove_from_favorites(
    lot_id: int,
    user_id: int = 1,  # TODO: Extract from auth token
    session: AsyncSession = Depends(get_db_session)
):
    """Remove lot from favorites."""
    from app.models import Favorite
    from sqlalchemy import delete
    
    await session.execute(
        delete(Favorite).where(
            Favorite.user_id == user_id,
            Favorite.lot_id == lot_id
        )
    )
    await session.commit()
    
    return {"message": "Removed from favorites"}
