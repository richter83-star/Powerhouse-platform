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
    # Email Service
    # =====================================================================================
    email_provider: str = Field(
        default="smtp",
        description="Email provider: sendgrid, aws_ses, or smtp"
    )
    email_from: str = Field(
        default="noreply@powerhouse.ai",
        description="Default sender email address"
    )
    email_from_name: str = Field(
        default="Powerhouse Platform",
        description="Default sender name"
    )
    frontend_url: str = Field(
        default="http://localhost:3000",
        description="Frontend URL for email links"
    )
    
    # SendGrid
    sendgrid_api_key: Optional[str] = Field(
        default=None,
        description="SendGrid API key"
    )
    
    # AWS SES
    aws_ses_region: Optional[str] = Field(
        default=None,
        description="AWS SES region"
    )
    
    # SMTP
    smtp_host: str = Field(
        default="localhost",
        description="SMTP server host"
    )
    smtp_port: int = Field(
        default=587,
        description="SMTP server port"
    )
    smtp_user: Optional[str] = Field(
        default=None,
        description="SMTP username"
    )
    smtp_password: Optional[str] = Field(
        default=None,
        description="SMTP password"
    )
    smtp_use_tls: bool = Field(
        default=True,
        description="Use TLS for SMTP"
    )

    # =====================================================================================
    # Stripe Payment Processing
    # =====================================================================================
    stripe_secret_key: Optional[str] = Field(
        default=None,
        description="Stripe secret API key (sk_test_... or sk_live_...)"
    )
    stripe_publishable_key: Optional[str] = Field(
        default=None,
        description="Stripe publishable API key (pk_test_... or pk_live_...)"
    )
    stripe_webhook_secret: Optional[str] = Field(
        default=None,
        description="Stripe webhook signing secret (whsec_...)"
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
