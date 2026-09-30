import os
from typing import Literal

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL

Environment = Literal["local", "ci", "prod"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


# NOTE: Настройки сервера
class RunConfig:
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    RELOAD: bool = False


# NOTE: Настройка приложении
class AppConfig(BaseModel):
    PROJECT_NAME: str = "Tempalte 1"
    ENVIRONMENT: Environment = "local"
    LOGLEVEL: LogLevel = "INFO"


# Настройки базы данных
class PostgresConfig(BaseModel):
    HOST: str = "localhost"
    PORT: int = 5432
    USERNAME: str = "postgresql"
    PASSWORD: str = "postgresql"
    DATABASE: str = "postgresql"
    DRIVER: str = "postgresql+asyncpg"

    AUTOFLUSH: bool = True
    EXPIRE_ON_COMMIT: bool = False

    def sqlalchemy_url(self) -> URL | str:
        url = URL.create(
            drivername=self.DRIVER,
            host=self.HOST,
            port=self.PORT,
            username=self.USERNAME,
            password=self.PASSWORD,
            database=self.DATABASE,
        )

        return url


class Settings(BaseSettings):
    run: RunConfig = RunConfig()
    app: AppConfig = AppConfig()
    db: PostgresConfig = PostgresConfig()

    model_config = SettingsConfigDict(
        env_file=os.getenv("ENV_FILE", ".env"),
        env_nested_delimiter="__",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
