"""Configuration management for LTMC."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """LTMC configuration settings."""
    
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    FAISS_INDEX_PATH: str = "./data/ltmc.index"
    DATABASE_PATH: str = "./data/ltmc.db"
    SUMMARIZATION_MODEL: str = "gpt-3.5-turbo"

    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields from environment


settings = Settings()
