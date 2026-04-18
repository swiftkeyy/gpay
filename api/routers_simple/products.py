"""Products router - simplified version."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db_session
from app.models.entities import Product, Price

router = APIRouter()


@router.get("/products")
async def get_products(
    game_id: int = Query(None),
    category_id: int = Query(None),
    session: AsyncSession = Depends(get_db_session)
):
    """Get products, optionally filtered by game or category."""
    stmt = select(Product).where(Product.is_active == True, Product.is_deleted == False)
    
    if game_id:
        stmt = stmt.where(Product.game_id == game_id)
    if category_id:
        stmt = stmt.where(Product.category_id == category_id)
    
    stmt = stmt.order_by(Product.sort_order)
    result = await session.execute(stmt)
    products = result.scalars().all()
    
    # Get prices for products
    product_ids = [p.id for p in products]
    if product_ids:
        price_stmt = select(Price).where(
            Price.product_id.in_(product_ids),
            Price.is_active == True
        )
        price_result = await session.execute(price_stmt)
        prices = {p.product_id: p for p in price_result.scalars().all()}
    else:
        prices = {}
    
    return [
        {
            "id": product.id,
            "game_id": product.game_id,
            "category_id": product.category_id,
            "slug": product.slug,
            "title": product.title,
            "description": product.description,
            "image_id": product.image_id,
            "is_active": product.is_active,
            "is_featured": product.is_featured,
            "sort_order": product.sort_order,
            "price": {
                "base_price": float(prices[product.id].base_price) if product.id in prices else 0,
                "discounted_price": float(prices[product.id].discounted_price) if product.id in prices and prices[product.id].discounted_price else None,
                "currency_code": prices[product.id].currency_code if product.id in prices else "RUB"
            } if product.id in prices else None
        }
        for product in products
    ]


@router.get("/products/{product_id}")
async def get_product(
    product_id: int,
    session: AsyncSession = Depends(get_db_session)
):
    """Get single product by ID."""
    stmt = select(Product).where(Product.id == product_id)
    result = await session.execute(stmt)
    product = result.scalar_one_or_none()
    
    if not product:
        return {"error": "Product not found"}, 404
    
    # Get price
    price_stmt = select(Price).where(
        Price.product_id == product_id,
        Price.is_active == True
    ).limit(1)
    price_result = await session.execute(price_stmt)
    price = price_result.scalar_one_or_none()
    
    return {
        "id": product.id,
        "game_id": product.game_id,
        "category_id": product.category_id,
        "slug": product.slug,
        "title": product.title,
        "description": product.description,
        "image_id": product.image_id,
        "is_active": product.is_active,
        "is_featured": product.is_featured,
        "sort_order": product.sort_order,
        "fulfillment_type": product.fulfillment_type,
        "requires_player_id": product.requires_player_id,
        "requires_nickname": product.requires_nickname,
        "requires_region": product.requires_region,
        "price": {
            "base_price": float(price.base_price) if price else 0,
            "discounted_price": float(price.discounted_price) if price and price.discounted_price else None,
            "currency_code": price.currency_code if price else "RUB"
        } if price else None
    }
