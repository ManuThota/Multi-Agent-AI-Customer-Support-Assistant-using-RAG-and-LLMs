import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    GEMINI_API_KEY: str = Field(..., alias="GEMINI_API_KEY")
    MONGODB_URL: str = Field("mongodb://localhost:27017", alias="MONGODB_URL")
    MONGODB_DB_NAME: str = Field("customer_support_db", alias="MONGODB_DB_NAME")
    JWT_SECRET: str = Field("supersecretjwtkeythatshouldbechanged123!", alias="JWT_SECRET")
    JWT_ALGORITHM: str = Field("HS256", alias="JWT_ALGORITHM")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(120, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")

    # Path properties to help locate vector databases & models easily
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    VECTORSTORE_DIR: str = os.path.join(BASE_DIR, "vectorstore")
    KNOWLEDGE_BASE_DIR: str = os.path.join(os.path.dirname(BASE_DIR), "knowledge_base")

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()