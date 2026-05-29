from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "crm_music_school"
    db_user: str = "postgres"
    db_password: str = "root"

    # JWT
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24

    # Первый администратор (создаётся при старте)
    first_admin_email: str = "admin@crm.com"
    first_admin_password: str = "admin12345"


    app_name: str = "CRM Music School"
    debug: bool = True

    @property
    def database_url(self) -> str:
        """URL для async-подключения через asyncpg."""
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )
    # Приложение
    @property
    def database_url_sync(self) -> str:
        """Sync URL для Alembic (он работает синхронно)."""
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()