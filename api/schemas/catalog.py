"""Catalog and search schemas."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class GameResponse(BaseModel):
    """Single game response."""
    id: int
    name: str
    slug: str
    description: str | None
    image_url: str | None
    is_active: bool


class GameListResponse(BaseModel):
    """Paginated game list response."""
    items: List[GameResponse]
    total: int
    page: int
    limit: int


class CategoryResponse(BaseModel):
    """Category response."""
    id: int
    name: str
    slug: str
    game_id: int
    parent_id: int | None = None


class ProductResponse(BaseModel):
    """Product response."""
    id: int
    title: str
    description: str | None
    category_id: int


class LotSearchItem(BaseModel):
    """Lot item in search results."""
    id: int
    title: str
    description: str
    price: float
    currency_code: str
    images: List[str]
    game_slug: str
    game_name: str
    game_image_url: str
    seller_name: str
    seller_rating: float
    rating: float
    delivery_type: str
    stock_count: int
    is_featured: bool


class LotSearchResponse(BaseModel):
    """Lot search results with pagination."""
    items: List[LotSearchItem]
    total: int
    page: int
    limit: int


class LotDetailResponse(BaseModel):
    """Detailed lot information."""
    id: int
    title: str
    description: str
    price: float
    currency_code: str
    images: List[str]
    game_slug: str
    game_name: str
    game_image_url: str
    category_name: str
    seller_name: str
    seller_id: int
    seller_rating: float
    seller_total_sales: int
    rating: float
    total_reviews: int
    delivery_type: str
    delivery_time_minutes: int | None
    stock_count: int
    is_featured: bool
    status: str


class FavoriteResponse(BaseModel):
    """Response for favorite operations."""
    message: str
