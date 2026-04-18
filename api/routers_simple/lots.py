"""Lots router - stub for frontend compatibility."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/lots")
async def get_lots():
    """Get lots - stub endpoint."""
    return {
        "items": [],
        "total": 0,
        "page": 1,
        "limit": 20
    }
