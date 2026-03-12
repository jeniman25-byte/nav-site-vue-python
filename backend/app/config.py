from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    secret_key: str = "replace-this-with-a-long-random-string"
    token_expire_minutes: int = 120
    algorithm: str = "HS256"
    database_url: str = "sqlite:///./nav_site.db"
    cors_origins: str = "http://127.0.0.1:5173,http://localhost:5173"
    default_admin_username: str = "admin"
    default_admin_password: str = "ChangeMe123!"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

