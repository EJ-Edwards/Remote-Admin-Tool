from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://sentinel:sentinel@localhost:5432/sentinel_link"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7
    auto_approve_agents: bool = True
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    heartbeat_offline_minutes: int = 5

    class Config:
        env_file = ".env"


settings = Settings()
