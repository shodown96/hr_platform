from enum import Enum

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, computed_field


class AppSettings(BaseSettings):
    APP_NAME: str = "FastAPI app"
    APP_DESCRIPTION: str | None = None
    APP_VERSION: str | None = None
    LICENSE_NAME: str | None = None
    CONTACT_NAME: str | None = None
    CONTACT_EMAIL: str | None = None


class CryptSettings(BaseSettings):
    # JWT for inter-service communication, should be the same in all services
    SECRET_KEY: SecretStr = SecretStr("secret-key")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7


class DatabaseSettings(BaseSettings):
    pass


class SQLiteSettings(BaseSettings):
    SQLITE_FILENAME: str = "boilerplate.db"
    SQLITE_SYNC_PREFIX: str = "sqlite:///"
    SQLITE_ASYNC_PREFIX: str = "sqlite+aiosqlite:///"
    CONNECT_ARGS: dict = {"check_same_thread": False}

    @computed_field
    @property
    def SQLITE_URL(self) -> str:
        return f"{self.SQLITE_SYNC_PREFIX}@{self.SQLITE_FILENAME}"

    @computed_field
    @property
    def SQLITE_ASYNC_URL(self) -> str:
        return f"{self.SQLITE_ASYNC_PREFIX}@{self.SQLITE_FILENAME}"


class MySQLSettings(DatabaseSettings):
    MYSQL_USER: str = "username"
    MYSQL_PASSWORD: str = "password"
    MYSQL_SERVER: str = "localhost"
    MYSQL_PORT: int = 5432
    MYSQL_DB: str = "dbname"
    MYSQL_SYNC_PREFIX: str = "mysql://"
    MYSQL_ASYNC_PREFIX: str = "mysql+aiomysql://"
    MYSQL_URL: str | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def MYSQL_URI(self) -> str:
        credentials = f"{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
        location = f"{self.MYSQL_SERVER}:{self.MYSQL_PORT}/{self.MYSQL_DB}"
        return f"{credentials}@{location}"


class PostgresSettings(DatabaseSettings):
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "hr_payroll"
    POSTGRES_SYNC_PREFIX: str = "postgresql://"
    POSTGRES_ASYNC_PREFIX: str = "postgresql+asyncpg://"
    POSTGRES_URL: str | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def POSTGRES_URI(self) -> str:
        credentials = f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
        location = f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        return f"{credentials}@{location}"


class SampleUserSettings(BaseSettings):
    ADMIN_NAME: str = "admin"
    ADMIN_EMAIL: str = "admin@admin.com"
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "!Ch4ng3Th1sP4ssW0rd!"
    
    HR_NAME: str = "hr manager"
    HR_EMAIL: str = "hr@company.com"
    HR_USERNAME: str = "hrmanager"
    HR_PASSWORD: str = "!Ch4ng3Th1sP4ssW0rd!"
    
    USER_NAME: str = "user"
    USER_EMAIL: str = "user@user.com"
    USER_USERNAME: str = "user"
    USER_PASSWORD: str = "!Ch4ng3Th1sP4ssW0rd!"
    
    EMPLOYEE_FIRST_NAME: str = "emp"
    EMPLOYEE_LAST_NAME: str = "emp"
    EMPLOYEE_EMAIL: str = "emp@employee.com"
    EMPLOYEE_USERNAME: str = "emp"
    EMPLOYEE_PASSWORD: str = "!Ch4ng3Th1sP4ssW0rd!"
    EMPLOYEE_CODE: str = "EMP001"


class TestSettings(BaseSettings):  # ... is used like pass
    # Test database URL (async SQLite in-memory)
    TEST_SQLALCHEMY_DATABASE_URL: str = (
        "sqlite+aiosqlite:///./test.db"  # "sqlite+aiosqlite:///:memory:"
    )
    TEST_CONNECT_ARGS: dict = {"check_same_thread": False}


class RedisCacheSettings(BaseSettings):
    REDIS_CACHE_HOST: str = "localhost"
    REDIS_CACHE_PORT: int = 6379

    @computed_field  # type: ignore[prop-decorator]
    @property
    def REDIS_CACHE_URL(self) -> str:
        return f"redis://{self.REDIS_CACHE_HOST}:{self.REDIS_CACHE_PORT}"


class ClientSideCacheSettings(BaseSettings):
    CLIENT_CACHE_MAX_AGE: int = 60


class RedisQueueSettings(BaseSettings):
    REDIS_QUEUE_HOST: str = "localhost"
    REDIS_QUEUE_PORT: int = 6379


class EnvironmentOption(str, Enum):
    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"


class EnvironmentSettings(BaseSettings):
    ENVIRONMENT: EnvironmentOption = EnvironmentOption.LOCAL


class CORSSettings(BaseSettings):
    CORS_ORIGINS: list[str] = ["*"]
    CORS_METHODS: list[str] = ["*"]
    CORS_HEADERS: list[str] = ["*"]


class RabbitMQSettings(BaseSettings):
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"


class MicroserviceSettings(BaseSettings):
    # Auth Service
    AUTH_SERVICE_URL: str = "http://localhost:8000"


class Settings(
    AppSettings,
    SQLiteSettings,
    PostgresSettings,
    CryptSettings,
    SampleUserSettings,
    TestSettings,
    RedisCacheSettings,
    ClientSideCacheSettings,
    RedisQueueSettings,
    EnvironmentSettings,
    CORSSettings,
    RabbitMQSettings,
    MicroserviceSettings,
):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)
    # env_file=os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "..", ".env"),


settings = Settings()
