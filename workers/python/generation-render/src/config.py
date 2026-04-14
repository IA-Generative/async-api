from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    BROKER_URL: str
    IN_QUEUE_NAME: str
    OUT_QUEUE_NAME: str
    WORKER_CONCURRENCY: int = 3
    HEALTH_CHECK_HOST: str = "0.0.0.0"  # noqa: S104
    HEALTH_CHECK_PORT: int = 8083
    LOG_LEVEL: str = "INFO"

    S3_ENDPOINT_URL: str
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    S3_REGION_NAME: str = "fr-par"
    S3_BUCKET_NAME: str


settings = Settings()
