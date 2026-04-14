#!/usr/bin/env python3
"""Minimal migration script - just add balance column first"""
import asyncio
import sys
sys.path.insert(0, '/app')

from sqlalchemy import text
from app.db.session import session_factory

async def main():
    async with session_factory() as session:
        # Just add balance column - most critical
        await session.execute(text(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS balance NUMERIC(12, 2) NOT NULL DEFAULT 0.00"
        ))
        await session.commit()
        print("✅ Balance column added!")

asyncio.run(main())
