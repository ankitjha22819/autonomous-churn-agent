"""
Application configuration using pydantic-settings.

Loads from environment variables with .env file support.
All secrets should be in .env (never committed to git).
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, RedisDsn, PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Usage:
        from churn_agent.core.config import get_settings
        settings = get_settings()
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
   
    # Application
   
    app_name: str = "Churn Analysis Agent"
    app_version: str = "0.1.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = Field(default=False, description="Enable debug mode")
    
   
    # API Server
   
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"
    allowed_origins: list[str] = Field(
        default=["*"],
        description="CORS allowed origins"
    )
    
   
    # Database
   
    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/churn_agent",
        description="Async PostgreSQL connection string"
    )
    db_pool_size: int = Field(default=5, ge=1, le=20)
    db_max_overflow: int = Field(default=10, ge=0, le=50)
    
   
    # Redis (for SSE events + Celery broker)
   
    redis_url: RedisDsn = Field(
        default="redis://localhost:6379/0",
        description="Redis connection string"
    )
    redis_sse_channel_prefix: str = "sse:job:"
    
   
    # Celery
   
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    
   
    # AI / LLM Configuration
   
    openai_api_key: SecretStr = Field(
        default=...,
        description="OpenAI API key for LLM calls"
    )
    anthropic_api_key: SecretStr | None = Field(
        default=None,
        description="Optional Anthropic API key"
    )
    default_llm_model: str = "gpt-4o"
    llm_temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    llm_max_tokens: int = Field(default=4096, ge=100, le=128000)
    
   
    # CrewAI Configuration
   
    crew_config_path: str = "config/agents.yaml"
    tasks_config_path: str = "config/tasks.yaml"
    crew_verbose: bool = True
    crew_memory: bool = True
    
   
    # SSE Configuration
   
    sse_heartbeat_interval: int = Field(
        default=15, 
        ge=5, 
        le=60,
        description="Seconds between SSE heartbeat pings"
    )
    sse_retry_timeout: int = Field(
        default=3000,
        description="Client retry timeout in milliseconds"
    )
    
   
    # Logging
   
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_format: Literal["json", "console"] = "console"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings instance.
    
    Returns the same Settings object for the lifetime of the application,
    avoiding repeated .env file reads.
    """
    return Settings()