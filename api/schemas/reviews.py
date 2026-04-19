"""Review and rating schemas."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, ConfigDict


class CreateReviewRequest(BaseModel):
    """Request to create a review.
    
    Validates requirement 11.10:
    - Rating: 1-5 integer
    - Review text: max 2000 characters
    """
    model_config = ConfigDict(str_strip_whitespace=True)
    
    rating: int = Field(..., ge=1, le=5, description="Rating (1-5)")
    text: Optional[str] = Field(None, max_length=2000, description="Review text (max 2000 characters)")
    photo_ids: Optional[List[int]] = Field(None, max_length=5, description="Photo IDs (max 5)")
    
    @field_validator('rating')
    @classmethod
    def validate_rating(cls, v: int) -> int:
        """Validate rating is between 1 and 5 (req 11.10)."""
        if not 1 <= v <= 5:
            raise ValueError('Rating must be between 1 and 5')
        return v
    
    @field_validator('text')
    @classmethod
    def validate_text(cls, v: Optional[str]) -> Optional[str]:
        """Validate review text length (req 11.10)."""
        if v is not None and len(v) > 2000:
            raise ValueError('Review text must not exceed 2000 characters')
        return v


class ReviewResponse(BaseModel):
    """Single review response."""
    id: int
    user_id: int
    username: str | None
    rating: int
    text: str | None
    photos: List[str]
    admin_reply: str | None
    admin_replied_at: str | None
    created_at: str


class ReviewListResponse(BaseModel):
    """Paginated review list."""
    items: List[ReviewResponse]
    total: int
    page: int
    limit: int
    average_rating: float


class ReviewReplyRequest(BaseModel):
    """Request to reply to a review."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    reply_text: str = Field(..., min_length=1, max_length=2000, description="Reply text (max 2000 characters)")


class SellerReviewResponse(BaseModel):
    """Seller review response."""
    id: int
    seller_id: int
    deal_id: int
    buyer_id: int
    buyer_username: str | None
    rating: int
    text: str | None
    status: str
    seller_reply: str | None
    seller_replied_at: str | None
    created_at: str


class SellerReviewListResponse(BaseModel):
    """Paginated seller review list."""
    items: List[SellerReviewResponse]
    total: int
    page: int
    limit: int
    average_rating: float


class ReviewModerationRequest(BaseModel):
    """Request to moderate a review (admin)."""
    status: str = Field(..., pattern="^(published|rejected)$", description="New review status")
    rejection_reason: Optional[str] = Field(None, max_length=500, description="Reason for rejection")
