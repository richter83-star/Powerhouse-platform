"""
Application settings and configuration.
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings."""

    # =====================================================================================
    # Application
    # =====================================================================================
    app_name: str = "Powerhouse Multi-Agent Platform"
    app_version: str = "1.0.0"
    debug: bool = False

    # =====================================================================================
    # API (internal service)
    # =====================================================================================
    api_v1_prefix: str = "/api/v1"
    api_host: str = "0.0.0.0"
    api_port: int = 8001

    # =====================================================================================
    # Security
    # =====================================================================================
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for JWT encoding"
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # =====================================================================================
    # Database Connection
    # =====================================================================================
    db_host: str = "localhost"
    db_port: int = 5433
    db_user: str = "postgres"
    db_password: str = "postgres"
    db_name: str = "powerhouse"
    database_url: Optional[str] = None  # if provided manually, overrides the above fields

    # =====================================================================================
    # Redis Connection
    # =====================================================================================
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None

    # =====================================================================================
    # CORS
    # =====================================================================================
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:8001"],
        description="Allowed CORS origins"
    )

    # =====================================================================================
    # Agent System
    # =====================================================================================
    max_agents_per_workflow: int = 19
    agent_timeout_seconds: int = 300

    # =====================================================================================
    # Workflow
    # =====================================================================================
    max_retry_attempts: int = 3
    workflow_timeout_seconds: int = 600

    # =====================================================================================
    # Logging
    # =====================================================================================
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    log_format: str = Field(
        default="text",
        description="Log format (text or json)"
    )
    enable_file_logging: bool = Field(
        default=False,
        description="Enable file logging"
    )
    log_file_path: Optional[str] = Field(
        default=None,
        description="Path to log file (default: logs/powerhouse.log)"
    )
    
    # =====================================================================================
    # Monitoring & Error Tracking
    # =====================================================================================
    sentry_dsn: Optional[str] = Field(
        default=None,
        description="Sentry DSN for error tracking"
    )
    sentry_environment: Optional[str] = Field(
        default=None,
        description="Sentry environment (production, staging, development)"
    )

    # =====================================================================================
    # Third-Party / LLM API Keys
    # =====================================================================================
    abacusai_api_key: str = ""
    environment: str = "production"

    # =====================================================================================
    # ENV handling
    # =====================================================================================
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"  # prevents crashes if new variables are added later
    )


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Return global settings instance."""
    return settings
