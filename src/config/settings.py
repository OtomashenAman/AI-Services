# src/config/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Service"
    DEBUG: bool = True
    ENV: str = "development"
    OPENAI_API_KEY: str = ""
    DATABASE_URL: str = ""
    LOG_LEVEL : str = "DEBUG"
    
    class Config:
        env_file = ".env"

settings = Settings()
