"""Authentication service for Telegram Mini App.

This service handles Telegram initData validation using HMAC-SHA256
to ensure requests are coming from legitimate Telegram users.

Requirements: 1.1, 1.2, 1.3, 29.1
"""
from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from typing import Any
from urllib.parse import parse_qsl

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.repositories.users import UserRepository


class AuthService:
    """Service for handling Telegram authentication and user management."""

    def __init__(self, session: AsyncSession, bot_token: str):
        """Initialize auth service.
        
        Args:
            session: Database session
            bot_token: Telegram bot token for HMAC validation
        """
        self.session = session
        self.bot_token = bot_token
        self.user_repo = UserRepository(session)

    def validate_init_data(self, init_data: str) -> dict[str, Any] | None:
        """Validate Telegram initData using HMAC-SHA256.
        
        This method implements the Telegram WebApp authentication algorithm:
        1. Parse the initData query string
        2. Extract the hash parameter
        3. Create a data check string from sorted parameters
        4. Calculate secret key using HMAC-SHA256(bot_token, "WebAppData")
        5. Calculate hash using HMAC-SHA256(secret_key, data_check_string)
        6. Compare calculated hash with provided hash
        
        Requirements: 1.2, 29.1
        
        Args:
            init_data: The initData string from Telegram WebApp SDK
            
        Returns:
            Parsed user data dict if validation succeeds, None otherwise
        """
        try:
            # Parse query string into dict
            parsed_data = dict(parse_qsl(init_data))
            hash_value = parsed_data.pop("hash", None)
            
            if not hash_value:
                return None
            
            # Create data check string (sorted key=value pairs joined by newline)
            data_check_arr = [f"{k}={v}" for k, v in sorted(parsed_data.items())]
            data_check_string = "\n".join(data_check_arr)
            
            # Calculate secret key: HMAC-SHA256("WebAppData", bot_token)
            secret_key = hmac.new(
                "WebAppData".encode(),
                self.bot_token.encode(),
                hashlib.sha256
            ).digest()
            
            # Calculate hash: HMAC-SHA256(secret_key, data_check_string)
            calculated_hash = hmac.new(
                secret_key,
                data_check_string.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Validate hash matches
            if calculated_hash != hash_value:
                return None
            
            return parsed_data
        except Exception:
            # Any parsing or validation error returns None
            return None

    async def authenticate_user(
        self, 
        init_data: str,
        referral_code: str | None = None
    ) -> tuple[User, bool]:
        """Authenticate user via Telegram initData and create/retrieve user.
        
        Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.8
        
        Args:
            init_data: The initData string from Telegram WebApp SDK
            referral_code: Optional referral code from start parameter
            
        Returns:
            Tuple of (User object, is_new_user boolean)
            
        Raises:
            ValueError: If initData validation fails or user data is invalid
        """
        # Validate initData hash (Requirement 1.2)
        user_data = self.validate_init_data(init_data)
        
        if not user_data:
            # Requirement 1.3: Return 401 for invalid hash
            raise ValueError("Invalid authentication data")
        
        # Extract user info from validated data
        user_json = user_data.get("user")
        if not user_json:
            raise ValueError("User data not found in initData")
        
        try:
            user_info = json.loads(user_json)
        except json.JSONDecodeError:
            raise ValueError("Invalid user data format")
        
        telegram_id = user_info.get("id")
        username = user_info.get("username")
        first_name = user_info.get("first_name")
        
        if not telegram_id:
            raise ValueError("Telegram ID not found")
        
        # Get existing user or create new one (Requirement 1.4, 1.5)
        user = await self.user_repo.get_by_telegram_id(telegram_id)
        
        if user:
            return user, False
        
        # Create new user (Requirement 1.4)
        user = await self._create_new_user(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            referral_code=referral_code
        )
        
        return user, True

    async def _create_new_user(
        self,
        telegram_id: int,
        username: str | None,
        first_name: str | None,
        referral_code: str | None
    ) -> User:
        """Create a new user with zero balance and unique referral code.
        
        Requirements: 1.4, 1.8, 14.1, 14.2
        
        Args:
            telegram_id: Telegram user ID
            username: Telegram username (optional)
            first_name: Telegram first name (optional)
            referral_code: Referral code if user was referred (optional)
            
        Returns:
            Created User object
        """
        # Generate unique referral code (8-12 characters alphanumeric)
        # Requirement 14.1: Generate unique 8-12 character alphanumeric referral code
        user_referral_code = await self._generate_unique_referral_code()
        
        # Requirement 1.4: Create user with zero balance
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            balance=0.00,
            referral_code=user_referral_code
        )
        
        # Handle referral tracking (Requirement 1.8, 14.2)
        if referral_code:
            referrer = await self.user_repo.get_by_referral_code(referral_code)
            if referrer:
                # Requirement 14.2: Associate new user with referrer
                user.referred_by_user_id = referrer.id
        
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        
        # Create Referral record if user was referred
        # This tracks the referral relationship for reward processing
        if referral_code and user.referred_by_user_id:
            from app.models import Referral
            referral = Referral(
                referrer_user_id=user.referred_by_user_id,
                referred_user_id=user.id,
                referral_code=referral_code
            )
            self.session.add(referral)
            await self.session.commit()
        
        return user
    
    async def _generate_unique_referral_code(self) -> str:
        """Generate a unique referral code.
        
        Requirement 14.1, 14.6: Ensure referral code is unique across all users
        
        Returns:
            Unique 8-12 character alphanumeric referral code
        """
        max_attempts = 10
        for _ in range(max_attempts):
            # Generate 8-12 character alphanumeric code
            code = secrets.token_urlsafe(9)[:12]  # Generate slightly longer and trim
            
            # Check if code is unique
            existing_user = await self.user_repo.get_by_referral_code(code)
            if not existing_user:
                return code
        
        # Fallback: use timestamp-based code if random generation fails
        import time
        return f"ref{int(time.time())}"[:12]

    def generate_access_token(self, user: User) -> str:
        """Generate access token for authenticated user.
        
        Note: This is a simplified implementation. In production,
        use proper JWT tokens with expiration and signing.
        
        Requirements: 1.6
        
        Args:
            user: Authenticated user
            
        Returns:
            Access token string
        """
        # Simplified token format: user_{id}_{telegram_id}
        # TODO: Replace with proper JWT implementation
        return f"user_{user.id}_{user.telegram_id}"
