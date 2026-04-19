"""Reviews router."""
from __future__ import annotations

import logging
from typing import Optional, List
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from pydantic import BaseModel, Field, validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.entities import User, Deal, Order, Review as ProductReview, Review as SellerReview, Seller, Product
from api.dependencies.auth import get_current_user, get_current_admin

router = APIRouter()
logger = logging.getLogger(__name__)


# Pydantic models
class ProductReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    text: Optional[str] = Field(None, max_length=2000)
    photos: Optional[List[str]] = Field(None, max_items=5)


class SellerReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    text: Optional[str] = Field(None, max_length=2000)


class ReviewReply(BaseModel):
    reply_text: str = Field(..., min_length=1, max_length=1000)


class ReviewModeration(BaseModel):
    status: str = Field(..., pattern="^(published|rejected)$")
    rejection_reason: Optional[str] = Field(None, max_length=500)


# Product reviews
@router.get("/products/{product_id}/reviews")
async def get_product_reviews(
    product_id: int,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """Get product reviews."""
    # Get published reviews
    result = await db.execute(
        select(ProductReview)
        .options(selectinload(ProductReview.user))
        .where(
            and_(
                ProductReview.product_id == product_id,
                ProductReview.status == 'published'
            )
        )
        .order_by(desc(ProductReview.created_at))
        .offset(skip)
        .limit(limit)
    )
    reviews = result.scalars().all()
    
    # Calculate average rating
    result = await db.execute(
        select(func.avg(ProductReview.rating)).where(
            and_(
                ProductReview.product_id == product_id,
                ProductReview.status == 'published'
            )
        )
    )
    avg_rating = result.scalar() or 0.0
    
    # Count total reviews
    result = await db.execute(
        select(func.count(ProductReview.id)).where(
            and_(
                ProductReview.product_id == product_id,
                ProductReview.status == 'published'
            )
        )
    )
    total_reviews = result.scalar()
    
    return {
        "items": [
            {
                "id": review.id,
                "user_id": review.user_id,
                "username": review.user.username if review.user else "Anonymous",
                "rating": review.rating,
                "text": review.text,
                "photos": review.photos,
                "reply_text": review.reply_text,
                "created_at": review.created_at.isoformat()
            }
            for review in reviews
        ],
        "total": total_reviews,
        "average_rating": round(float(avg_rating), 2),
        "skip": skip,
        "limit": limit
    }


@router.post("/orders/{order_id}/review")
async def create_product_review(
    order_id: int,
    request: ProductReviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create product review."""
    # Get order
    result = await db.execute(
        select(Order).where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check if user is buyer
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your order")
    
    # Check if order is completed
    if order.status != "completed":
        raise HTTPException(status_code=400, detail="Order not completed")
    
    # Check if review already exists
    result = await db.execute(
        select(ProductReview).where(
            and_(
                ProductReview.order_id == order_id,
                ProductReview.user_id == current_user.id
            )
        )
    )
    existing_review = result.scalar_one_or_none()
    
    if existing_review:
        raise HTTPException(status_code=400, detail="Review already exists")
    
    # Create review
    review = ProductReview(
        user_id=current_user.id,
        order_id=order_id,
        product_id=order.product_id,
        rating=request.rating,
        text=request.text,
        photos=request.photos,
        status="pending"
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)
    
    logger.info(f"Product review created: id={review.id}, order_id={order_id}, user_id={current_user.id}")
    
    return {
        "review_id": review.id,
        "status": "pending",
        "message": "Review submitted for moderation"
    }


# Seller reviews
@router.get("/sellers/{seller_id}/reviews")
async def get_seller_reviews(
    seller_id: int,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """Get seller reviews."""
    # Get published reviews
    result = await db.execute(
        select(SellerReview)
        .options(selectinload(SellerReview.user))
        .where(
            and_(
                SellerReview.seller_id == seller_id,
                SellerReview.status == 'published'
            )
        )
        .order_by(desc(SellerReview.created_at))
        .offset(skip)
        .limit(limit)
    )
    reviews = result.scalars().all()
    
    # Calculate average rating
    result = await db.execute(
        select(func.avg(SellerReview.rating)).where(
            and_(
                SellerReview.seller_id == seller_id,
                SellerReview.status == 'published'
            )
        )
    )
    avg_rating = result.scalar() or 0.0
    
    # Count total reviews
    result = await db.execute(
        select(func.count(SellerReview.id)).where(
            and_(
                SellerReview.seller_id == seller_id,
                SellerReview.status == 'published'
            )
        )
    )
    total_reviews = result.scalar()
    
    return {
        "items": [
            {
                "id": review.id,
                "user_id": review.user_id,
                "username": review.user.username if review.user else "Anonymous",
                "rating": review.rating,
                "text": review.text,
                "reply_text": review.reply_text,
                "created_at": review.created_at.isoformat()
            }
            for review in reviews
        ],
        "total": total_reviews,
        "average_rating": round(float(avg_rating), 2),
        "skip": skip,
        "limit": limit
    }


@router.post("/deals/{deal_id}/review")
async def create_seller_review(
    deal_id: int,
    request: SellerReviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create seller review."""
    # Get deal
    result = await db.execute(
        select(Deal).where(Deal.id == deal_id)
    )
    deal = result.scalar_one_or_none()
    
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    # Check if user is buyer
    if deal.buyer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your deal")
    
    # Check if deal is completed
    if deal.status != "completed":
        raise HTTPException(status_code=400, detail="Deal not completed")
    
    # Check if review already exists
    result = await db.execute(
        select(SellerReview).where(
            and_(
                SellerReview.deal_id == deal_id,
                SellerReview.user_id == current_user.id
            )
        )
    )
    existing_review = result.scalar_one_or_none()
    
    if existing_review:
        raise HTTPException(status_code=400, detail="Review already exists")
    
    # Create review
    review = SellerReview(
        user_id=current_user.id,
        deal_id=deal_id,
        seller_id=deal.seller_id,
        rating=request.rating,
        text=request.text,
        status="pending"
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)
    
    logger.info(f"Seller review created: id={review.id}, deal_id={deal_id}, user_id={current_user.id}")
    
    return {
        "review_id": review.id,
        "status": "pending",
        "message": "Review submitted for moderation"
    }


# Review replies (seller can reply to their reviews)
@router.post("/reviews/seller/{review_id}/reply")
async def reply_to_seller_review(
    review_id: int,
    request: ReviewReply,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Reply to seller review."""
    # Get review
    result = await db.execute(
        select(SellerReview).where(SellerReview.id == review_id)
    )
    review = result.scalar_one_or_none()
    
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    # Check if user is the seller
    result = await db.execute(
        select(Seller).where(
            and_(
                Seller.id == review.seller_id,
                Seller.user_id == current_user.id
            )
        )
    )
    seller = result.scalar_one_or_none()
    
    if not seller:
        raise HTTPException(status_code=403, detail="Not your review")
    
    # Check if already replied
    if review.reply_text:
        raise HTTPException(status_code=400, detail="Already replied")
    
    # Add reply
    review.reply_text = request.reply_text
    review.replied_at = datetime.utcnow()
    
    await db.commit()
    
    return {
        "message": "Reply added successfully"
    }


@router.post("/reviews/product/{review_id}/reply")
async def reply_to_product_review(
    review_id: int,
    request: ReviewReply,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Reply to product review."""
    # Get review
    result = await db.execute(
        select(ProductReview).options(selectinload(ProductReview.order)).where(ProductReview.id == review_id)
    )
    review = result.scalar_one_or_none()
    
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    # Get seller from order
    result = await db.execute(
        select(Deal).where(Deal.order_id == review.order_id)
    )
    deal = result.scalar_one_or_none()
    
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    # Check if user is the seller
    result = await db.execute(
        select(Seller).where(
            and_(
                Seller.id == deal.seller_id,
                Seller.user_id == current_user.id
            )
        )
    )
    seller = result.scalar_one_or_none()
    
    if not seller:
        raise HTTPException(status_code=403, detail="Not your review")
    
    # Check if already replied
    if review.reply_text:
        raise HTTPException(status_code=400, detail="Already replied")
    
    # Add reply
    review.reply_text = request.reply_text
    review.replied_at = datetime.utcnow()
    
    await db.commit()
    
    return {
        "message": "Reply added successfully"
    }


# Admin moderation
@router.get("/admin/reviews/pending")
async def get_pending_reviews(
    review_type: str = "all",  # all, product, seller
    skip: int = 0,
    limit: int = 20,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get pending reviews for moderation."""
    reviews = []
    
    if review_type in ["all", "product"]:
        result = await db.execute(
            select(ProductReview)
            .options(selectinload(ProductReview.user))
            .where(ProductReview.status == 'pending')
            .order_by(desc(ProductReview.created_at))
            .offset(skip)
            .limit(limit)
        )
        product_reviews = result.scalars().all()
        
        reviews.extend([
            {
                "id": review.id,
                "type": "product",
                "user_id": review.user_id,
                "username": review.user.username if review.user else "Anonymous",
                "product_id": review.product_id,
                "rating": review.rating,
                "text": review.text,
                "photos": review.photos,
                "created_at": review.created_at.isoformat()
            }
            for review in product_reviews
        ])
    
    if review_type in ["all", "seller"]:
        result = await db.execute(
            select(SellerReview)
            .options(selectinload(SellerReview.user))
            .where(SellerReview.status == 'pending')
            .order_by(desc(SellerReview.created_at))
            .offset(skip)
            .limit(limit)
        )
        seller_reviews = result.scalars().all()
        
        reviews.extend([
            {
                "id": review.id,
                "type": "seller",
                "user_id": review.user_id,
                "username": review.user.username if review.user else "Anonymous",
                "seller_id": review.seller_id,
                "rating": review.rating,
                "text": review.text,
                "created_at": review.created_at.isoformat()
            }
            for review in seller_reviews
        ])
    
    return {
        "items": reviews,
        "total": len(reviews),
        "skip": skip,
        "limit": limit
    }


@router.patch("/admin/reviews/product/{review_id}")
async def moderate_product_review(
    review_id: int,
    request: ReviewModeration,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Moderate product review."""
    result = await db.execute(
        select(ProductReview).where(ProductReview.id == review_id)
    )
    review = result.scalar_one_or_none()
    
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    review.status = request.status
    review.moderated_at = datetime.utcnow()
    review.moderated_by = current_admin.id
    
    if request.rejection_reason:
        review.rejection_reason = request.rejection_reason
    
    # Update product average rating if published
    if request.status == "published":
        result = await db.execute(
            select(func.avg(ProductReview.rating)).where(
                and_(
                    ProductReview.product_id == review.product_id,
                    ProductReview.status == 'published'
                )
            )
        )
        avg_rating = result.scalar() or 0.0
        
        # Update product rating
        result = await db.execute(
            select(Product).where(Product.id == review.product_id)
        )
        product = result.scalar_one_or_none()
        if product:
            product.rating = Decimal(str(round(float(avg_rating), 2)))
    
    await db.commit()
    
    return {
        "id": review.id,
        "status": review.status
    }


@router.patch("/admin/reviews/seller/{review_id}")
async def moderate_seller_review(
    review_id: int,
    request: ReviewModeration,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Moderate seller review."""
    result = await db.execute(
        select(SellerReview).where(SellerReview.id == review_id)
    )
    review = result.scalar_one_or_none()
    
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    review.status = request.status
    review.moderated_at = datetime.utcnow()
    review.moderated_by = current_admin.id
    
    if request.rejection_reason:
        review.rejection_reason = request.rejection_reason
    
    # Update seller average rating if published
    if request.status == "published":
        result = await db.execute(
            select(func.avg(SellerReview.rating)).where(
                and_(
                    SellerReview.seller_id == review.seller_id,
                    SellerReview.status == 'published'
                )
            )
        )
        avg_rating = result.scalar() or 0.0
        
        # Update seller rating
        result = await db.execute(
            select(Seller).where(Seller.id == review.seller_id)
        )
        seller = result.scalar_one_or_none()
        if seller:
            seller.rating = Decimal(str(round(float(avg_rating), 2)))
    
    await db.commit()
    
    return {
        "id": review.id,
        "status": review.status
    }
