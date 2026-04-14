from functools import lru_cache
from decimal import Decimal

from pydantic import Field
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

    db_host: str = Field(..., alias="POSTGRES_HOST")
    db_port: int = Field(5432, alias="POSTGRES_PORT")
    db_name: str = Field(..., alias="POSTGRES_DB")
    db_user: str = Field(..., alias="POSTGRES_USER")
    db_password: str = Field(..., alias="POSTGRES_PASSWORD")
    db_ssl_mode: str = Field("require", alias="POSTGRES_SSL_MODE")

    redis_host: str = Field(..., alias="REDIS_HOST")
    redis_port: int = Field(6379, alias="REDIS_PORT")
    redis_db: int = Field(0, alias="REDIS_DB")
    redis_password: str | None = Field(None, alias="REDIS_PASSWORD")
    redis_ssl: bool = Field(True, alias="REDIS_SSL")

    shop_name: str = Field("Game Pay", alias="SHOP_NAME")
    super_admin_tg_id: int = Field(0, alias="SUPER_ADMIN_TG_ID")
    second_admin_tg_id: int = Field(0, alias="SECOND_ADMIN_TG_ID")

    telegram_stars_enabled: bool = Field(True, alias="TELEGRAM_STARS_ENABLED")
    telegram_stars_per_rub: Decimal = Field(Decimal("1"), alias="TELEGRAM_STARS_PER_RUB")

    cryptobot_enabled: bool = Field(True, alias="CRYPTOBOT_ENABLED")
    cryptobot_api_token: str | None = Field(None, alias="CRYPTOBOT_API_TOKEN")
    cryptobot_api_base_url: str = Field("https://pay.crypt.bot/api", alias="CRYPTOBOT_API_BASE_URL")
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
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
            f"?ssl={self.db_ssl_mode}"
        )

    @property
    def sync_database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
            f"?sslmode={self.db_ssl_mode}"
        )

    @property
    def redis_url(self) -> str:
        scheme = "rediss" if self.redis_ssl else "redis"
        if self.redis_password:
            return f"{scheme}://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"{scheme}://{self.redis_host}:{self.redis_port}/{self.redis_db}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
