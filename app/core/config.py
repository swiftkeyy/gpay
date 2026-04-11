from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: str = Field(..., alias="BOT_TOKEN")

    db_host: str = Field("db", alias="POSTGRES_HOST")
    db_port: int = Field(5432, alias="POSTGRES_PORT")
    db_name: str = Field("game_pay", alias="POSTGRES_DB")
    db_user: str = Field("game_pay", alias="POSTGRES_USER")
    db_password: str = Field("game_pay", alias="POSTGRES_PASSWORD")

    redis_host: str = Field("redis", alias="REDIS_HOST")
    redis_port: int = Field(6379, alias="REDIS_PORT")
    redis_db: int = Field(0, alias="REDIS_DB")

    shop_name: str = Field("Game Pay", alias="SHOP_NAME")
    super_admin_tg_id: int = Field(0, alias="SUPER_ADMIN_TG_ID")
    second_admin_tg_id: int = Field(0, alias="SECOND_ADMIN_TG_ID")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def sync_database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()