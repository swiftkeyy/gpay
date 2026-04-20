"""Reviews router."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional, List
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from pydantic import BaseModel, Field, validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.entities import (
    User, 
    Deal, 
    Order, 
    OrderItem,
    Review as ProductReview, 
    SellerReview, 
    Seller, 
    Product
)
from app.models.enums import ReviewStatus, OrderStatus, DealStatus
from api.dependencies.auth import get_current_user, get_current_admin

router = APIRouter()
logger = logging.getLogger(__name__)


# Pydantic models
class ProductReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    text: Optional[str] = Field(None, max_length=2000, description="Review text (max 2000 characters)")
    # Note: Photo support requires database schema update (photos field or review_photos table)
    # photos: Optional[List[int]] = Field(None, max_items=5, description="List of media file IDs (max 5)")


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
                ProductReview.status == ReviewStatus.PUBLISHED
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
                ProductReview.status == ReviewStatus.PUBLISHED
            )
        )
    )
    avg_rating = result.scalar() or 0.0
    
    # Count total reviews
    result = await db.execute(
        select(func.count(ProductReview.id)).where(
            and_(
                ProductReview.product_id == product_id,
                ProductReview.status == ReviewStatus.PUBLISHED
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


@router.post("/orders/{order_id}/review", status_code=status.HTTP_201_CREATED)
async def create_product_review(
    order_id: int,
    request: ProductReviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create product review for a completed order.
    
    Requirements implemented:
    - 11.1: POST /api/v1/orders/{id}/review endpoint
    - 11.3: Validate rating (1-5) and text (max 2000 chars)
    - 11.10: Set status to pending (HIDDEN) for moderation
    
    Note: Photo support (11.4) requires database schema update.
    """
    # Get order with items
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Order not found"
        )
    
    # Check if user is the buyer
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You can only review your own orders"
        )
    
    # Check if order is completed
    if order.status != OrderStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Cannot review order with status '{order.status.value}'. Order must be completed."
        )
    
    # Check if order has items
    if not order.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order has no items to review"
        )
    
    # Get the first product from order items (for now, assuming one product per order)
    # TODO: In future, support multiple reviews per order (one per product)
    first_item = order.items[0]
    product_id = first_item.product_id
    
    # Check if review already exists for this order
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="You have already reviewed this order"
        )
    
    # Create review with status HIDDEN (pending moderation)
    review = ProductReview(
        user_id=current_user.id,
        order_id=order_id,
        product_id=product_id,
        rating=request.rating,
        text=request.text,
        status=ReviewStatus.HIDDEN  # HIDDEN serves as "pending" status
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)
    
    logger.info(
        f"Product review created: review_id={review.id}, order_id={order_id}, "
        f"user_id={current_user.id}, rating={request.rating}"
    )
    
    return {
        "review_id": review.id,
        "order_id": order_id,
        "product_id": product_id,
        "rating": review.rating,
        "text": review.text,
        "status": "pending",
        "message": "Review submitted for moderation",
        "created_at": review.created_at.isoformat()
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
        .options(selectinload(SellerReview.buyer))
        .where(
            and_(
                SellerReview.seller_id == seller_id,
                SellerReview.status == ReviewStatus.PUBLISHED
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
                SellerReview.status == ReviewStatus.PUBLISHED
            )
        )
    )
    avg_rating = result.scalar() or 0.0
    
    # Count total reviews
    result = await db.execute(
        select(func.count(SellerReview.id)).where(
            and_(
                SellerReview.seller_id == seller_id,
                SellerReview.status == ReviewStatus.PUBLISHED
            )
        )
    )
    total_reviews = result.scalar()
    
    return {
        "items": [
            {
                "id": review.id,
                "buyer_id": review.buyer_id,
                "username": review.buyer.username if review.buyer else "Anonymous",
                "rating": review.rating,
                "text": review.text,
                "reply_text": review.seller_reply,
                "created_at": review.created_at.isoformat()
            }
            for review in reviews
        ],
        "total": total_reviews,
        "average_rating": round(float(avg_rating), 2),
        "skip": skip,
        "limit": limit
    }


@router.post("/deals/{deal_id}/review", status_code=status.HTTP_201_CREATED)
async def create_seller_review(
    deal_id: int,
    request: SellerReviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create seller review for a completed deal.
    
    Requirements implemented:
    - 11.2: POST /api/v1/deals/{id}/review endpoint
    - 11.4: Validate rating (1-5) and text (max 2000 chars)
    - Set status to pending for admin moderation
    """
    # Get deal
    result = await db.execute(
        select(Deal).where(Deal.id == deal_id)
    )
    deal = result.scalar_one_or_none()
    
    if not deal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal not found"
        )
    
    # Check if user is the buyer
    if deal.buyer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only review deals where you are the buyer"
        )
    
    # Check if deal is completed
    if deal.status != DealStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot review deal with status '{deal.status.value}'. Deal must be completed."
        )
    
    # Check if review already exists for this deal
    result = await db.execute(
        select(SellerReview).where(
            and_(
                SellerReview.deal_id == deal_id,
                SellerReview.buyer_id == current_user.id
            )
        )
    )
    existing_review = result.scalar_one_or_none()
    
    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already reviewed this deal"
        )
    
    # Create review with status HIDDEN (pending moderation)
    # Note: Using HIDDEN as "pending" status per requirement 11.4
    review = SellerReview(
        buyer_id=current_user.id,
        deal_id=deal_id,
        seller_id=deal.seller_id,
        rating=request.rating,
        text=request.text,
        status=ReviewStatus.HIDDEN  # HIDDEN serves as "pending" status
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)
    
    logger.info(
        f"Seller review created: review_id={review.id}, deal_id={deal_id}, "
        f"buyer_id={current_user.id}, seller_id={deal.seller_id}, rating={request.rating}"
    )
    
    return {
        "review_id": review.id,
        "deal_id": deal_id,
        "seller_id": deal.seller_id,
        "rating": review.rating,
        "text": review.text,
        "status": "pending",
        "message": "Review submitted for moderation",
        "created_at": review.created_at.isoformat()
    }


# Review replies (seller can reply to their reviews)
@router.post("/reviews/{review_id}/reply")
async def reply_to_review(
    review_id: int,
    request: ReviewReply,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Reply to a review (product or seller review).
    
    Requirements implemented:
    - 11.6: POST /api/v1/reviews/{id}/reply endpoint for sellers
    
    Sellers can reply to reviews of their products or their seller profile.
    """
    # Try to find product review first
    result = await db.execute(
        select(ProductReview).options(selectinload(ProductReview.order)).where(ProductReview.id == review_id)
    )
    product_review = result.scalar_one_or_none()
    
    if product_review:
        # Get seller from order
        result = await db.execute(
            select(Deal).where(Deal.order_id == product_review.order_id)
        )
        deal = result.scalar_one_or_none()
        
        if not deal:
            raise HTTPException(status_code=404, detail="Deal not found for this review")
        
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
            raise HTTPException(status_code=403, detail="You can only reply to reviews of your products")
        
        # Check if already replied
        if product_review.reply_text:
            raise HTTPException(status_code=400, detail="You have already replied to this review")
        
        # Add reply
        product_review.reply_text = request.reply_text
        product_review.replied_at = datetime.utcnow()
        
        await db.commit()
        
        logger.info(
            f"Product review reply added: review_id={review_id}, seller_id={seller.id}"
        )
        
        return {
            "message": "Reply added successfully",
            "review_id": review_id,
            "reply_text": request.reply_text
        }
    
    # Try to find seller review
    result = await db.execute(
        select(SellerReview).where(SellerReview.id == review_id)
    )
    seller_review = result.scalar_one_or_none()
    
    if seller_review:
        # Check if user is the seller
        result = await db.execute(
            select(Seller).where(
                and_(
                    Seller.id == seller_review.seller_id,
                    Seller.user_id == current_user.id
                )
            )
        )
        seller = result.scalar_one_or_none()
        
        if not seller:
            raise HTTPException(status_code=403, detail="You can only reply to your own seller reviews")
        
        # Check if already replied
        if seller_review.seller_reply:
            raise HTTPException(status_code=400, detail="You have already replied to this review")
        
        # Add reply
        seller_review.seller_reply = request.reply_text
        seller_review.seller_replied_at = datetime.utcnow()
        
        await db.commit()
        
        logger.info(
            f"Seller review reply added: review_id={review_id}, seller_id={seller.id}"
        )
        
        return {
            "message": "Reply added successfully",
            "review_id": review_id,
            "reply_text": request.reply_text
        }
    
    # Review not found
    raise HTTPException(status_code=404, detail="Review not found")


@router.post("/reviews/seller/{review_id}/reply")
async def reply_to_seller_review(
    review_id: int,
    request: ReviewReply,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Reply to seller review (deprecated - use /reviews/{id}/reply instead)."""
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
    if review.seller_reply:
        raise HTTPException(status_code=400, detail="Already replied")
    
    # Add reply
    review.seller_reply = request.reply_text
    review.seller_replied_at = datetime.utcnow()
    
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
            .where(ProductReview.status == ReviewStatus.HIDDEN)
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
            .options(selectinload(SellerReview.buyer))
            .where(SellerReview.status == ReviewStatus.HIDDEN)
            .order_by(desc(SellerReview.created_at))
            .offset(skip)
            .limit(limit)
        )
        seller_reviews = result.scalars().all()
        
        reviews.extend([
            {
                "id": review.id,
                "type": "seller",
                "buyer_id": review.buyer_id,
                "username": review.buyer.username if review.buyer else "Anonymous",
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
    
    # Convert string status to ReviewStatus enum
    if request.status == "published":
        review.status = ReviewStatus.PUBLISHED
    elif request.status == "rejected":
        review.status = ReviewStatus.REJECTED
    else:
        raise HTTPException(status_code=400, detail="Invalid status. Must be 'published' or 'rejected'")
    
    review.moderated_at = datetime.utcnow()
    review.moderated_by_admin_id = current_admin.id
    
    if request.rejection_reason:
        review.rejection_reason = request.rejection_reason
    
    # Update product average rating if published
    if request.status == "published":
        result = await db.execute(
            select(func.avg(ProductReview.rating)).where(
                and_(
                    ProductReview.product_id == review.product_id,
                    ProductReview.status == ReviewStatus.PUBLISHED
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
    
    logger.info(
        f"Product review moderated: review_id={review.id}, status={request.status}, "
        f"admin_id={current_admin.id}"
    )
    
    return {
        "id": review.id,
        "status": request.status
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
    
    # Convert string status to ReviewStatus enum
    if request.status == "published":
        review.status = ReviewStatus.PUBLISHED
    elif request.status == "rejected":
        review.status = ReviewStatus.REJECTED
    else:
        raise HTTPException(status_code=400, detail="Invalid status. Must be 'published' or 'rejected'")
    
    # Update seller average rating if published
    if request.status == "published":
        result = await db.execute(
            select(func.avg(SellerReview.rating)).where(
                and_(
                    SellerReview.seller_id == review.seller_id,
                    SellerReview.status == ReviewStatus.PUBLISHED
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
    
    logger.info(
        f"Seller review moderated: review_id={review.id}, status={request.status}, "
        f"admin_id={current_admin.id}"
    )
    
    return {
        "id": review.id,
        "status": request.status
    }
