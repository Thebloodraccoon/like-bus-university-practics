from pydantic import SecretStr, computed_field  # type: ignore
from pydantic_settings import BaseSettings  # type: ignore


class Settings(BaseSettings):
    # Database settings
    DATABASE_USER: str
    DATABASE_PASSWORD: SecretStr
    DATABASE_HOST: str
    DATABASE_PORT: str
    DATABASE_NAME: str

    @computed_field
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD.get_secret_value()}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"

    # Test database settings
    TEST_DATABASE_USER: str
    TEST_DATABASE_PASSWORD: SecretStr
    TEST_DATABASE_HOST: str
    TEST_DATABASE_PORT: int
    TEST_DATABASE_NAME: str

    @computed_field
    def TEST_DATABASE_URL(self) -> str:
        return f"postgresql://{self.TEST_DATABASE_USER}:{self.TEST_DATABASE_PASSWORD.get_secret_value()}@{self.TEST_DATABASE_HOST}:{self.TEST_DATABASE_PORT}/{self.TEST_DATABASE_NAME}"

    # JWT settings
    JWT_SECRET_KEY: SecretStr
    JWT_ALGORITHM: str

    # Admin credentials
    ADMIN_LOGIN: str
    ADMIN_PASSWORD: SecretStr

    # PGAdmin settings
    PGADMIN_EMAIL: str
    PGADMIN_PASSWORD: SecretStr

    # Redis settings
    HOST_REDIS: str
    PORT_REDIS: int
    DB_REDIS: int

    # Test Redis settings
    TEST_HOST_REDIS: str
    TEST_PORT_REDIS: int
    TEST_DB_REDIS: int

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "allow"}


# Initialize settings
settings = Settings()
