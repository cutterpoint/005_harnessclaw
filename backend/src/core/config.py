"""全局配置模块，基于 pydantic-settings 管理环境变量。"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """应用配置，从 .env 文件和环境变量加载。"""

    # 服务配置
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # JWT 配置
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # 数据库配置
    DATABASE_URL: str = "sqlite:///./data/harnessclaw.db"

    # LLM 配置
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    DEFAULT_MODEL: str = "gpt-4o"

    # 向量库配置
    VECTOR_STORE_PATH: str = "./data/vector_store"
    VECTOR_DB_TYPE: str = "faiss"

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"

    # Agent 配置
    MAX_TOKEN_LIMIT: int = 8192
    MAX_ITERATIONS: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
