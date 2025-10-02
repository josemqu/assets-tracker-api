from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List, Union


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_DAYS: int = 7
    
    MONGODB_URI: str
    ALLOWED_ORIGINS: Union[List[str], str] = ["http://localhost:8000"]
    RATE_LIMIT_PER_MINUTE: int = 100
    
    model_config = SettingsConfigDict(env_file=".env")
    
    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


settings = Settings()
