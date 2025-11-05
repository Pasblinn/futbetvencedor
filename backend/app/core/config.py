from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Football Analytics API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "football_user"
    POSTGRES_PASSWORD: str = "football_pass"
    POSTGRES_DB: str = "football_analytics"
    POSTGRES_PORT: str = "5432"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # API Keys
    FOOTBALL_DATA_API_KEY: str = ""
    ODDS_API_KEY: str = ""
    WEATHER_API_KEY: str = ""
    API_SPORTS_KEY: str = ""
    FOOTYSTATS_API_KEY: str = ""

    # Security
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # ML Model paths
    MODEL_PATH: str = "models/"

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 100

    # Development mode
    DEV_MODE_NO_REDIS: bool = False

    # External APIs
    FOOTBALL_DATA_BASE_URL: str = "https://api.football-data.org/v4"
    ODDS_API_BASE_URL: str = "https://api.the-odds-api.com/v4"
    WEATHER_API_BASE_URL: str = "https://api.openweathermap.org/data/2.5"
    SPORTDB_BASE_URL: str = "https://www.thesportsdb.com/api/v1/json/3"
    OPENLIGADB_BASE_URL: str = "https://api.openligadb.de"
    API_SPORTS_BASE_URL: str = "https://api-football-v1.p.rapidapi.com/v3"

    # Adicionado suporte para DATABASE_URL direto
    DATABASE_URL: str = ""

    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        # Use SQLite for development to avoid PostgreSQL dependency issues
        return "sqlite:///./football_analytics_dev.db"

    class Config:
        env_file = ".env"  # Changed to use .env file
        case_sensitive = True

settings = Settings()

def get_settings() -> Settings:
    """Get settings instance"""
    return settings