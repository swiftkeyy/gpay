from functools import lru_cache
from decimal import Decimal
from urllib.parse import urlparse

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: str = Field(..., alias="BOT_TOKEN")
    bot_username: str = Field("", alias="BOT_USERNAME")

    app_env: str = Field("dev", alias="APP_ENV")
    log_level: str = Field("INFO", alias="LOG_LEVEL")

    # Railway-style DATABASE_URL (optional, takes precedence)
    database_url_raw: str | None = Field(None, alias="DATABASE_URL")
    
    # Individual database fields (optional, used if DATABASE_URL not provided)
    db_host: str | None = Field(None, alias="POSTGRES_HOST")
    db_port: int = Field(5432, alias="POSTGRES_PORT")
    db_name: str | None = Field(None, alias="POSTGRES_DB")
    db_user: str | None = Field(None, alias="POSTGRES_USER")
    db_password: str | None = Field(None, alias="POSTGRES_PASSWORD")
    db_ssl_mode: str = Field("require", alias="POSTGRES_SSL_MODE")

    # Railway-style REDIS_URL (optional, takes precedence)
    redis_url_raw: str | None = Field(None, alias="REDIS_URL")
    
    # Individual Redis fields (optional, used if REDIS_URL not provided)
    redis_host: str | None = Field(None, alias="REDIS_HOST")
    redis_port: int = Field(6379, alias="REDIS_PORT")
    redis_db: int = Field(0, alias="REDIS_DB")
    redis_password: str | None = Field(None, alias="REDIS_PASSWORD")
    redis_ssl: bool = Field(True, alias="REDIS_SSL")

    @field_validator("database_url_raw", mode="after")
    @classmethod
    def parse_database_url(cls, v, info):
        """Parse DATABASE_URL and populate individual fields if provided"""
        if v:
            parsed = urlparse(v)
            # Store parsed values for later use
            info.data["_db_parsed"] = {
                "host": parsed.hostname,
                "port": parsed.port or 5432,
                "name": parsed.path.lstrip("/"),
                "user": parsed.username,
                "password": parsed.password,
            }
        return v

    @field_validator("redis_url_raw", mode="after")
    @classmethod
    def parse_redis_url(cls, v, info):
        """Parse REDIS_URL and populate individual fields if provided"""
        if v:
            # Railway sometimes provides malformed URLs like "https://redis://..."
            # Clean it up by removing any leading protocol before redis://
            cleaned_url = v
            if "redis://" in v or "rediss://" in v:
                # Extract the redis:// or rediss:// part onwards
                if "redis://" in v:
                    cleaned_url = "redis://" + v.split("redis://", 1)[1]
                elif "rediss://" in v:
                    cleaned_url = "rediss://" + v.split("rediss://", 1)[1]
            
            parsed = urlparse(cleaned_url)
            # Store parsed values for later use
            db_num = 0
            if parsed.path and parsed.path != "/":
                try:
                    db_num = int(parsed.path.lstrip("/"))
                except (ValueError, AttributeError):
                    db_num = 0
            
            info.data["_redis_parsed"] = {
                "host": parsed.hostname,
                "port": parsed.port or 6379,
                "db": db_num,
                "password": parsed.password,
                "ssl": parsed.scheme == "rediss",
            }
        return v

    shop_name: str = Field("Game Pay", alias="SHOP_NAME")
    super_admin_tg_id: int = Field(0, alias="SUPER_ADMIN_TG_ID")
    second_admin_tg_id: int = Field(0, alias="SECOND_ADMIN_TG_ID")
    
    # JWT settings
    jwt_secret_key: str = Field("your-secret-key-change-in-production", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")
    jwt_expiration_minutes: int = Field(43200, alias="JWT_EXPIRATION_MINUTES")  # 30 days
    
    # WebApp URL for Mini App
    webapp_url: str = Field("https://gpay-production.up.railway.app", alias="WEBAPP_URL")
    
    # CORS settings
    cors_origins: str = Field("*", alias="CORS_ORIGINS")

    telegram_stars_enabled: bool = Field(True, alias="TELEGRAM_STARS_ENABLED")
    # 1 рубль = 0.5 звезды (или 1 звезда = 2 рубля) - стандартный курс Telegram
    telegram_stars_per_rub: Decimal = Field(Decimal("0.5"), alias="TELEGRAM_STARS_PER_RUB")

    cryptobot_enabled: bool = Field(True, alias="CRYPTOBOT_ENABLED")
    cryptobot_api_token: str | None = Field(None, alias="CRYPTOBOT_API_TOKEN")
    # Исправлен URL API - старый pay.crypt.bot больше не работает
    cryptobot_api_base_url: str = Field("https://testnet-pay.crypt.bot/api", alias="CRYPTOBOT_API_BASE_URL")
    cryptobot_currency_type: str = Field("fiat", alias="CRYPTOBOT_CURRENCY_TYPE")
    cryptobot_fiat: str = Field("RUB", alias="CRYPTOBOT_FIAT")
    cryptobot_asset: str = Field("USDT", alias="CRYPTOBOT_ASSET")
    cryptobot_accepted_assets: str = Field(
        "USDT,TON,BTC,ETH,LTC,BNB,TRX,USDC",
        alias="CRYPTOBOT_ACCEPTED_ASSETS",
    )
    cryptobot_expires_in: int = Field(3600, alias="CRYPTOBOT_EXPIRES_IN")
    cryptobot_allow_comments: bool = Field(False, alias="CRYPTOBOT_ALLOW_COMMENTS")
    cryptobot_allow_anonymous: bool = Field(False, alias="CRYPTOBOT_ALLOW_ANONYMOUS")

    @property
    def database_url(self) -> str:
        # Use DATABASE_URL if provided (Railway style)
        if self.database_url_raw:
            # Railway sometimes provides malformed URLs like "https://postgres://..."
            # Clean it up by removing any leading protocol before postgres://
            cleaned_url = self.database_url_raw
            if "postgres://" in self.database_url_raw or "postgresql://" in self.database_url_raw:
                # Extract the postgres:// or postgresql:// part onwards
                if "postgres://" in self.database_url_raw:
                    cleaned_url = "postgres://" + self.database_url_raw.split("postgres://", 1)[1]
                elif "postgresql://" in self.database_url_raw:
                    cleaned_url = "postgresql://" + self.database_url_raw.split("postgresql://", 1)[1]
            
            # Convert postgres:// to postgresql+asyncpg://
            url = cleaned_url.replace("postgres://", "postgresql+asyncpg://", 1)
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            
            # Ensure SSL mode is appended
            if "?" not in url:
                url += f"?ssl={self.db_ssl_mode}"
            elif "ssl=" not in url:
                url += f"&ssl={self.db_ssl_mode}"
            return url
        
        # Otherwise use individual fields
        if not all([self.db_host, self.db_name, self.db_user, self.db_password]):
            raise ValueError("Either DATABASE_URL or individual database fields must be provided")
        
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
            f"?ssl={self.db_ssl_mode}"
        )

    @property
    def sync_database_url(self) -> str:
        # Use DATABASE_URL if provided (Railway style)
        if self.database_url_raw:
            # Railway sometimes provides malformed URLs like "https://postgres://..."
            # Clean it up by removing any leading protocol before postgres://
            cleaned_url = self.database_url_raw
            if "postgres://" in self.database_url_raw or "postgresql://" in self.database_url_raw:
                # Extract the postgres:// or postgresql:// part onwards
                if "postgres://" in self.database_url_raw:
                    cleaned_url = "postgres://" + self.database_url_raw.split("postgres://", 1)[1]
                elif "postgresql://" in self.database_url_raw:
                    cleaned_url = "postgresql://" + self.database_url_raw.split("postgresql://", 1)[1]
            
            # Convert postgres:// to postgresql+psycopg://
            url = cleaned_url.replace("postgres://", "postgresql+psycopg://", 1)
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
            
            # Ensure SSL mode is appended
            if "?" not in url:
                url += f"?sslmode={self.db_ssl_mode}"
            elif "sslmode=" not in url:
                url += f"&sslmode={self.db_ssl_mode}"
            return url
        
        # Otherwise use individual fields
        if not all([self.db_host, self.db_name, self.db_user, self.db_password]):
            raise ValueError("Either DATABASE_URL or individual database fields must be provided")
        
        return (
            f"postgresql+psycopg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
            f"?sslmode={self.db_ssl_mode}"
        )

    @property
    def redis_url(self) -> str:
        # Use REDIS_URL if provided (Railway style)
        if self.redis_url_raw:
            # Railway sometimes provides malformed URLs like "https://redis://..."
            # Clean it up by removing any leading protocol before redis://
            cleaned_url = self.redis_url_raw
            if "redis://" in self.redis_url_raw or "rediss://" in self.redis_url_raw:
                # Extract the redis:// or rediss:// part onwards
                if "redis://" in self.redis_url_raw:
                    cleaned_url = "redis://" + self.redis_url_raw.split("redis://", 1)[1]
                elif "rediss://" in self.redis_url_raw:
                    cleaned_url = "rediss://" + self.redis_url_raw.split("rediss://", 1)[1]
            return cleaned_url
        
        # Otherwise use individual fields
        if not self.redis_host:
            raise ValueError("Either REDIS_URL or REDIS_HOST must be provided")
        
        scheme = "rediss" if self.redis_ssl else "redis"
        if self.redis_password:
            return f"{scheme}://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"{scheme}://{self.redis_host}:{self.redis_port}/{self.redis_db}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
